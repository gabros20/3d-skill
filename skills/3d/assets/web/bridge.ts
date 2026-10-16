// 3d-preview bridge (mode B). Copy-and-own: drop into the user's app, call installBridge() once the
// renderer, scene and camera exist, behind the `?3d-preview` query and a dev-only guard.
// Owns: the window.__3d contract that `scripts/preview capture` drives (ready, shots, loadShots,
// setShot, frame, capture, info). Must NOT: start/own the render loop, change app state beyond the
// camera/scroll hook you pass in, or ship in production builds. Remove it when the user approves.
//
// R3F: call it from a tiny component, e.g.
//   const { gl, scene, camera } = useThree();
//   // Tunables: const P = readParams({ keyIntensity: 2 }); scene code reads P.keyIntensity;
//   // installBridge({ ..., params: P, onParams: () => applyLook(P) }) lets `preview sweep` and ?p= retune it.
//   useEffect(() => (process.env.NODE_ENV !== 'production' ? installBridge({ gl, scene, camera }) : undefined), [gl, scene, camera]);
// Apps with postprocessing (EffectComposer etc.) pass `render` so captures include the post chain.
import type { Camera, OrthographicCamera, PerspectiveCamera, Scene, Vector3Tuple, WebGLRenderer } from 'three';

/** shots.v1 (references/brief-spec.md): one lens key; metres, Y up; optional end pose `to`. */
export interface BridgePose {
  position?: Vector3Tuple;
  target?: Vector3Tuple;
  focal_mm?: number;
  fov?: number;
  ortho_height?: number;
  roll_deg?: number;
  /** Seconds for time-driven scenes and loops; handed to the app's `setTime` hook. */
  t?: number;
}

export interface BridgeShot extends BridgePose {
  id: string;
  purpose?: string;
  duration_s?: number;
  /** Scroll-driven scenes: normalised progress [start, end] handed to `setProgress` (never pixels). */
  scroll?: [number, number];
  ease?: 'linear' | 'in' | 'out' | 'inOut';
  to?: BridgePose;
  notes?: string;
}

/** Plain JSON object of tunables (the `P` block). */
export type Params = Record<string, unknown>;

export interface BridgeInfo {
  params: Params;
  mode: 'live';
  shot: string | null;
  renderer: string;
  size: [number, number];
  tris: number;
  drawCalls: number;
  textures: number;
  geometries: number;
  visibility: DocumentVisibilityState;
}

export interface Bridge {
  ready: boolean;
  shots(): BridgeShot[];
  loadShots(list: ReadonlyArray<Partial<BridgeShot>>): void;
  /** t in 0..1 moves along the shot's `to` end pose (default 0 = start). */
  setShot(id: string, t?: number): boolean;
  /** Put time-driven state at `t` seconds via the app's setTime hook; false when no hook is registered. */
  setTime(t: number): boolean;
  /** Merge `obj` into the live params (mutating the object you passed as `params`), then call `onParams`. Returns a copy. */
  setParams(obj: Params): Params;
  getParams(): Params;
  frame(n?: number): number;
  capture(): string;
  info(): BridgeInfo;
}

export interface BridgeOptions {
  gl: WebGLRenderer;
  scene: Scene;
  camera: Camera;
  /** OrbitControls-like: only `target` and `update` are used. */
  controls?: { target: { set(x: number, y: number, z: number): unknown }; update(dt?: number): unknown };
  /** Initial shot list (same shape as .3d/shots.json "shots"). `scripts/preview capture` also calls loadShots(). */
  shots?: ReadonlyArray<Partial<BridgeShot>>;
  /** Advance your own time-based animation by a fixed dt (seconds) per frame(n) step. */
  advance?: (dt: number) => void;
  /** Put time-driven state (animation, loop) at `t` seconds; shots with `t` call it. Register like setProgress. */
  setTime?: (t: number) => void;
  /** Move scroll-driven state to normalised progress; shots with `scroll` call it. */
  setProgress?: (progress: number) => void;
  /** Your `P` object (from readParams). setParams() mutates it in place so scene code that reads P sees the change. */
  params?: Params;
  /** Called after every setParams with the merged params: re-apply uniforms, lights, materials here. */
  onParams?: (params: Params) => void;
  /** Draw one frame. Default gl.render(scene, camera); pass your composer's render for postprocessed apps. */
  render?: () => void;
  /** Run `?3d-preview` check yourself; default reads location.search. */
  enabled?: boolean;
}

