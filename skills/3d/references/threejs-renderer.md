# three.js Renderer Setup

Purpose: Stand up a vanilla three r186 renderer correctly (backend choice, colour, loop, resize, teardown) and avoid the stale APIs models reach for.

Read when:
- Writing or reviewing vanilla three.js setup, or any code touching `WebGLRenderer` / `WebGPURenderer`.
- Output looks washed, dark, blank, or the canvas leaks across route changes.
- Code uses `Clock`, `PostProcessing`, `RGBELoader`, `uv2`, `three/examples/jsm`.

Skip when:
- React/Next scene → [threejs-r3f-next](threejs-r3f-next.md).
- Lighting, materials, env maps → [threejs-lookdev](threejs-lookdev.md).
- Budgets → [shared-performance](shared-performance.md).

Inputs:
- `package.json` three version, target browsers, whether TSL/compute is needed.

Produces:
- A renderer module with one loop, one resize path, one dispose path.

## Contents

- Backend rule · WebGL setup · WebGPU setup · Colour · Resize and DPR · Lifecycle · Version traps

## Backend rule

1. Default `WebGLRenderer` (GLSL, `onBeforeCompile`, pmndrs postprocessing, drei all work).
2. Use `WebGPURenderer` only when the design needs TSL node materials or compute. It falls back to a WebGL2 backend automatically (`forceWebGL: true` forces it). GLSL `ShaderMaterial` does not run on it.
3. Record the choice in `3D.md`. Never hybridise: no pmndrs composer on WebGPU, no `ShaderMaterial` in a WebGPU scene.

## WebGL setup

```ts
import * as THREE from 'three';
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const timer = new THREE.Timer(); timer.connect(document);
renderer.setAnimationLoop((t) => { timer.update(t); update(timer.getDelta()); renderer.render(scene, camera); });
```

## WebGPU setup

```ts
import * as THREE from 'three/webgpu';
const renderer = new THREE.WebGPURenderer({ canvas, antialias: true });
await renderer.init();               // ALWAYS, before the first render() or compute()
renderer.setAnimationLoop(frame);    // sync render(); renderAsync/computeAsync are deprecated
```

Skipping `init()` gives a blank canvas and no error. Guard against unmount racing the await (set a `disposed` flag, bail after the await).

## Colour

- `renderer.outputColorSpace` defaults `SRGBColorSpace`; `toneMapping` defaults `NoToneMapping`. Pick tone mapping deliberately (`NeutralToneMapping` for brand colour, `AgXToneMapping` for cinematic) — policy lives in [design-lookdev-presets](design-lookdev-presets.md).
- Colour textures (map, emissiveMap) → `texture.colorSpace = THREE.SRGBColorSpace`; data textures (normal, roughness, metalness, AO) stay `NoColorSpace`. GLTFLoader does this itself.
- Tone mapping applies only when drawing to the screen. With `EffectComposer` end the chain in `OutputPass`; never tone-map twice.

## Resize and DPR

1. Clamp DPR to `Math.min(devicePixelRatio, 2)`; lower on mobile per [shared-performance](shared-performance.md).
2. On resize: `camera.aspect = w/h; camera.updateProjectionMatrix(); renderer.setSize(w, h, false)` (CSS owns the size), plus `composer.setSize` if present. Drive it from `ResizeObserver` on the canvas parent, not `window` alone.
3. Re-apply DPR on `devicePixelRatio` change (zoom, monitor move).

## Lifecycle

- One loop, one final-render owner. Stop with `setAnimationLoop(null)`.
- On teardown dispose geometry, materials, every texture slot, render targets, PMREM generator, controls (`controls.dispose()`), then `renderer.dispose()` (async on WebGPU in r186 — await it). Hiding is `visible = false`, never dispose.
- Context loss: listen for `webglcontextlost` (`preventDefault()`) and `webglcontextrestored`; on restore rebuild GPU content from source, not from disposed objects. Test with `renderer.forceContextLoss()`.
- `timer.connect(document)` stops huge deltas after a hidden tab; `timer.dispose()` on teardown.

## Version traps

| Stale (LLM habit) | Current (r186) |
|---|---|
| `new Clock()`, `getDelta()` | `Timer`: `update(t)` once per frame, then `getDelta()` (Clock deprecated r183) |
| `PostProcessing` (WebGPU) | `RenderPipeline` (r183; old name warns) |
| `three/examples/jsm/...` | `three/addons/...` |
| `RGBELoader` (deprecated wrapper, warns) | `HDRLoader` (r180); `UltraHDRLoader` for Ultra HDR JPEG |
| `renderer.outputEncoding`, `sRGBEncoding`, `texture.encoding` | `outputColorSpace`, `colorSpace`, `SRGBColorSpace` |
| `uv2` for AO/light maps | `texture.channel = 1` (reads `uv1`) |
| `envMapIntensity` for `scene.environment` | `scene.environmentIntensity` (r163) |
| `PCFSoftShadowMap` | `PCFShadowMap` or `VSMShadowMap` (soft deprecated r186: WebGL warns and falls back to PCF; removed on WebGPU) |
| `KTX2Loader.detectSupportAsync` | sync `detectSupport(renderer)` after `await renderer.init()` |
| `DRACOLoader.setDecoderConfig` | `setDecoderPath('/draco/')` |
| `renderAsync` / `computeAsync` | `await init()` once, then `render()` / `compute()` |
| `FileLoader.load()` return value | gone (r184): use `loadAsync` or `onLoad` |
| `WebGLMultipleRenderTargets`, `TextGeometry.height`, `CapsuleGeometry.length` | `WebGLRenderTarget` with `count`, `depth`, `height` |
| `useLegacyLights`, `physicallyCorrectLights` | gone; light units are physical |

- Look drift: PBR/PMREM changed in r181, r185 and r186. Never promise the same HDRI looks identical across versions; re-tune env intensity after a bump.
- Pin `three` exactly when using TSL and re-read the migration guide on every bump (TSL has no stability promise).
