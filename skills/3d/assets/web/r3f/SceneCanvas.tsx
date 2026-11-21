'use client'
/**
 * r3f/SceneCanvas.tsx: the Canvas wrapper for a hero or scroll scene in the Next App Router.
 *
 * Owns: capability + reduced-motion gate, poster slot (the LCP element when the object is the
 * subject), the load of three, R3F and the scene's chunk (the poster path never downloads them),
 * dpr clamp, colour/tone defaults, frameloop control, off-screen and hidden-tab pause, the fallback
 * on context loss or error, the shader guard, the staged start and `ConductorDriver` (the one tick).
 * Must not: start the scroll authority or pin, publish the page entrance, hold scene content, or
 * decide budgets (those live in the project's 3D.md). Mount it from a Client Component and pass the
 * scene as `scene={() => import('./Scene')}`; `children` stay tiny, or three loads with the page.
 *
 * Stages (`data-scene-stage`, references/threejs-orchestration.md):
 *   prepare: the load, `compileAsync`, ONE warm render through every useFrame subscriber (so a
 *            composer's pass programs compile and draw now, not at the reveal), the shader guard,
 *            then a GPU fence. With `startAfter="entrance"` none of it runs while the page entrance
 *            is `running` or `tail`: it runs before the entrance starts or after `settled`.
 *   reveal:  prepared and proven, and the entrance at `tail` (or the timeout): one still frame shows.
 *   run:     the entrance `settled` (or the timeout): the frameloop starts.
 * Timeouts count from navigation start, where the entrance starts, not from this mount (hydration).
 * A failure in prepare never reaches `reveal`; a later one (a shader at first use, a thrown render, a
 * lost context) drops `data-scene-ready` to false and shows the poster again. `data-scene-mode`
 * ("error" or "poster") says which, and `onError` or `onContextLost` fires.
 *
 * No Suspense hold on the reveal: three, R3F and `scene` load as promises and render from state.
 * Once a Suspense fallback has shown, React 19 reveals the boundary no sooner than ~300 ms after it
 * (react-dom 19.3 `FALLBACK_THROTTLE_MS`), however soon the chunk lands, so `React.lazy` or
 * `next/dynamic` here makes every cue late. Children that suspend for assets (useGLTF) stay inside
 * this wrapper's boundary in the Canvas, so prepare waits for them: R3F's own boundary would suspend
 * the whole Canvas in the page instead (its Block fallback). R3F's reconciler throttles that inner
 * reveal the same way, so preload assets the first frame needs (`useGLTF.preload` in the scene chunk).
 *
 * Colour: `look="neutral"` (Khronos PBR Neutral, brand-accurate) or `"agx"` (cinematic), with R3F's
 * default ACES switched off through `flat`. Same intent as the Blender view transform.
 */
import {
  Component,
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ComponentType,
  type MutableRefObject,
  type ReactNode,
} from 'react'
import type { CanvasProps } from '@react-three/fiber'
import type { Camera, Object3D, WebGLRenderer } from 'three'
import type { Conductor } from '../conductor'
import { readEntrance, whenEntrance, type EntranceWait } from '../entrance-gate'
import { guardShaders, type ShaderGuard } from '../shader-guard'