declare global {
  interface Window {
    __3d?: Bridge;
  }
}

const FIXED_DT = 1 / 60;

const isPlain = (v: unknown): v is Params => typeof v === 'object' && v !== null && !Array.isArray(v);

function merge(base: Params, over: Params): Params {
  for (const [k, v] of Object.entries(over)) base[k] = isPlain(v) && isPlain(base[k]) ? merge(base[k] as Params, v) : v;
  return base;
}

function decodeParam(b64: string): Params | null {
  try {
    const t = b64.replace(/-/g, '+').replace(/_/g, '/');
    const bin = atob(t + '='.repeat((4 - (t.length % 4)) % 4));
    const json = new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
    const v: unknown = JSON.parse(json);
    return isPlain(v) ? v : null;
  } catch {
    return null;
  }
}

/**
 * Tunables in one object: `const P = readParams({ keyIntensity: 2, bloom: { strength: 0.4 } })`.
 * Merges `?p=<base64url JSON>` over the defaults (nested plain objects merge, everything else replaces).
 * SSR-safe: without a window it returns a copy of the defaults. Never throws on a bad `p`.
 */
export function readParams<T extends Params>(defaults: T, search?: string): T {
  const out = merge({}, JSON.parse(JSON.stringify(defaults)) as Params);
  const q = search ?? (typeof window !== 'undefined' ? window.location.search : '');
  const raw = q ? new URLSearchParams(q).get('p') : null;
  const over = raw ? decodeParam(raw) : null;
  if (over) merge(out, over);
  return out as T;
}

