# Ground truth: web 3D (researched 2026-10-16)

Grades: [V] official source · [B] measured by me (npm registry / gh api / fetched bytes) · [P] practitioner/secondary · [U] unverified.
WebFetch pages were summarised by a small model; load-bearing claims were cross-checked against registry or repo data where possible.

## 1. Version table

| Package | Version | Date | Source |
|---|---|---|---|
| three | 0.186.1 (r186 = 2026-09-24; patch 09-24) | 2026-09-24 | npm `time`, gh releases [B] |
| three history | r180 2025-09-03 · r181 2025-11-19 · r182 2025-12-10 · r183 2026-02-20 · r184 2026-04-16 · r185 2026-07-01 · r186 2026-09-24 | | gh api releases [B] |
| @types/three | 0.186.0 | 2026-10-04 | npm [B] |
| @react-three/fiber | **9.8.2 = `latest`** (2026-10-15); **10.0.0-alpha.5** (2026-09-08, `alpha`); 10.0.0-canary.* daily (`canary`) | | npm dist-tags, gh [B] |
| R3F 9.8.2 peers | react/react-dom `>=19 <19.4`, three `>=0.156` | | npm [B] |
| R3F 10 alpha peers | three `>=0.185.0`, react `>=19.0 <19.4` | | v10 migration doc [V] |
| @react-three/drei | **10.7.9 = `latest`** (2026-09-25); 11.0.0-alpha.7 (2026-09-05, `alpha`, needs R3F 10 alpha, react `<19.3`, three `>=0.185`) | | npm [B] |
| drei 10.7.9 peers | react ^19, three >=0.159, fiber ^9.0.0 | | npm [B] |
| @react-three/postprocessing | 3.2.0 (peers fiber >=9.7, postprocessing ^6.36, react ^19, three >=0.156) | 2026-10-10 | npm [B] |
| postprocessing (pmndrs) | 6.39.5 | 2026-09-09 | npm [B] |
| @react-three/rapier | 2.2.0 (peers fiber ^9.0.4, react ^19) | 2025-11-03 | npm [B] |
| @react-three/xr | 6.6.32 (peers react >=18, fiber >=8, three *) | 2026-10-13 | npm [B] |
| @react-three/uikit | 1.0.77 | 2026-10-13 | npm [B] |
| @react-three/tsl | only `10.0.0-canary.*` (R3F 10 TSL hooks) | | npm [B] |
| @splinetool/runtime | 2.0.89 (releases near-daily) | 2026-10-16 | npm [B] |
| @splinetool/react-spline | 4.1.0 (no release since 2025-07-15) | 2025-07-15 | npm [B] |
| @sparkjsdev/spark | 2.3.1 (2.0.0 2026-04-14 · 2.1 05-18 · 2.2 09-11 · 2.3.0 09-29/30) MIT, World Labs | 2026-10-01 | npm, CHANGELOG [B] |
| @mkkellogg/gaussian-splats-3d | 0.4.7 (2025-01-25); README: "no longer in active development", recommends Spark | | npm, README [B] |
| gsplat (huggingface/gsplat.js) | 1.2.9 (2025-07), repo pushed 2026-09 | | npm/gh [B] |
| @theatre/core · @theatre/r3f | 0.7.2 (2024-05-19); repo last push 2024-08-14 | | npm/gh [B] |
| @google/model-viewer | 4.4.0 | 2026-10-09 | npm [B] |
| r3f-perf | 7.2.3 (2024-11); repo pushed 2024-12 | | npm/gh [B] |
| stats-gl | 4.2.3 | 2026-07-10 | npm [B] |
| spectorjs | 0.9.33 (repo pushed 2026-10-12; includes an MCP server) | 2026-09-14 | npm, README [B] |
| three-mesh-bvh | 0.9.16 | 2026-10-08 | npm [B] |
| @gltf-transform/cli | 4.5.1 | 2026-09-28 | npm [B] |
| gltfpack / meshoptimizer | 1.3.0 | 2026-09-25 | npm [B] |
| motion | 14.3.0 (2026-10-15) · gsap 3.15.0 (2026-04-13) · lenis 1.3.27 | | npm [B] |
| leva 0.10.1 · lil-gui 0.21.0 · zustand 5.0.15 | | | npm [B] |