export interface SceneCanvasProps {
  /** Tiny content only (a ConductorDriver, a light): anything heavy goes in `scene`, or three loads with the page. */
  children?: ReactNode
  /**
   * The scene's chunk, as for React.lazy: `() => import('./Scene')`, its default export rendered with no props.
   * Loaded with three and R3F once the gate decides, and rendered from state, never through Suspense.
   */
  scene?: () => Promise<{ default: ComponentType }>
  /** Rendered first and again on failure: the designed still of the scene's hero frame. Unmounted after the fade. */
  poster?: ReactNode
  /**
   * 'demand' renders only on input or while smoothing (pair with ConductorDriver). Default 'demand'.
   * 'never' when an outside tick renders through `advance()`, e.g. inside a `scroll-animation` pin.
   */
  frameloop?: 'always' | 'demand' | 'never'
  /** [min, max] device pixel ratio. Default [1, 1.5]; 2 only for a close-up hero that earns it. */
  dpr?: readonly [number, number]
  look?: 'neutral' | 'agx'
  exposure?: number
  /** 'poster' (default) never mounts the Canvas; 'live' mounts it and relies on the conductor's snap. */
  reducedMotion?: 'poster' | 'live'
  /**
   * 'entrance' keys the stages to the page entrance (`data-entrance` on <html>, published by the
   * entrance's owner). Default 'none': prepare, reveal and run follow each other at once.
   */
  startAfter?: 'none' | 'entrance'
  /** Failsafe for `startAfter="entrance"`, ms from navigation start (not from mount). Default 2500. */
  entranceTimeoutMs?: number
  /** Context MSAA. Default true; false under a composer (put `samples` on its target instead). */
  antialias?: boolean
  /** Transparent canvas. Default true; false when the scene paints its own background (cheaper to composite). */
  alpha?: boolean
  /**
   * The scene draws through a composer (its RenderPass draws into a render target). Default false. Prepare then
   * compiles the program variant a target gets (linear, no tone mapping), or the real programs compile in the
   * warm render, synchronously.
   */
  composer?: boolean
  camera?: CanvasProps['camera']
  className?: string
  style?: CSSProperties
  /** Extra warm margin for the off-screen pause, CSS length. Default '200px'. */
  pauseMargin?: string
  onContextLost?: () => void
  /** The scene failed: a shader program (at prepare or later), a load, prepare or a render threw. The poster shows. */
  onError?: (reason: string) => void
}

type Mode = 'pending' | 'live' | 'poster' | 'error'
type Stage = 'prepare' | 'reveal' | 'run'
type Fiber = typeof import('@react-three/fiber')
type Three = typeof import('three')

const FADE_MS = 400

const reasonOf = (error: unknown): string => (error instanceof Error ? error.message : String(error))

function webglAvailable(): boolean {
  try {
    const probe = document.createElement('canvas')
    const gl = (probe.getContext('webgl2') ?? probe.getContext('webgl')) as WebGLRenderingContext | null
    if (!gl) return false
    gl.getExtension('WEBGL_lose_context')?.loseContext()
    return true
  } catch {
    return false
  }
}

/** Resolves once the GPU has finished the commands issued so far (WebGL2 fence, polled), capped. */
function gpuDone(gl: WebGLRenderingContext | WebGL2RenderingContext, capMs = 1000): Promise<void> {
  if (!('fenceSync' in gl)) return new Promise((resolve) => requestAnimationFrame(() => resolve()))
  const sync = gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0)
  if (!sync) return Promise.resolve()
  gl.flush()
  const start = performance.now()
  return new Promise((resolve) => {
    const poll = (): void => {
      if (gl.clientWaitSync(sync, 0, 0) === gl.TIMEOUT_EXPIRED && performance.now() - start < capMs) {
        setTimeout(poll, 4)
        return
      }
      gl.deleteSync(sync)
      resolve()
    }
    setTimeout(poll, 0)
  })
}

/**
 * `compileAsync` for the program variant the scene will draw with. three r186 picks it by the bound render target:
 * the canvas gets `outputColorSpace` and the renderer's tone mapping, any other target linear and none. A composer's
 * RenderPass draws into a target, so compile with one bound; compileAsync reads it synchronously, at the call.
 */
function compileFor(three: Three, gl: WebGLRenderer, scene: Object3D, camera: Camera, composer: boolean): Promise<unknown> {
  if (!composer) return gl.compileAsync(scene, camera)
  const previous = gl.getRenderTarget()
  const target = new three.WebGLRenderTarget(1, 1)
  let compiling: Promise<unknown>
  try {
    gl.setRenderTarget(target)
    compiling = gl.compileAsync(scene, camera)
  } catch (error) {
    target.dispose()
    throw error
  } finally {
    gl.setRenderTarget(previous)
  }
  return compiling.finally(() => target.dispose())
}

interface LiveProps {
  children?: ReactNode
  scene: ComponentType | null
  frameloop: 'always' | 'demand' | 'never'
  dpr: [number, number]
  look: 'neutral' | 'agx'
  exposure: number
  antialias: boolean
  alpha: boolean
  composer: boolean
  camera?: CanvasProps['camera'] | undefined
  stage: Stage
  /** No poster: the canvas fades in itself (build-up reveal). With a poster it sits at full opacity under it. */
  fadeIn: boolean
  /** Resolves when main-thread work is allowed (not mid-entrance). */
  clear: (signal: AbortSignal) => Promise<unknown>
  onPrepared: () => void
  onFail: (reason: string) => void
  onLost: () => void
}