const EASE = {
  linear: (t: number) => t,
  in: (t: number) => t * t,
  out: (t: number) => t * (2 - t),
  inOut: (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
};
const mix = (a: number, b: number, k: number): number => a + (b - a) * k;
const mixV = (a: Vector3Tuple, b: Vector3Tuple, k: number): Vector3Tuple => [mix(a[0], b[0], k), mix(a[1], b[1], k), mix(a[2], b[2], k)];
/** focal_mm is full-frame equivalent (36x24): vertical FOV from the 24 mm sensor height. */
const focalToFov = (mm: number): number => (2 * Math.atan(12 / mm) * 180) / Math.PI;

interface Pose {
  position?: Vector3Tuple;
  target?: Vector3Tuple;
  fov?: number;
  ortho?: number;
  roll: number;
  time?: number;
}

function lensOf(o: BridgePose): Pick<Pose, 'fov' | 'ortho'> {
  if (o.ortho_height !== undefined) return { ortho: o.ortho_height };
  if (o.focal_mm !== undefined) return { fov: focalToFov(o.focal_mm) };
  if (o.fov !== undefined) return { fov: o.fov };
  return {};
}

function poseAt(s: BridgeShot, t: number): Pose {
  const a: Pose = { position: s.position, target: s.target, roll: s.roll_deg ?? 0, time: s.t, ...lensOf(s) };
  if (!s.to || !t) return a;
  const k = EASE[s.ease ?? 'inOut'](Math.min(1, Math.max(0, t)));
  const b: Pose = { ...a, ...(s.to.position && { position: s.to.position }), ...(s.to.target && { target: s.to.target }),
    ...(s.to.roll_deg !== undefined && { roll: s.to.roll_deg }), ...(s.to.t !== undefined && { time: s.to.t }), ...lensOf(s.to) };
  const out: Pose = { roll: mix(a.roll, b.roll, k) };
  if (a.time !== undefined) out.time = mix(a.time, b.time ?? a.time, k);
  if (a.position && b.position) out.position = mixV(a.position, b.position, k);
  if (a.target && b.target) out.target = mixV(a.target, b.target, k);
  if (a.ortho !== undefined) out.ortho = mix(a.ortho, b.ortho ?? a.ortho, k);
  else if (a.fov !== undefined) out.fov = mix(a.fov, b.fov ?? a.fov, k);
  return out;
}

function normalise(list: ReadonlyArray<Partial<BridgeShot>>): BridgeShot[] {
  return list.map((s, i) => ({ ...s, id: String(s.id ?? `shot${i + 1}`) }));
}

/** Installs window.__3d and returns an uninstall function. No-op unless `?3d-preview` is present. */
export function installBridge(opts: BridgeOptions): () => void {
  const enabled = opts.enabled ?? new URLSearchParams(window.location.search).has('3d-preview');
  if (!enabled) return () => {};

  const { gl, scene, camera, controls } = opts;
  let shots = normalise(opts.shots ?? []);
  let current: string | null = null;
  const params: Params = opts.params ?? readParams({});

  let rollRad = 0;
  const draw = opts.render ?? ((): void => gl.render(scene, camera));
  // roll_deg is applied around the draw only: OrbitControls re-aims the camera on every update() and would drop it.
  const render = (): void => {
    if (rollRad) {
      camera.rotateZ(rollRad);
      camera.updateMatrixWorld(true);
    }
    draw();
    if (rollRad) {
      camera.rotateZ(-rollRad);
      camera.updateMatrixWorld(true);
    }
  };

  const bridge: Bridge = {
    ready: true,
    shots: () => shots.map((s) => ({ ...s })),
    loadShots(list) {
      shots = normalise(list);
    },
    setShot(id, t = 0) {
      const s = shots.find((x) => x.id === id);
      if (!s) throw new Error(`3d bridge: unknown shot "${id}"`);
      current = id;
      const p = poseAt(s, t);
      if (p.time !== undefined) opts.setTime?.(p.time);
      if (s.scroll) opts.setProgress?.(mix(s.scroll[0], s.scroll[1], t));
      if (p.position) camera.position.set(...p.position);
      if (p.target) {
        controls?.target.set(...p.target);
        camera.lookAt(...p.target);
      }
      const persp = camera as PerspectiveCamera;
      const ortho = camera as OrthographicCamera;
      if (p.fov !== undefined && persp.isPerspectiveCamera) {
        persp.fov = p.fov;
        persp.updateProjectionMatrix();
      } else if (p.ortho !== undefined && ortho.isOrthographicCamera) {
        const half = p.ortho / 2;
        const aspect = (ortho.right - ortho.left) / (ortho.top - ortho.bottom) || 1;
        ortho.top = half;
        ortho.bottom = -half;
        ortho.left = -half * aspect;
        ortho.right = half * aspect;
        ortho.updateProjectionMatrix();
      }
      controls?.update(0);
      rollRad = (p.roll * Math.PI) / 180;
      camera.updateMatrixWorld(true);
      return true;
    },
    setParams(obj) {
      merge(params, obj);
      opts.onParams?.(params);
      return JSON.parse(JSON.stringify(params)) as Params;
    },
    getParams: () => JSON.parse(JSON.stringify(params)) as Params,
    setTime(t) {
      opts.setTime?.(t);
      return opts.setTime !== undefined;
    },
    // Hidden/occluded tabs never fire requestAnimationFrame, so drive frames synchronously.
    frame(n = 1) {
      for (let i = 0; i < n; i++) {
        opts.advance?.(FIXED_DT);
        controls?.update(FIXED_DT);
      }
      render();
      return n;
    },
    // Rendering and reading in the same task keeps the buffer valid even without preserveDrawingBuffer.
    capture() {
      render();
      return gl.domElement.toDataURL('image/png');
    },
    info() {
      const i = gl.info;
      const ctx = gl.getContext();
      const ext = ctx.getExtension('WEBGL_debug_renderer_info');
      const name = ext ? String(ctx.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : 'WebGL';
      return {
        mode: 'live',
        params: JSON.parse(JSON.stringify(params)) as Params,
        shot: current,
        renderer: name,
        size: [gl.domElement.width, gl.domElement.height],
        tris: i.render.triangles,
        drawCalls: i.render.calls,
        textures: i.memory.textures,
        geometries: i.memory.geometries,
        visibility: document.visibilityState,
      };
    },
  };

  window.__3d = bridge;
  return () => {
    if (window.__3d === bridge) delete window.__3d;
  };
}
