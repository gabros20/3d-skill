# three.js Runtime Loading

Purpose: Load glTF assets at runtime with the right decoders and hide shader compile and texture upload behind a preloader so the first reveal does not jank.

Read when:
- Wiring GLTFLoader/useGLTF with meshopt, Draco or KTX2, or decoders 404 in production.
- The page freezes right after the loader disappears, or first scroll hitches.

Skip when:
- Producing/compressing the GLB (CLI flags, KTX2 encode) → [asset-pipeline](asset-pipeline.md).
- Steady-state frame cost → [shared-performance](shared-performance.md).

Inputs:
- GLB compression used (meshopt / Draco / KTX2), renderer instance, list of materials/states the scene will show.

Produces:
- One loader module with identical config for preload and load, plus a gated reveal.

## Decoder wiring (vanilla)

```ts
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
const loader = new GLTFLoader()
  .setMeshoptDecoder(MeshoptDecoder)
  .setKTX2Loader(new KTX2Loader().setTranscoderPath('/basis/').detectSupport(renderer));
// only if a file uses Draco:
loader.setDRACOLoader(new DRACOLoader().setDecoderPath('/draco/'));
```

1. Copy `three/examples/jsm/libs/basis/` and `.../libs/draco/` into `public/`; paths are served URLs, not imports.
2. `detectSupport(renderer)` is sync; on WebGPU call it after `await renderer.init()`. Without it KTX2 throws "Missing initialization".
3. One KTX2Loader and one decoder pool, owned by one module; `setWorkerLimit(n)` to cap. Never create loaders per component.
4. Meshopt is the default compression; Draco only per [asset-pipeline](asset-pipeline.md). A file is one or the other, never both.
5. `setDecoderConfig` is deprecated; use `setDecoderPath`.

## R3F

- `useGLTF(url, useDraco = true, useMeshopt = true, extendLoader?)` handles Suspense and cache. Draco defaults ON and fetches its decoder from the gstatic CDN: pass `false` for meshopt-only files, or self-host with a path string (`useGLTF(url, '/draco/')`) or `useGLTF.setDecoderPath('/draco/')`. Call `useGLTF.preload(url, ...)` at module scope for assets needed soon, not the catalogue, with the same arguments as the load.
- KTX2 under R3F: build one `KTX2Loader`, pass it through `extendLoader`: `useGLTF(url, false, true, (l) => l.setKTX2Loader(shared))`. Do not switch to `useLoader(GLTFLoader)`: drei uses three-stdlib's loader and wires meshopt itself.
- Conditional asset = conditionally mount a child, never a null URL.
- Suspense groups assets that reveal together. Suspense does not catch rejections: add an error boundary with retry. Inside the Canvas use a three-side fallback; drei `Loader` lives outside. `useProgress` is not byte-accurate.

## Hide compile and upload behind the preloader

1. Mount the scene while the preloader is up (paused CSS animation, un-paused on the ready signal).
2. `await renderer.compileAsync(scene, camera)`. Layer-masked cameras and each state that switches materials are separate programs: compile each. On Safari await the second compile before reveal. On WebGPU `compileAsync` is also on the renderer.
3. Warm render: a few real frames through the full post chain; set `frustumCulled = false` on meshes for the warm pass so off-screen meshes compile, restore after. Force texture upload with an actual render (or `renderer.initTexture(tex)`, after `init()` on WebGPU) so GPU upload happens now, not on first scroll.
4. Gate the reveal on rendered frames, not asset progress or timers: count frames in `useFrame(..., -999)` and fire at about frame 8. Then wait two `requestAnimationFrame`s before fading. Two timer-based gates failed in production.
5. Chunk one-shot procedural work (noise textures, buffers) across frames and start at creation, not first use.

## Validation

- Throttled network + cold cache: no decoder 404, no frame over ~100 ms after reveal.
- DevTools Network lists `.wasm`/transcoder files from your paths, not a CDN you did not choose.
- `renderer.info.programs.length` stops growing after reveal.

## Traps

- Missing `Content-Type: application/wasm` or wrong base path gives a silent hang.
- `renderer.initTexture(tex)` works on both renderers; on WebGPU call it only after `await renderer.init()` (it throws before).