interface PrepareProps {
  stage: Stage
  guard: MutableRefObject<ShaderGuard | null>
  composer: boolean
  clear: LiveProps['clear']
  onPrepared: () => void
  onFail: (reason: string) => void
}

/** R3F once loaded: ConductorDriver reads its hooks from here. */
let fiber: Fiber | null = null
let live: Promise<ComponentType<LiveProps>> | null = null

/** three + R3F, once per page, only after the gate decided the Canvas should exist. A failed load is retried. */
function loadLive(): Promise<ComponentType<LiveProps>> {
  live ??= Promise.all([import('@react-three/fiber'), import('three')]).then(
    ([r3f, three]) => {
      fiber = r3f
      return createLive(r3f, three)
    },
    (error: unknown) => {
      live = null
      throw error
    },
  )
  return live
}

function createLive(r3f: Fiber, three: Three): ComponentType<LiveProps> {
  const { Canvas, useThree } = r3f

  // Mounted beside the scene in one Suspense boundary: its effect runs once everything in it has loaded.
  function Prepare({ stage, guard, composer, clear, onPrepared, onFail }: PrepareProps): null {
    const get = useThree((s) => s.get)
    // One still frame at the current time. R3F's 'never' path writes seconds into clock.oldTime, a millisecond
    // field. Leaving 'never', setFrameloop restarts the clock, so the run's first delta is fine without this reset:
    // it is a belt for an author who keeps frameloop="never" and later advances without a timestamp.
    const still = useCallback((): void => {
      const { clock, advance } = get()
      advance(clock.elapsedTime, true)
      clock.oldTime = performance.now()
    }, [get])

    useEffect(() => {
      const life = new AbortController()
      const run = async (): Promise<void> => {
        await clear(life.signal)
        if (life.signal.aborted) return
        const { gl, scene, camera } = get()
        await compileFor(three, gl, scene, camera, composer)
        await clear(life.signal)
        if (life.signal.aborted) return
        still() // the warm render: every program, post passes included, is first used here
        const verdict = guard.current?.check() ?? { ok: true }
        if (!verdict.ok) return onFail(verdict.reason)
        await gpuDone(gl.getContext())
        if (!life.signal.aborted) onPrepared()
      }
      run().catch((error: unknown) => {
        if (!life.signal.aborted) onFail(reasonOf(error))
      })
      return () => life.abort()
    }, [get, still, guard, composer, clear, onPrepared, onFail])

    useEffect(() => {
      if (stage === 'reveal') still() // re-present at the current size before the fade
      if (stage === 'run') get().clock.oldTime = performance.now() // the belt again: see still()
    }, [stage, still, get])
    return null
  }

  function LiveCanvas(props: LiveProps): ReactNode {
    const guard = useRef<ShaderGuard | null>(null)
    const revealed = props.stage !== 'prepare'
    const Scene = props.scene
    return (
      <Canvas
        flat
        frameloop={props.frameloop}
        dpr={props.dpr}
        {...(props.camera ? { camera: props.camera } : {})}
        style={{
          position: 'absolute',
          inset: 0,
          opacity: revealed || !props.fadeIn ? 1 : 0,
          ...(props.fadeIn ? { transition: `opacity ${FADE_MS}ms ease-out` } : {}),
        }}
        gl={{ antialias: props.antialias, alpha: props.alpha, powerPreference: 'high-performance' }}
        onCreated={({ gl }) => {
          // After R3F's own setup, so nothing overwrites it; before the first render, so the guard sees it.
          gl.outputColorSpace = three.SRGBColorSpace
          gl.toneMapping = props.look === 'agx' ? three.AgXToneMapping : three.NeutralToneMapping
          gl.toneMappingExposure = props.exposure
          guard.current = guardShaders(gl, props.onFail)
          gl.domElement.addEventListener('webglcontextlost', (event) => {
            event.preventDefault()
            props.onLost()
          })
        }}
      >
        <Suspense fallback={null}>
          {Scene ? <Scene /> : null}
          {props.children}
          <Prepare
            stage={props.stage}
            guard={guard}
            composer={props.composer}
            clear={props.clear}
            onPrepared={props.onPrepared}
            onFail={props.onFail}
          />
        </Suspense>
      </Canvas>
    )
  }
  return LiveCanvas
}

