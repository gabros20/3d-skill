'use client'
/**
 * r3f/SceneCanvas.tsx: the Canvas wrapper for a hero or scroll scene in the Next App Router.
 *
 * Owns: capability + reduced-motion gate, poster slot (the LCP element when the object is the
 * subject), lazy load of three and R3F (the poster path never downloads them), dpr clamp,
 * colour/tone defaults, frameloop control, off-screen and hidden-tab pause, context-loss fallback,
 * the shader guard, the staged start and `ConductorDriver` (the one tick).
 * Must not: start the scroll authority or pin, publish the page entrance, hold scene content, or
 * decide budgets (those live in the project's 3D.md). Mount it from a Client Component; children
 * must come from a chunk that is itself lazy (or be tiny), or three loads anyway.
 *
 * Stages (`data-scene-stage`, references/threejs-orchestration.md):
 *   prepare: lazy load, `compileAsync`, ONE warm render through every useFrame subscriber (so a
 *            composer's pass programs compile and draw now, not at the reveal), the shader guard,
 *            then a GPU fence. With `startAfter="entrance"` none of it runs while the page entrance
 *            is `running` or `tail`: it runs before the entrance starts or after `settled`.
 *   reveal:  prepared and proven, and the entrance at `tail` (or the timeout): one still frame shows.
 *   run:     the entrance `settled` (or the timeout): the frameloop starts.
 * A failed program never reaches `reveal`: `data-scene-mode="error"`, the poster stays, `onError` fires.
 * Children that must be in the first frame suspend directly under the Canvas (no inner Suspense
 * boundary), so prepare waits for them.
 *
 * Colour: `look="neutral"` (Khronos PBR Neutral, brand-accurate) or `"agx"` (cinematic), with R3F's
 * default ACES switched off through `flat`. Same intent as the Blender view transform.
 */