Licences: three MIT; R3F MIT; drei MIT; postprocessing **Zlib**; Spark MIT; model-viewer Apache-2.0; Theatre Apache-2.0; Spector MIT; r3f-perf MIT; @react-three/xr repo licence NOASSERTION; stats-gl no licence field detected.

## 2. Topic facts

### 2.1 three.js core
- Release cadence ~every 2-3 months (r183 → r186 in 7 months). [B]
- **Package exports** (`three@0.186.0` package.json): `.` (build/three.module.js + three.cjs), `./addons` → `examples/jsm/Addons.js`, `./addons/*` → `examples/jsm/*`, `./webgpu` → `build/three.webgpu.js`, `./tsl` → `build/three.tsl.js`, `./examples/jsm/*` still exported, `./src/*`. [B]  So `import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'` is canonical; `three/examples/jsm/...` still works.
- `three/webgpu` + `three/tsl` entrypoints introduced r171 (migration "170→171: use `three/webgpu` and `three/tsl`"). [V]
- Gzipped entry-chunk sizes at 0.186.1 (jsdelivr min files, gzip -9; no tree-shaking; `three.module` imports a separate `three.core` chunk, so WebGL total ≈ 90 + 104 KB): three.module.min 90 KB, three.core.min 104 KB, three.webgpu.min 205 KB. [B] Treat as upper bound; bundlers tree-shake.
- **WebGPURenderer**: constructor options `antialias` (false), `samples`, `alpha` (true), `depth`, `stencil` (false), `logarithmicDepthBuffer`, `reversedDepthBuffer`, `outputType`, `outputBufferType` (HalfFloat default), `multiview`, **`forceWebGL`**. Uses WebGPU when available, **falls back to WebGL2 backend automatically**; `forceWebGL: true` forces fallback. [V docs/pages/WebGPURenderer.html]
- `init()` is async and must be awaited before first `render()` (R3F v9 docs state the "render() before backend initialized" failure). `renderAsync/computeAsync/clearAsync/initTextureAsync/hasFeatureAsync` deprecated r181; after `await renderer.init()` use sync `render()`/`compute()`. `setAnimationLoop` is the supported loop (docs: prefer over manual rAF). [V migration + docs]
- r186: `renderer.dispose()` introduced as async on the node Renderer ("Introduce dispose() async", #34364) [V release notes]; `Object3D.dispose()` added (custom overrides must call `super.dispose()`).
- **Colour**: `ColorManagement.enabled = true` default since r152; `outputEncoding→outputColorSpace`, `texture.encoding→colorSpace` (r152). `WebGLRenderer.outputColorSpace` default `SRGBColorSpace`; `toneMapping` default `NoToneMapping`; options No/Linear/Reinhard/Cineon/ACESFilmic/Custom/**AgX/Neutral**; `toneMappingExposure` 1. [V docs/pages/WebGLRenderer.html] Colour textures (map, emissiveMap, ...) need `texture.colorSpace = SRGBColorSpace`; data textures (normal/roughness/AO/metalness) stay `NoColorSpace`. GLTFLoader sets this itself. [P - well-known; r152 migration confirms rename]
- r163: `envMapIntensity` only affects material `envMap`; use `scene.environmentIntensity` for `scene.environment`. r155: `useLegacyLights` deprecated, default false (physical light units: intensities for Point/Spot are candela, ~PI x older values). [V migration]
- r184: background/environment rotation aligned with object rotation semantics. r181: PMREM/PBR indirect specular changed (look shifts vs old versions; re-tune env intensity). r186: PMREM uses spiral blur; multiscatter/energy conservation changes (look changes slightly). [V]
- Shadows: `PCFSoftShadowMap` deprecated for WebGLRenderer r182, **removed from WebGPURenderer r186**; default type is `PCFShadowMap`. Use `PCFShadowMap`/`VSMShadowMap`. [V]
- **Timer replaces Clock**: `Clock` deprecated r183 → `Timer` (in core `THREE.Timer` since r179). API: `timer.update(timestamp)` once per frame, then `getDelta()`/`getElapsed()` (idempotent), `connect(document)` to avoid huge deltas after tab hidden (r174: no longer automatic), `setTimescale`, `dispose()`. [V docs + migration]
- **Post-processing rename**: `PostProcessing` → `RenderPipeline` (r183), `PostProcessingUtils` → `RendererUtils` (r172). WebGLRenderer path still uses `EffectComposer` + `OutputPass` (inline tone mapping applies only when drawing to screen; r155). [V]
- Loaders: `RGBELoader → HDRLoader` (r180), `RGBMLoader` removed; `KTX2Loader.detectSupport(renderer)` is now **sync** and accepts WebGL or WebGPU renderer (`detectSupportAsync` deprecated r181); `FileLoader.load`/`ImageBitmapLoader.load` return nothing (r184; use `loadAsync` or `onLoad`); `DRACOLoader.setDecoderConfig` deprecated (r185) - use `setDecoderPath('/draco/')`; `DRACOExporter.parse → parseAsync`; `SimplifyModifier.modify()` async (r186); `USDZLoader → USDLoader`; `LWOLoader`/`VTKLoader`/`LottieLoader` deprecated. [V]
- **Loader wiring** (docs-verified pieces): `new DRACOLoader().setDecoderPath(dir)`, `new KTX2Loader().setTranscoderPath(dir).detectSupport(renderer)`, `gltfLoader.setDRACOLoader(d).setKTX2Loader(k).setMeshoptDecoder(MeshoptDecoder)` with `MeshoptDecoder` from `three/addons/libs/meshopt_decoder.module.js`. KTX2 supports only Basis Universal (UASTC/ETC1S) in KTX 2.0 containers; requires WASM; `setWorkerLimit(n)` caps workers. Copy `examples/jsm/libs/{draco,basis}` into `public/` for production. [V docs; setters on GLTFLoader from docs + practice]
- TSL churn (examples of breakage between releases): chaining removed r168; blend fns renamed `blend*` r171; `varying()→toVarying()`, `vertexStage()→toVertexStage()` r173; `PI2→TWO_PI` r181; `directionToColor→packNormalToRGB`, `colorToDirection→unpackRGBToNormal` r185; `positionLocal` no longer reflects skinning, use `positionGeometry` r185; `TiledLighting→ClusteredLighting` r185; `AnamorphicNode` removed → `BloomNode` r185; `GTAONode` params changed r181/r185/r186; `resolution→resolutionScale` on several nodes (r180/r181); `LightProbeGrid→LightProbeGridWebGL` r186. [V] TSL has no stability guarantee: pin `three` exactly and re-read the migration guide on every bump.
- Status statement: no official "stable" label found in docs; secondary sources say WebGPURenderer is the recommended default for new projects with automatic WebGL2 fallback, with Linux Firefox and old iPhones as holes. [P]

### 2.2 React Three Fiber / drei
- **v9.x is `latest`** and is the production line. Needs React 19 (`>=19 <19.4`). v8 ↔ React 18 pairing not re-verified here [U]. v9 migration guide [V]: `Canvas Props → CanvasProps`; `MeshProps`-style exports removed → `ThreeElements['mesh']`; `Node/Object3DNode/...` helpers → `ThreeElement<typeof X>`; automatic sRGB conversion of texture props removed; `useLoader` accepts a loader instance; `extend(Class)` factory form; **StrictMode now inherited from outside the Canvas - remove an inner `<StrictMode>`**.
- **Async `gl`** (v9.x): `gl={async (props) => { const r = new THREE.WebGPURenderer(props); await r.init(); return r }}` plus `extend(THREE)` (from `three/webgpu`) and `*NodeMaterial` JSX. R3F owns/disposes the returned renderer. [V r3f.docs.pmnd.rs/api/canvas]
- Canvas defaults (v9 docs): `frameloop="always"`, `dpr=[1,2]`, `flat` false = **ACES Filmic tone mapping on**, sRGB output, WebGLRenderer antialias+alpha+high-performance, default camera fov 75 pos [0,0,5], `shadows` true = PCFSoft. [V] Because three itself defaults to NoToneMapping, R3F's ACES default is a frequent source of "washed/desaturated vs my glTF viewer" - set `flat` or `gl={{ toneMapping: AgXToneMapping/NeutralToneMapping }}` deliberately.
- **v9.8.x fixes worth knowing** (gh 9.8.2 notes): `setDpr` is overwritten by the `dpr` prop on every Canvas re-render; dpr now follows display/zoom changes; `frameloop="demand"` now requests a frame when an object is removed; portal memory leak fixed. [V]
- **R3F v10 = alpha only** (alpha.5 2026-09-08; daily canary). Do not default to it. Facts from its migration doc: peers three `>=0.185` and React `<19.4` (r181-r184 cannot install v10); `state.gl → state.renderer` (gl still works with a warning); `<Canvas renderer>` opts into WebGPU with automatic init (also `renderer={{...}}` or an instance); three entries `@react-three/fiber` (both, lazy), `/legacy` (WebGL only), `/webgpu` (WebGPU only); `state.clock` removed (use `{time, delta, elapsed}`); `useFrame` numeric priority >0 deprecated → `{ phase: 'render' }`; `onUpdate` prop removed; `<Canvas shadows>` moves into renderer settings; React Native moved to `@react-three/native`; TSL hooks (`useUniforms`, `useNodes`, `usePostProcessing`/`useRenderPipeline`) live in `@react-three/tsl`. [V]
- drei key helpers confirmed in README/docs index (v10.7.9): `useGLTF`/`Gltf`, `Environment`/`useEnvironment`, `ScrollControls`, `View`, `PerformanceMonitor`, `AdaptiveDpr`, `Bvh`, `Preload`, `Html`, `Stats`/`StatsGl`. Note: drei is **WebGL-oriented in 10.x**; a WebGPU tree exists only in the 11 alpha (several components still classified "todo"). [V gh release notes + README]
- @react-three/postprocessing 3.2.0 wraps pmndrs `postprocessing` ⇒ **WebGLRenderer only**. [B peers + README; WebGPU incompatibility is inference from README's WebGLRenderer-only API - grade P]
- @react-three/rapier 2.2.0: peers fiber ^9, React 19; last release 2025-11. @react-three/xr 6.6.x actively released (2026-10-13), peers fiber >=8. [B]
- @react-three/xr usage: `createXRStore()`, `<XR store>` inside `<Canvas>`, `store.enterAR()` / `enterVR()` called from a user gesture; features: hit-test, anchors, hand handles, teleport, DOM overlay. [V pmndrs/xr README]

### 2.3 Next.js App Router
- `ssr: false` with `next/dynamic` **is not allowed in a Server Component** (build error) - wrap in a Client Component (`'use client'`) and put the dynamic import there. Automatic code-splitting is not applied when a Server Component dynamically imports a Client Component. [V nextjs.org/docs/app/guides/lazy-loading, updated 2026-03-10]
- Rules of thumb [P/B]: any file using `<Canvas>`, `useFrame`, `useThree`, drei, or touching `window` needs `'use client'`; keep the scene in one client module, load it via `dynamic(() => import('./Scene'), { ssr: false, loading })` from a client wrapper, and keep Server Components for copy/SEO around it. R3F/three do not need `transpilePackages` in current setups [U - not found necessary in 2025-26 starters; check if a dep ships untranspiled ESM].
- React 19 Strict Mode double-mounts effects in dev: renderers, loaders, geometries created in effects must be disposed in cleanup; R3F handles disposal of its own JSX objects; hand-made `WebGPURenderer` needs `await init()` guard against unmount races. [P]
- Spark's official Next.js example marks Spark modules `"use client"`; **Spark's WASM `new URL()` breaks under webpack** (examples use Vite/Turbopack, or disable `parser.url` in webpack config); older Node (<21) SSR may trip on `navigator`. [P from spark-react-* repos via search; repos last pushed 2025-07-16 and pin Spark 0.1.x / three 0.178, so re-check against Spark 2.x]
- Spline: `@splinetool/react-spline` default import is client-only; `@splinetool/react-spline/next` renders a server-side blurred placeholder. [V github README]
- Next 16 default bundler (Turbopack) vs webpack affects WASM/`new URL()` handling [U - not verified here].

### 2.4 Post-processing choices
- pmndrs `postprocessing` (6.39.5): `EffectComposer` + `RenderPass` + `EffectPass`; merges effects into one pass; WebGLRenderer only; set `outputColorSpace = SRGBColorSpace` and it follows; use `HalfFloatType` buffers for HDR bloom. [V README]
- three built-in: WebGLRenderer → `EffectComposer` (addons) + `OutputPass`; WebGPURenderer → `RenderPipeline` (r183 rename of `PostProcessing`) with TSL nodes (`bloom`, `fxaa`, `ssao`/`GTAONode`, `taa`/`TRAANode`, `dof`, `ssr`, `ssgi`, `DotScreenNode`...). API unstable across r180-r186 (see TSL churn list). [V]
- Pick: WebGL + R3F → @react-three/postprocessing; WebGPU/TSL → RenderPipeline (R3F 10: `useRenderPipeline`). Never mix pmndrs composer with a WebGPURenderer. [P]

### 2.5 Spline
- Packages: `@splinetool/runtime` (2.0.89, released daily) + `@splinetool/react-spline` (4.1.0, stale since 2025-07). Install both: `npm i @splinetool/react-spline @splinetool/runtime`. Props: `scene` (URL to `.splinecode`), `onLoad(app)`, `renderOnDemand` (default true), pointer/key/scroll event handlers; app methods `emitEvent`, `emitEventReverse`, `findObjectByName/Id`, `setZoom`. CORS issues → self-host the `.splinecode`. [V README]
- Export options (secondary, The New Stack + Spline docs via search): Vanilla JS, Three.js, React, Next.js, R3F; **animations/events work only in the Vanilla JS and React exports**; exported code edits do not sync back to the Spline file. [P]
- Performance: Spline editor has a Performance panel under Export that flags too many objects/clones/polygons; no official polygon ceiling found. [P] Treat `.splinecode` as a heavy opaque runtime (own renderer) that cannot share a scene with your three.js scene.
- MCP: **no official REST API**; the best-known community `aydinfer/spline-mcp-server` is archived and only generates runtime code; another community `spline-mcp` exists. The New Stack (headline: Spline rebuilt its editor and "handed the keys to Claude Code") reports a Claude Code workflow, but I could not retrieve the article body or confirm an official MCP. [P/U]

### 2.6 Gaussian splats
- **Spark** (sparkjs.dev, MIT, World Labs): three.js-native; `new SparkRenderer({ renderer })` added to scene; `new SplatMesh({ url })`; formats **.ply (incl. compressed), .spz, .splat, .ksplat, .sog**; multi-splat correct sorting; dynamic edit/animation; targets ~98% WebGL2 devices; 2.3.0 added on-demand rendering and a GPU leak fix (`SparkRenderer.dispose()` disposes geometry/material); `SplatMesh` now behaves more like a normal Object3D (clone, visible, layers, renderOrder). [V README/CHANGELOG, P for PR #196 detail]
- R3F: official examples exist (`sparkjsdev/spark-react-r3f`, `-nextjs`, `-react-router`) using `extend` for `SparkRenderer`/`SplatMesh`; they are from 2025-07 and pin Spark 0.1.x / three 0.178 / R3F 9.2 - **re-verify against 2.x**. [B]
- `@mkkellogg/gaussian-splats-3d`: author states no longer in active development, recommends Spark. `.ksplat` is its own compressed format. [V README]
- `gsplat.js` (HF): `.splat` (raw Uint8 buffer, **no SH, colours not view-dependent**) and `.ply` with converter; repo still receiving pushes. [V README]
- PlayCanvas SuperSplat (MIT, active 2026-10-05) is the editor/cleaner for .ply → compressed/SOG outputs. [B repo; role is P]
- Format cheat sheet: `.ply` = INRIA full-precision (huge); `.splat` = antimatter15 compact, no SH; `.ksplat` = mkkellogg compressed (tool-specific); `.spz` = Niantic compressed (small, Spark native); `.sog` = PlayCanvas compressed. [V Spark README links]

### 2.7 WebXR / AR
- three: `renderer.xr.enabled = true`, `ARButton`/`VRButton` addons, `setAnimationLoop` required (not rAF) [P; standard]. R3F: `@react-three/xr` v6 store API above.
- iOS: Safari has **no WebXR immersive-ar**; AR = Quick Look with USDZ. `<model-viewer>` `ar-modes` values `webxr`, `scene-viewer` (Android), `quick-look` (iOS); `ios-src` points to a USDZ; iOS users download the model twice (GLB + USDZ). A `prepareUSDZ()` helper exists in recent API docs (unverified how it is invoked). [V docs.json snippet + P]
- model-viewer 4.4.0 (Apache-2.0) is actively maintained and is the lowest-effort AR/viewer path for a single product model. [B]

### 2.8 Timeline/scroll tooling
- Theatre.js: `@theatre/core`/`r3f` 0.7.2 last published 2024-05-19; repo last push 2024-08-14 ⇒ **effectively dormant ~2 years**; its R3F integration (`@theatre/r3f`) is the part to avoid for new work. [B]
- Active alternatives for scroll/timeline: motion 14.3.0 (2026-10-15), gsap 3.15.0 (2026-04), lenis 1.3.27, drei `ScrollControls`, `three-stdlib`. (Project-local constraint: this repo bans GSAP/Lenis, so skill must stay stack-agnostic.) [B]

### 2.9 Verification tooling
- **Spector.js** (MIT, active 2026-10-12): WebGL/WebGL2 frame capture; extension or npm `spectorjs`; **ships an MCP server** (`mcp/README.md`) for AI capture/inspection; WebGPU not mentioned. [V README]
- **r3f-perf** 7.2.3: last release 2024-11; peers not re-checked against R3F 9.8/React 19.3 [U]. **stats-gl** 4.2.3 (active, supports WebGL + WebGPU timing; drei exposes `StatsGl`). `stats.js` 0.17.0 last 2022. [B]
- Headless screenshots: Chrome's own guidance (blog "Supercharge Web AI model testing") says headless Chrome disables GPU by default and recommends `--use-angle=vulkan --enable-features=Vulkan --disable-vulkan-surface --enable-unsafe-webgpu` on Linux for WebGPU; software path `--use-angle=vulkan --use-vulkan=swiftshader --use-webgpu-adapter=swiftshader` (third-party tool preset); **without it a screenshot succeeds with a black canvas**. `--use-gl=angle --use-angle=swiftshader` for WebGL under Playwright is plausible but **not confirmed by any source** - test via `chrome://gpu` / `gl.getParameter(UNMASKED_RENDERER)` in the target environment. [P/U]
- Always add `preserveDrawingBuffer` only for capture needs; prefer `canvas.toDataURL()` after a forced `renderer.render()` or Playwright `page.screenshot()` after waiting for a "ready" flag (e.g. `window.__sceneReady`). [P]

## 3. Stale-API traps an LLM will make

1. **Clock**: `new THREE.Clock()`/`clock.getDelta()` → deprecated r183; use `Timer` + `timer.connect(document)`; in R3F 9 `state.clock` still exists but is **removed in R3F 10**.
2. **`outputEncoding`/`sRGBEncoding`/`texture.encoding`** → gone since r152; `outputColorSpace`, `colorSpace`, `SRGBColorSpace`. `renderer.physicallyCorrectLights`/`useLegacyLights` obsolete.
3. **Forgetting `await renderer.init()`** for `WebGPURenderer` (blank canvas, no error) - and using `renderAsync()` after init (deprecated r181; use `render()`).
4. **`import ... from 'three/examples/jsm/...'`** in new code: prefer `three/addons/...`. `three-stdlib` re-exports are usually unnecessary now (check TS types).
5. **`RGBELoader`** → `HDRLoader` (r180); `RGBMLoader` removed; `HDRJPGLoader` removed r167 → `UltraHDRLoader`.
6. **`PostProcessing`** (WebGPU) → `RenderPipeline` (r183); `renderer.renderAsync` post path; chained TSL calls (`outputPass.fxaa()`) removed r168; `rangeFog/densityFog` deprecated; `PostProcessingUtils` → `RendererUtils`.
7. **`PCFSoftShadowMap`**: deprecated r182 on WebGL, removed r186 on WebGPU - use `PCFShadowMap`/`VSMShadowMap`. R3F `shadows` (true) selects PCFSoft in v9 docs - check warnings.
8. **`KTX2Loader.detectSupportAsync`** → sync `detectSupport`; **`DRACOLoader.setDecoderConfig`** deprecated; `FileLoader.load()` return value gone (r184).
9. **`envMapIntensity` on `scene.environment`** no longer works (r163) → `scene.environmentIntensity`. Env/background rotation semantics changed r184; PBR look changed r181/r185/r186 - do not tell users "same HDRI looks the same".
10. **`THREE.Geometry`, `WebGL1`, `uv2`** (→ `uv1`, r152), `WebGLMultipleRenderTargets` (r162), `TextGeometry.height` → `depth` (r163), `CapsuleGeometry.length → height` (r176), `Material.type` read-only (r170).
11. **R3F**: `import { Canvas } from '@react-three/fiber/native'` (R3F 10 → `@react-three/native`); `MeshProps`/`Object3DNode`/`Props` types (v9 removed); inner `<StrictMode>`; assuming `useLoader` auto-sRGB's texture props (removed in v9); `<Canvas gl={(canvas) => new WebGLRenderer({ canvas })}>` (v9 passes constructor **props**, not canvas).
12. **Recommending R3F 10 / drei 11 as current**: they are alpha/canary; `latest` is 9.8.2 / 10.7.9. Pairing: drei 10.x needs fiber ^9; R3F 10 needs three ≥0.185 (so r181-r184 users cannot upgrade). `state.gl`→`state.renderer`, `<Canvas renderer>` exist only in 10.
13. **`@react-three/postprocessing` with WebGPU** will not work; R3F 9 `gl` async factory + `*NodeMaterial` requires `extend(THREE)` from `three/webgpu` (and mixing `three` + `three/webgpu` class identities is a risk [U]).
14. **`dynamic(..., { ssr: false })` inside a Server Component** (e.g., `app/page.tsx`) fails the build; move to a `'use client'` wrapper.
15. **`@theatre/r3f`** for new projects (dormant since 2024); `r3f-perf` assumed current (stale since 2024-11); `@mkkellogg/gaussian-splats-3d` as the default splat lib (author recommends Spark); Spark examples with `^0.1.x` APIs.
16. **ACES default in R3F**: LLMs assume three's no-tone-mapping default and then mis-tune lights/exposure; also `toneMapping` set on renderer is ignored by post chains unless `OutputPass`/`toneMapped` handled.
17. **TSL**: `positionLocal` for skinned meshes (r185 → `positionGeometry`), `PI2`→`TWO_PI`, `uniforms()`→`uniformArray()`, `varying()`→`toVarying()`; TSL code from 2024-25 posts is mostly stale.
18. **Spline**: `<Spline>` default import for SEO-critical hero in Next (use `/next`); expecting Spline events/animations in Three.js/R3F export; no official MCP.
19. **WebXR on iOS**: assuming `immersive-ar` works in Safari; correct answer is USDZ Quick Look.
20. **Headless QA**: assuming a plain headless screenshot proves the scene rendered (blank/black canvas passes); need GPU/SwiftShader flags and a pixel-variance check.

## 4. Gaps / not verified
- Official three.js statement of WebGPURenderer "stable" status and TSL stability policy: not found in docs [U].
- three.js docs `Color-management` manual page and `ColorManagement` page returned 404 via fetch; colour facts rest on WebGLRenderer docs + migration guide.
- R3F default tone mapping in v10 (renderer prop) and its WebGPU-side default: not read.
- Playwright + SwiftShader exact flag set for WebGL (and WebGPU) in 2026 Chrome: unconfirmed; needs a local experiment (do not run here).
- Spark 2.x R3F `extend` code and perf-tuning page (`sparkjs.dev` sub-pages 404'd); format feature matrix (SH degrees, LoD) from Spark docs.
- Spline official export doc was unreachable (404); export/animation limits are secondary. Official MCP existence unconfirmed. Spline perf ceilings unknown.
- model-viewer `prepareUSDZ`/auto-USDZ behaviour, and Android `scene-viewer` requirements, from docs not read.
- Browser WebGPU support table is from secondary blogs (Chrome 113+, Safari 26, Firefox Windows/macOS yes, Linux/Android partial); needs caniuse/MDN confirmation.
- r3f-perf compatibility with R3F 9.8 / React 19.3; whether `transpilePackages` is ever required; three-stdlib vs `three/addons` overlap.
- Bundle sizes are CDN-file gzip numbers, not a real Next build measurement.