/** A scene that throws (an asset that failed to load, a render error, a context R3F can't create) shows the poster. */
class SceneBoundary extends Component<{ onError: (reason: string) => void; children?: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError(): { failed: boolean } {
    return { failed: true }
  }
  componentDidCatch(error: unknown): void {
    this.props.onError(reasonOf(error))
  }
  render(): ReactNode {
    return this.state.failed ? null : this.props.children
  }
}

interface Loaded {
  Live: ComponentType<LiveProps>
  Scene: ComponentType | null
}

export function SceneCanvas(props: SceneCanvasProps): ReactNode {
  const {
    children,
    poster,
    frameloop = 'demand',
    look = 'neutral',
    exposure = 1,
    reducedMotion = 'poster',
    startAfter = 'none',
    entranceTimeoutMs = 2500,
    antialias = true,
    alpha = true,
    composer = false,
    pauseMargin = '200px',
  } = props
  const dprMin = props.dpr?.[0] ?? 1
  const dprMax = props.dpr?.[1] ?? 1.5
  // Stable array: R3F 9.8 re-applies the dpr prop on every Canvas re-render.
  const dpr = useMemo<[number, number]>(() => [dprMin, dprMax], [dprMin, dprMax])

  const root = useRef<HTMLDivElement>(null)
  const [mode, setMode] = useState<Mode>('pending')
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [prepared, setPrepared] = useState(false)
  const [stage, setStage] = useState<Stage>('prepare')
  const [inView, setInView] = useState(true)
  const [pageVisible, setPageVisible] = useState(true)
  const [posterGone, setPosterGone] = useState(false)
  const failed = useRef(false)
  // Read when needed, never effect dependencies: an inline `scene={() => import(…)}` is a new function each render.
  const latest = useRef({ onError: props.onError, onContextLost: props.onContextLost, scene: props.scene })
  useEffect(() => {
    latest.current = { onError: props.onError, onContextLost: props.onContextLost, scene: props.scene }
  })

  // The entrance's clock: whenEntrance counts the failsafe from navigation start, where the entrance starts.
  const wait = useCallback(
    (phase: 'tail' | 'settled', signal: AbortSignal): Promise<EntranceWait> =>
      startAfter === 'entrance' ? whenEntrance(phase, { timeoutMs: entranceTimeoutMs, signal }) : Promise.resolve('none'),
    [startAfter, entranceTimeoutMs],
  )
  // Main-thread prepare work runs before the entrance starts or after it settles, never mid-entrance.
  const clear = useCallback(
    (signal: AbortSignal): Promise<unknown> => {
      const phase = startAfter === 'entrance' ? readEntrance() : null
      return phase === 'running' || phase === 'tail' ? wait('settled', signal) : Promise.resolve()
    },
    [startAfter, wait],
  )
  const fail = useCallback((reason: string): void => {
    if (failed.current) return
    failed.current = true
    setMode('error')
    latest.current.onError?.(reason)
  }, [])
  const onPrepared = useCallback((): void => setPrepared(true), [])
  const onLost = useCallback((): void => {
    if (failed.current) return
    setMode('poster')
    latest.current.onContextLost?.()
  }, [])

  // Gate once on the client: WebGL present, reduced motion honoured.
  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!webglAvailable() || (reduced && reducedMotion === 'poster')) setMode('poster')
    else setMode('live')
  }, [reducedMotion])

  // The load of three, R3F and the scene's chunk is main-thread work like the rest of prepare. The modules go into
  // state and render directly: no React.lazy, so no Suspense fallback whose reveal React would hold.
  useEffect(() => {
    if (mode !== 'live' || loaded) return
    const life = new AbortController()
    clear(life.signal)
      .then(() => Promise.all([loadLive(), latest.current.scene?.()]))
      .then(([Live, scene]) => {
        if (life.signal.aborted) return
        if (scene && typeof scene.default !== 'function') throw new Error('scene: the chunk has no default export')
        setLoaded({ Live, Scene: scene?.default ?? null })
      })
      .catch((error: unknown) => {
        if (!life.signal.aborted) fail(reasonOf(error))
      })
    return () => life.abort()
  }, [mode, loaded, clear, fail])

  useEffect(() => {
    if (!prepared || stage !== 'prepare') return
    const life = new AbortController()
    wait('tail', life.signal).then(
      () => setStage('reveal'),
      () => {},
    )
    return () => life.abort()
  }, [prepared, stage, wait])

  useEffect(() => {
    if (stage !== 'reveal') return
    const life = new AbortController()
    wait('settled', life.signal).then(
      () => setStage('run'),
      () => {},
    )
    return () => life.abort()
  }, [stage, wait])

  // Pause the render loop off-screen and in a hidden tab (rAF stops there anyway; this also stops demand).
  useEffect(() => {
    const el = root.current
    if (!el) return
    const observer = new IntersectionObserver((entries) => setInView(entries.some((entry) => entry.isIntersecting)), {
      rootMargin: `${pauseMargin} 0px`,
    })
    observer.observe(el)
    const onVisibility = (): void => setPageVisible(!document.hidden)
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      observer.disconnect()
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [pauseMargin])

  const isLive = mode === 'live'
  const showPoster = !isLive || stage === 'prepare'
  // A poster kept at opacity 0 still holds its decoded image and a layer: unmount it after the fade.
  useEffect(() => {
    if (showPoster) {
      setPosterGone(false)
      return
    }
    const timer = setTimeout(() => setPosterGone(true), FADE_MS + 50)
    return () => clearTimeout(timer)
  }, [showPoster])

  const running = inView && pageVisible
  const Live = loaded?.Live

  return (
    <div
      ref={root}
      className={props.className}
      style={{ position: 'relative', width: '100%', height: '100%', ...props.style }}
      data-scene-ready={isLive && stage !== 'prepare' ? 'true' : 'false'}
      data-scene-mode={mode}
      data-scene-stage={isLive ? stage : undefined}
    >
      {isLive && Live && (
        <SceneBoundary onError={fail}>
          <Live
            scene={loaded.Scene}
            frameloop={running && stage === 'run' ? frameloop : 'never'}
            dpr={dpr}
            look={look}
            exposure={exposure}
            antialias={antialias}
            alpha={alpha}
            composer={composer}
            camera={props.camera}
            stage={stage}
            fadeIn={poster == null}
            clear={clear}
            onPrepared={onPrepared}
            onFail={fail}
            onLost={onLost}
          >
            {children}
          </Live>
        </SceneBoundary>
      )}
      {poster != null && (showPoster || !posterGone) && (
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            opacity: showPoster ? 1 : 0,
            transition: `opacity ${FADE_MS}ms ease-out`,
          }}
        >
          {poster}
        </div>
      )}
    </div>
  )
}