import {
  lazy,
  Suspense,
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
import type { Conductor } from '../conductor'
import { readEntrance, whenEntrance, type EntranceWait } from '../entrance-gate'
import { guardShaders, type ShaderGuard } from '../shader-guard'

export interface SceneCanvasProps {
  children: ReactNode
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
  /** Failsafe for `startAfter="entrance"`, ms from mount. Default 2500. */
  entranceTimeoutMs?: number
  /** Context MSAA. Default true; false under a composer (put `samples` on its target instead). */
  antialias?: boolean
  /** Transparent canvas. Default true; false when the scene paints its own background (cheaper to composite). */
  alpha?: boolean
  camera?: CanvasProps['camera']
  className?: string
  style?: CSSProperties
  /** Extra warm margin for the off-screen pause, CSS length. Default '200px'. */
  pauseMargin?: string
  onContextLost?: () => void
  /** A shader program failed (at prepare or later) or prepare threw; the poster is showing. */
  onError?: (reason: string) => void
}

type Mode = 'pending' | 'live' | 'poster' | 'error'
type Stage = 'prepare' | 'reveal' | 'run'

const FADE_MS = 400
const noop = (): void => {}

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

interface LiveProps {
  children: ReactNode
  frameloop: 'always' | 'demand' | 'never'
  dpr: [number, number]
  look: 'neutral' | 'agx'
  exposure: number
  antialias: boolean
  alpha: boolean
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
  clear: LiveProps['clear']
  onPrepared: () => void
  onFail: (reason: string) => void
}

// three + R3F load here, once, only after the gate decided the Canvas should exist.
const Live = lazy(async () => {
  const [{ Canvas, useThree }, three] = await Promise.all([import('@react-three/fiber'), import('three')])

  // Mounted beside the children in one Suspense boundary: its effect runs once they have all loaded.
  function Prepare({ stage, guard, clear, onPrepared, onFail }: PrepareProps): null {
    const get = useThree((s) => s.get)
    // One still frame at the current time. R3F's 'never' path writes seconds into clock.oldTime
    // (a millisecond field), so reset it, or the first run frame gets a delta of the page's age.
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
        await gl.compileAsync(scene, camera)
        await clear(life.signal)
        if (life.signal.aborted) return
        still() // the warm render: every program, post passes included, is first used here
        const verdict = guard.current?.check() ?? { ok: true }
        if (!verdict.ok) return onFail(verdict.reason)
        await gpuDone(gl.getContext())
        if (!life.signal.aborted) onPrepared()
      }
      run().catch((error: unknown) => {
        if (!life.signal.aborted) onFail(error instanceof Error ? error.message : String(error))
      })
      return () => life.abort()
    }, [get, still, guard, clear, onPrepared, onFail])

    useEffect(() => {
      if (stage === 'reveal') still() // re-present at the current size before the fade
      if (stage === 'run') get().clock.oldTime = performance.now() // the first run frame continues the still
    }, [stage, still, get])
    return null
  }

  function LiveCanvas(props: LiveProps): ReactNode {
    const guard = useRef<ShaderGuard | null>(null)
    const revealed = props.stage !== 'prepare'
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
          {props.children}
          <Prepare
            stage={props.stage}
            guard={guard}
            clear={props.clear}
            onPrepared={props.onPrepared}
            onFail={props.onFail}
          />
        </Suspense>
      </Canvas>
    )
  }
  return { default: LiveCanvas as ComponentType<LiveProps> }
})

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
    pauseMargin = '200px',
  } = props
  const dprMin = props.dpr?.[0] ?? 1
  const dprMax = props.dpr?.[1] ?? 1.5
  // Stable array: R3F 9.8 re-applies the dpr prop on every Canvas re-render.
  const dpr = useMemo<[number, number]>(() => [dprMin, dprMax], [dprMin, dprMax])

  const root = useRef<HTMLDivElement>(null)
  const [mode, setMode] = useState<Mode>('pending')
  const [mounted, setMounted] = useState(false)
  const [prepared, setPrepared] = useState(false)
  const [stage, setStage] = useState<Stage>('prepare')
  const [inView, setInView] = useState(true)
  const [pageVisible, setPageVisible] = useState(true)
  const [posterGone, setPosterGone] = useState(false)
  const deadline = useRef(0)
  const failed = useRef(false)
  const callbacks = useRef({ onError: props.onError, onContextLost: props.onContextLost })
  useEffect(() => {
    callbacks.current = { onError: props.onError, onContextLost: props.onContextLost }
  })

  // The entrance clock: one failsafe deadline from mount, shared by every wait.
  const wait = useCallback(
    (phase: 'tail' | 'settled', signal: AbortSignal): Promise<EntranceWait> =>
      startAfter === 'entrance'
        ? whenEntrance(phase, { timeoutMs: Math.max(0, deadline.current - performance.now()), signal })
        : Promise.resolve('none'),
    [startAfter],
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
    callbacks.current.onError?.(reason)
  }, [])
  const onPrepared = useCallback((): void => setPrepared(true), [])
  const onLost = useCallback((): void => {
    if (failed.current) return
    setMode('poster')
    callbacks.current.onContextLost?.()
  }, [])

  // Gate once on the client: WebGL present, reduced motion honoured.
  useEffect(() => {
    deadline.current = performance.now() + entranceTimeoutMs
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!webglAvailable() || (reduced && reducedMotion === 'poster')) setMode('poster')
    else setMode('live')
  }, [reducedMotion, entranceTimeoutMs])

  // Mounting starts the three chunk's download and evaluation: main-thread work like the rest of prepare.
  useEffect(() => {
    if (mode !== 'live' || mounted) return
    const life = new AbortController()
    clear(life.signal).then(() => setMounted(true), noop)
    return () => life.abort()
  }, [mode, mounted, clear])

  useEffect(() => {
    if (!prepared || stage !== 'prepare') return
    const life = new AbortController()
    wait('tail', life.signal).then(() => setStage('reveal'), noop)
    return () => life.abort()
  }, [prepared, stage, wait])

  useEffect(() => {
    if (stage !== 'reveal') return
    const life = new AbortController()
    wait('settled', life.signal).then(() => setStage('run'), noop)
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

  const live = mode === 'live'
  const showPoster = !live || stage === 'prepare'
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

  return (
    <div
      ref={root}
      className={props.className}
      style={{ position: 'relative', width: '100%', height: '100%', ...props.style }}
      data-scene-ready={live && stage !== 'prepare' ? 'true' : 'false'}
      data-scene-mode={mode}
      data-scene-stage={live ? stage : undefined}
    >
      {live && mounted && (
        <Suspense fallback={null}>
          <Live
            frameloop={running && stage === 'run' ? frameloop : 'never'}
            dpr={dpr}
            look={look}
            exposure={exposure}
            antialias={antialias}
            alpha={alpha}
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
        </Suspense>
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

/**
 * The one tick. Render it inside <SceneCanvas>. It ticks the conductor from useFrame, calls
 * onFrame with the fresh state, wakes an on-demand loop when input arrives, and keeps frames
 * coming until smooth has settled. Loaded lazily so this file stays free of three at import time.
 */
export const ConductorDriver = lazy(async () => {
  const { useFrame, useThree } = await import('@react-three/fiber')
  function Driver({ conductor, onFrame }: ConductorDriverProps): null {
    const invalidate = useThree((s) => s.invalidate)
    const frameloop = useThree((s) => s.frameloop)

    useEffect(() => conductor.onInput(() => invalidate()), [conductor, invalidate])
    // setFrameloop does not request a frame: wake after resuming from 'never'.
    useEffect(() => {
      if (frameloop !== 'never') invalidate()
    }, [frameloop, invalidate])

    useFrame((_state, delta) => {
      const state = conductor.tick(delta)
      onFrame(state)
      if (!state.settled) invalidate()
    })
    return null
  }
  return { default: Driver as ComponentType<ConductorDriverProps> }
})
