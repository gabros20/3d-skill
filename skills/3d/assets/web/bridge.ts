// 3d-preview bridge (mode B). Copy-and-own: drop into the user's app, call installBridge() once the
// renderer, scene and camera exist, behind the `?3d-preview` query and a dev-only guard.
// Owns: the window.__3d contract that `scripts/preview capture` drives (ready, shots, loadShots,
// setShot, frame, capture, info). Must NOT: start/own the render loop, change app state beyond the
// camera/scroll hook you pass in, or ship in production builds. Remove it when the user approves.
//
// R3F: call it from a tiny component, e.g.
//   const { gl, scene, camera } = useThree();
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

export interface BridgeInfo {
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