export interface ConductorDriverProps {
  conductor: Conductor
  /** Runs inside the R3F frame, right after the tick: write camera, world state, uniforms here. */
  onFrame: (state: Readonly<Conductor['state']>) => void
}

function Driver({ conductor, onFrame }: ConductorDriverProps): null {
  const r3f = fiber as Fiber // set before any Driver renders: by loadLive, or by LazyDriver's load
  const invalidate = r3f.useThree((s) => s.invalidate)
  const frameloop = r3f.useThree((s) => s.frameloop)

  useEffect(() => conductor.onInput(() => invalidate()), [conductor, invalidate])
  // setFrameloop does not request a frame: wake after resuming from 'never'.
  useEffect(() => {
    if (frameloop !== 'never') invalidate()
  }, [frameloop, invalidate])

  r3f.useFrame((_state, delta) => {
    const state = conductor.tick(delta)
    onFrame(state)
    if (!state.settled) invalidate()
  })
  return null
}

// Outside a SceneCanvas (a hand-made <Canvas>), R3F may not be loaded yet: wait for it the lazy way.
const LazyDriver = lazy(async () => {
  fiber ??= await import('@react-three/fiber')
  return { default: Driver }
})

/**
 * The one tick. Render it inside <SceneCanvas>. It ticks the conductor from useFrame, calls onFrame with the
 * fresh state, wakes an on-demand loop when input arrives, and keeps frames coming until smooth has settled.
 * This file stays free of three at import time: inside SceneCanvas, R3F is loaded before it renders, so it
 * renders at once with no Suspense hold on the prepare; elsewhere it loads R3F lazily first.
 */
export function ConductorDriver(props: ConductorDriverProps): ReactNode {
  const [direct] = useState(() => fiber !== null) // decided once: switching would remount the driver
  return direct ? <Driver {...props} /> : <LazyDriver {...props} />
}
