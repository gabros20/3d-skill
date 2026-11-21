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

## After loading a Blender glTF

- Shadows are not in glTF: `traverse` and set `castShadow` / `receiveShadow`, then pick a shadow technique ([threejs-lookdev](threejs-lookdev.md)).
- Lightmaps from a second UV are assigned in code (`texture.channel = 1`, `material.lightMap`); the exporter carries only AO.
- Materials often arrive `doubleSided` (Blender default): set `side = FrontSide` where the mesh is closed.
- `KHR_materials_variants` needs a third-party plugin, stale since 2022: test before relying on it.

## Hide compile and upload behind the preloader

1. Mount the scene while the preloader is up (paused CSS animation, un-paused on the ready signal). Behind a page-load entrance, prepare runs before it starts or after it settles: [threejs-orchestration](threejs-orchestration.md).
2. `await renderer.compileAsync(scene, camera)`. It walks the scene only: composer pass materials (bloom's blur chain, a merged final pass) are not in it. It also compiles for the bound target: three (r186) gives the canvas sRGB output and tone mapping, any render target linear and none, and a composer's RenderPass draws into a target. Under a composer, `renderer.setRenderTarget(composer.readBuffer)` (pmndrs: `inputBuffer`) before the call and `setRenderTarget(null)` after, or the real programs compile in the warm render, synchronously (`SceneCanvas`: `composer`). Layer-masked cameras and each state that switches materials are separate programs: compile each. On Safari await the second compile before reveal. On WebGPU `compileAsync` is also on the renderer.
3. Warm render the full chain: `composer.render()` (R3F: one `advance()`, which runs the composer's `useFrame`) at final size, so every pass program compiles and draws now, not on the reveal frame. A linked program is not a warm one: Metal and D3D back ends build pipeline state at the first draw. Set `frustumCulled = false` for the warm pass so off-screen meshes compile, restore after. The draw also uploads textures (or `renderer.initTexture(tex)`, after `init()` on WebGPU).
4. Prove it: the shader guard (`<skill>/assets/web/shader-guard.ts`, [threejs-renderer](threejs-renderer.md) "Shader errors") after the warm render, then a WebGL2 fence: `gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0)`, `gl.flush()`, poll `clientWaitSync(sync, 0, 0)` from a timer until it stops returning `TIMEOUT_EXPIRED`. `SceneCanvas` does all three.
5. Gate the reveal on proven frames, not asset progress or timers: two timer-based gates failed in production. A loop already running can count frames in `useFrame(..., -999)` and fire at about frame 8, then wait two `requestAnimationFrame`s.
6. Firefox has no `KHR_parallel_shader_compile`: `compileAsync` resolves after about 10 ms without waiting, and the warm render blocks while it compiles. Schedule it where a block is harmless (under a veil, before the entrance, after `settled`).
7. Chunk one-shot procedural work (noise textures, buffers) across frames and start at creation, not first use.

## Texture residency

- `loading="lazy"` does nothing for WebGL textures: schedule loads by chapter or camera distance ([scroll-conductor](scroll-conductor.md) rule 11).
- Cache variants by full identity plus sampling and colour settings, never a filename suffix; a placeholder → hero upgrade keeps UV scale and material identity.
- GPU memory is per context: the same texture in two canvases allocates twice. `visible = false` frees nothing: reference-count shared textures and materials and dispose at world teardown, never from one mesh; revoke object URLs once the loader has consumed them.

## Validation

- Throttled network + cold cache: no decoder 404, no frame over ~100 ms after reveal.
- DevTools Network lists `.wasm`/transcoder files from your paths, not a CDN you did not choose.
- `renderer.info.programs.length` stops growing after reveal; a new program after it means the warm render missed a pass or a state.

## Traps

- Missing `Content-Type: application/wasm` or wrong base path gives a silent hang.
- `renderer.initTexture(tex)` works on both renderers; on WebGPU call it only after `await renderer.init()` (it throws before).
