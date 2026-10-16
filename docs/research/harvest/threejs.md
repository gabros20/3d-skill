# Harvest R3: three.js / R3F / shaders / perf / visual QA

Compiled 2026-10-16 from saved community skills under `docs/research/community-scan/sources/` (paths abbreviated `src/`). Grades: [V] official/primary doc or three.js source checked · [B] measured by the source author · [P] practitioner · [U] unverified. Latest three.js tag seen: r186 (`gh api`, 2026-10-16); most sources target r185 + Fiber 9.7 + React 19.

**Licences** (checked via `gh api` 2026-10-16): vladmdgolam MIT · scottstts MIT · majidmanzarpour MIT · OpenAEC/Impertio MIT · MengTo MIT · zebbern MIT · PlayableIntelligence frontmatter MIT (repo none) · linegel ISC · full-stack-skills Apache-2.0 · **no licence (inspire only, do not copy):** EnzeD, CloudAI-X, dgreenheck, openai/plugins, OpusGameLabs repo · **NOASSERTION (treat as inspire only):** millionco, AThevon.

Short names: **EnzeD** = r3f-skills (11); **CAI** = CloudAI-X (10); **VG** = vladmdgolam perf-loading; **MC** = millionco improve-threejs; **DG** = dgreenheck webgpu-threejs-tsl; **SS** = scottstts; **LG** = linegel; **AEC** = OpenAEC/Impertio; **MJ** = majidmanzarpour; **MT** = MengTo; **ZB** = zebbern; **AT** = AThevon; **PI** = PlayableIntelligence.

## 1. Scene setup, renderer, R3F/React 19 boundaries, lifecycle

**Procedure**
1. Read `package.json` + lockfile: three, @react-three/fiber, drei, postprocessing, React major. Fiber 9 is React 19 only (peer `>=19 <19.3`); Fiber 8 + drei 9 for React 18. Never upgrade to fit a recipe. (EnzeD fundamentals; AT header, verified 2026-09-08) [P]
2. Choose renderer: WebGL (default; GLSL, drei shader materials, `@react-three/postprocessing` all work) vs WebGPURenderer (TSL, node materials, `RenderPipeline`). Do not hybridise blindly. (EnzeD renderers; full-stack tsl-vs-classic) [P]
3. R3F: `<Canvas>` parent needs nonzero height; scene code lives in child components of Canvas; DOM UI outside Canvas or via drei `Html`. `dpr={[1, 2]}` is the common clamp.
5. Per-frame motion: mutate refs in `useFrame`, use `delta` in seconds; React state only for discrete changes.
6. Verify: type-check, render in browser, console clean, resize, unmount/remount, Strict Mode cleanup, and for `frameloop="demand"` both wake and return-to-idle. (EnzeD Verify)

**Hard rules**
- NEVER call `useThree`/`useFrame`/loader hooks in the component that creates `<Canvas>`, or inside event callbacks. (EnzeD, AEC)
- NEVER `setState` in `useFrame`; NEVER allocate `new Vector3()/Color()` per frame (hoist to module scope or `useMemo`). (MC, ZB, AT, AEC, all agree)
- NEVER add the same Object3D via `<primitive>` under two parents; clone it. (EnzeD loaders, AEC)
- ALWAYS `useThree(s => s.camera)` selectors, not bare `useThree()`. (AEC, AT)
- ALWAYS keep a stable `args`; changing `args` reconstructs the object. Animate props or refs. (EnzeD)
- ALWAYS call `camera.updateProjectionMatrix()` after fov/near/far/aspect edits; set `texture.colorSpace`; keep exactly one render loop and one final-render owner. (AEC, MC, MJ debug playbook)

**Gotchas**
- `frameloop="demand"` needs `invalidate()` after imperative changes and animations must keep invalidating until settled. (EnzeD, AEC, ZB)
- Frame priority: a positive priority disables automatic render, so its owner must render and coordinate with any composer. (EnzeD, AEC)
- Default Canvas = sRGB output + ACES filmic. `flat` = `NoToneMapping`, `linear` = linear output; neither is a generic fix for washed-out assets. **Conflict:** ZB lists "`canvas-linear-flat` use linear/flat for correct colors". EnzeD is right, three's colour-management doc defaults to `SRGBColorSpace` output. [V-consistent, EnzeD cites the manual]
- On three r182+ use `shadows="percentage"`; bare `shadows` selects deprecated `PCFSoftShadowMap` on Fiber 9. MT hard-codes `PCFSoftShadowMap`: stale. (EnzeD, cites migration guide) [P]

**Disposal / ownership** (EnzeD, MC, AEC, AT agree)
- R3F disposes declaratively owned geometry/materials on unmount. `<primitive object>` is not disposed. Cached loader assets need an explicit owner. `dispose={null}` is for shared resources, not a perf switch.
- Imperative resources: dispose geometry, materials, textures, render targets, PMREM generator, controls (`controls.dispose()` removes listeners), renderer. AEC has a full material texture-slot list. It also says never dispose when merely hiding, use `visible=false`. (AEC, ZB `perf-visibility-toggle`)
- A `key`-flip remount of a material family disposes + reallocates all GPU resources in one frame: **936 ms single frame measured** on ~24 drei transmission materials (VG §2) [B].


**Sources**: EnzeD fundamentals (no licence, inspire), MC (NOASSERTION), AEC (MIT), VG (MIT), ZB (MIT).

---

## 2. Materials, lighting, environment, colour management, art direction → renderer

**Procedure**
1. Fix the colour pipeline *before* judging materials: `outputColorSpace = SRGBColorSpace`, deliberate tone mapping + exposure, environment intensity, post order stable. (MT §3, MJ)
2. Annotate textures: base colour + emissive = `SRGBColorSpace`; normal/roughness/metalness/AO/masks = `NoColorSpace`; HDR/EXR keep loader metadata. Colour hex → `Color` is converted to linear; numeric uniform vectors are already linear, don't convert twice. (EnzeD textures/shaders, MT, MC) [V: three colour-management manual]
3. Lighting: environment (PMREM via drei `Environment`) for PBR reflections/fill + one or two direct lights for direction/shadows. More ambient does not restore missing metal reflections; metals with no `scene.environment` render black. (EnzeD, MC, AEC)
4. Material choice: `MeshBasic` → `Standard` → `Physical` only for clearcoat/transmission/sheen; share materials by role; clone before per-instance edits (cached glTF materials are shared). (EnzeD materials, AEC, MJ "material kit")
5. Art direction to renderer mapping (MJ + MT + SS router): lock subject/silhouette first, then material roles, then key/fill/rim, then atmosphere, then post last. Fog/bloom/darkness must not substitute for missing authored form. Keep a **no-post baseline that still reads** (SS router acceptance gate).
6. Shadows: tighten the shadow camera before raising map size; tune `bias`/`normalBias`; add the light `target` to the scene graph or its matrix never updates; `CameraHelper` to inspect. Limit casters to ≤2 desktop / 1 mobile; never point-light shadows on mobile (6 renders each). (EnzeD lighting, AEC, MJ)
7. Static lighting: `renderer.shadowMap.autoUpdate = false` + `needsUpdate = true` on events; the largest cheap win for static scenes (VG §2) [B].

**Hard rules**
- NEVER tone-map twice; NEVER paste GLSL output chunks into TSL; apply output conversion once. (SS image pipeline, LG, EnzeD)
- ALWAYS map `texture.channel` (0=uv, 1=uv1…) for AO/light maps. **Conflict:** CAI, MT and AEC-era text copy `uv` into `uv2`; that is stale. EnzeD/geometry right. [P, matches r151+ rename]
- `RGBELoader` → `HDRLoader` in modern three; addons import from `three/addons/...`, not `three/examples/jsm`. (EnzeD loaders vs CAI) [P]
- Transmission is not transparency: keep `opacity` 1 and set `thickness`/IOR; `DoubleSide` everywhere hides winding bugs and costs fill. (EnzeD)


**Sources**: EnzeD materials/lighting/textures, MT realtime-architecture (MIT), MJ aaa-graphics (MIT), SS router (MIT), AEC scene-builder (MIT).

---

## 3. Shaders: GLSL, `onBeforeCompile`, TSL/node materials, compute

**Choose the path first** (EnzeD shaders, DG, AEC, full-stack):

| Need | Path |
|---|---|
| Built-in property already expresses it | built-in material |
| Keep PBR lighting, add a tweak | `onBeforeCompile` (WebGL) or `colorNode`/`positionNode` (node mat) |
| Fully custom, WebGL | `ShaderMaterial` / drei `shaderMaterial` / `<shaderMaterial>` |
| WebGPU renderer | TSL node materials only; GLSL does not run |

**GLSL procedure**
1. Uniforms stable: `useMemo` the container, mutate `.value` in `useFrame`; drei `shaderMaterial` exposes `material.uTime`, native uses `material.uniforms.uTime.value`. Never set `needsUpdate` for a value-only uniform change. (EnzeD, AT)
2. `onBeforeCompile`: set before first compile; chunk names are version-sensitive (inspect installed source, render-test after update); animated values in uniforms; when the patch changes generated GLSL set a matching `customProgramCacheKey` (EnzeD). Note CAI's example stashes the shader in `userData` and omits the cache key. **Add customProgramCacheKey for any patch variant** [V: three docs on `Material.customProgramCacheKey`; not shown in CAI].

**Gotchas**
- A backtick or `${` inside GLSL (even in comments) inside a JS template literal ends the string. Write GLSL comments without backticks. (EnzeD)
- Space bugs: `normalMatrix * normal` is view space, don't dot with a world-space camera vector. (EnzeD)
- Custom vertex deformation: raise subdivisions, recompute normals, mirror deformation in depth/distance material for shadows; CPU bounds and raycasts do not follow GPU displacement. (EnzeD, geometry)

**TSL / WebGPU procedure** (DG, EnzeD webgpu ref, LG, AEC)
1. `import * as THREE from 'three/webgpu'`, TSL from `three/tsl`. `await renderer.init()` before first render. In R3F 9 pass an async `gl` factory that inits and returns the renderer. No Fiber 10 alpha APIs on Fiber 9.
2. Build node graphs once (`useMemo`), update uniform nodes, never rebuild per frame.
3. Use `Fn()`, `.toVar()` and `.assign()`. **TSL gotcha (DG):** JS variable reassignment of a scalar node (`v = v.add(1)`) is not intercepted; use `select()`, `.toVar()` + `.assign()`, or assign on buffer elements inside `If()`. Use capital `If`. (DG, AEC)
4. Compute: set storage buffers, dispatch `renderer.compute(node)` after init. **Conflict:** AEC says always `await computeAsync()`; DG says `computeAsync` is deprecated since r181. Checked three source (r186, `Renderer.js`): `computeAsync` still exists and `compute()` auto-falls back to it if not initialised, so both work, prefer `await init()` then `compute()`. [V] LG adds: `computeAsync` resolution is submission, not proof of GPU completion; use readback/timestamps.
5. Device loss: listen to `device.lost`, fresh adapter before re-requesting, restart GPU content only, request only needed limits (DG device-loss/limits) [P].
6. `ShaderMaterial` and `onBeforeCompile` do not port. Drei shader materials do not either. Type-checking proves nothing about GPU compat: render on the target backend and verify the WebGL2 fallback separately. (EnzeD)

**Renames**: `PostProcessing` → `RenderPipeline` (r183, exists in current source); DOF API rewritten r181; `three/nodes` path is old. AEC webgpu ("PostProcessing", "NEVER requestAnimationFrame", "Safari 18+") is partly stale [U].

**Sources**: EnzeD shaders (no licence), DG (no licence), LG (ISC), AEC webgpu (MIT), full-stack tsl (Apache-2.0, link-only, thin).

---

## 4. Postprocessing, bloom, grading

**Procedure**
1. Decide pipeline: pmndrs `postprocessing` / `@react-three/postprocessing` (WebGL) vs three `RenderPipeline` + TSL nodes (WebGPU). Do not install the WebGL composer as a substitute on WebGPU. (EnzeD, DG)
2. One owner renders the final frame. EffectComposer uses a positive frame priority; extra manual `gl.render` overwrites or duplicates it. (EnzeD, AEC)
3. Signal order (SS image pipeline): scene HDR + depth/normal → AO → atmosphere/transparency → **bloom (HDR)** → exposure → **tone map once** → grade/LUT → lens effects → output conversion. In vanilla EffectComposer finish with `OutputPass`; `composer.setSize` alongside `renderer.setSize`. (AEC)
4. Bloom: threshold in HDR before tone mapping; make glow sources emissive/HDR >1, don't flatten the scene; `luminanceThreshold≈1` means nothing glows unless emissive (AT, EnzeD). Selective options ranked by cost: HDR threshold (cheapest) → MRT emissive channel read by bloom (VG, DG, WebGPU) → dual selective passes with material swap (SS; multiple full renders, expensive; the swap must restore in `finally`).
5. Grading: only add adaptive exposure if the brief needs it (SS: 64×36 luminance meter, async readback, weighted log-average, asymmetric adaptation, 32³ LUT after tone map [P, single source]); fixed exposure is the marketing default.

**Hard rules**
- NEVER give `<EffectComposer>` an inline-rebuilt children array: it rebuilds all passes + render targets whenever children identity changes. `useMemo` the effects, gate conditionals so identity is stable. **Measured 100–386 ms per re-render frame in Safari.** (VG §2) [B]
- Toggle features by relinking `outputNode` + `needsUpdate = true`, not rebuilding passes (VG, LG).
- SSAO in the wrapper needs `enableNormalPass`; DOF `target` is a world position, not a ref. (EnzeD)


**Sources**: EnzeD postprocessing, VG (MIT), SS bloom/pipeline/exposure (MIT), DG post-processing, AT (NOASSERTION).

---

## 5. Loading and assets at runtime

**Procedure**
1. `useGLTF` for glTF/GLB (Suspense + cache + Draco/Meshopt); `useLoader` with the right loader otherwise. Conditional loading = conditionally mount a child, never a null URL. Preload what is needed soon (`useGLTF.preload` at module scope), not the catalogue. (EnzeD, ZB, AEC)
2. Configure decoders before first request and use identical settings for preload and load: Draco/Meshopt paths, a **KTX2Loader with `detectSupport(renderer)`**, one worker pool with an owner. (EnzeD loaders)
4. Suspense boundaries: group assets that reveal together; error boundary + retry (Suspense does not catch rejects); inside Canvas use a three fallback or drei `Html`; drei `Loader` lives outside. `useProgress` is not byte-accurate. (EnzeD)
5. **Hide compile + decode behind the loader (VG §1):**
   - Render real frames through the *full* post chain while the loader is up; disable `frustumCulled` for the warm pass so off-screen meshes compile; warm every scroll section/state that activates different materials (Ivress: 6 sections × 3 frames + overlay pass). [P]
   - `await renderer.compileAsync(scene, camera)`; layer-masked cameras are different programs, compile each. Safari: await the second compile before reveal. (VG; MT uses same, with hidden warm frame if unavailable)
   - Gate the reveal on **rendered frames, not asset progress or timers**: `useFrame(..., -999)` counting frames inside the mounted scene, fire at frame ~8. Two timer/progress gates failed in production. Show the loader immediately but paused (`animation-play-state`), un-pause on the signal. [B]
   - Wait 2 RAFs + a microtask after warm-up before fading; start non-critical assets (SFX) on the compile-end event.
   - Chunk one-shot procedural fills (noise texture, impulse response ~40k samples per rAF chunk) and start at creation, not first use.
7. Compression: gltfpack/gltf-transform after export, never Blender Draco; Draco or meshopt per primitive, not both; KTX2 ETC1S for colour, UASTC for normals; assess first, write a new file, compare visually. (AEC optimizer) [P]


**Sources**: VG (MIT), EnzeD loaders/textures, AEC optimizer (MIT), MT (MIT).

---

## 6. Performance: frame loop, adaptive quality, instancing, budgets, leaks

**Triage procedure** (MJ debug-profiler, MT QA §10, MC)
1. Fix the scenario: route, viewport, DPR, state, camera, device tier. Profile the production build, not dev.
2. Baseline p50/p95 frame time, `renderer.info` calls/triangles/geometries/textures/programs, render targets, passes, heap. Classify CPU vs GPU draw / fragment / vertex / memory.
4. Toggle in this order: lower DPR → disable post → disable/freeze shadows → disable transparency/particles → hide chapter groups → swap LODs → neutral basic materials. Interpret: DPR win = fill/post/shadow; basic-material win = shader cost; group visibility win = draw/geometry; particle win = overdraw; no GPU win + high scripting = update/raycast/DOM. (MT §10)
5. Change one thing, re-measure the same scenario, recheck visuals.
6. If DevTools cannot attribute, add frame-attribution tooling behind a URL flag (VG §6): per-frame marks buffer, timed spans (~0.5 ms floor), `gl.info` program/texture/geometry diff by program identity, a dispose tracer with stacks, a module-scope RAF boot tracer. Profiler overhead skews Safari, so attribution runs differ from measurement runs; if all instrumentation is silent it is GC or driver. [B]

**Frame-loop discipline** (all agree): no allocations/`setState` in the hot path; `matrixAutoUpdate=false` + `updateMatrix()` for static; raycast a filtered list; `frameloop="demand"` when it can rest; drei `AdaptiveDpr`/`AdaptiveEvents`/`Bvh`; GPU-resident particle motion from a time uniform; proximity gating with separate enter/exit thresholds (VG §2).

**Instancing / batching**
- `InstancedMesh` for 100+ same geometry+material; set `instanceMatrix.needsUpdate` once per batch; recompute bounds; `args` capacity vs `count`; negative scale unsupported. `BatchedMesh` for different geometries in one call (AEC). Merge only static, non-interactive geometry with `mergeGeometries`; drei `Merged` merges *meshes into instances*, not BufferGeometry (EnzeD).
- PI measured (r183, headless Chromium, M1 Pro, SwiftShader): 19,365 → 2 draw calls, render CPU p95 28.5 → 0.5 ms; 8,000 moving entities → 1 call, 9.9 → 0.5 ms. **Trust draw calls + CPU p95, not FPS, in headless software GL.** [B]

**Adaptive quality** (VG §3, hardened against false positives; contrast MT §12 simple version "120 frames > 22 ms")
1. One flat perf-budget config object (resolution scales, frame skip, kill switches); doubles as debug API.
2. Sample a rolling window **after** reveal; discard the first 2–3 windows after arming.
3. Discard any window containing a frame > ~100 ms (transition, not steady state).
4. Latch degradation one-way; stage the cheapest lever first (DPR only, nothing rebuilt), then tier drop; skip 1–2 windows after each escalation (the degrade itself hitches: GC 794 ms vs 354 ms).
5. Escalate only if the cheap lever measurably failed (compare fps to the fps that triggered the last step).
6. Pin the GPU-tier classification in localStorage (detect-gpu flaps); suspend the monitor during benchmarks; gate mobile Safari at boot (`maxPixelRatio=1`, no SMAA). [P]

**Budgets** (starting contracts, document overruns; sources differ)

MJ budgets (game scaffold; use as config defaults for marketing scenes, document overruns): draw calls ≤300 desktop / ≤150 mobile; triangles ≤750k / ≤300k; geometries ≤300 / ≤200; textures ≤60 / ≤40 (≤256 / ≤128 MB); shadow lights ≤2 / 1, map ≤2048 / ≤1024; post passes ≤2 / 0–1. AEC (generic) is looser: <100 calls target, >500 critical, >50 programs critical; AT: <100 calls, <1M tris. Frame budget 16.6 ms at 60. [P]

**Scroll/input smoothing** (VG §4): clamp the per-frame *step* of the damped lerp, not the target; drei `ScrollControls` `maxSpeed` is rail-units/s, so test with a hard wheel notch. For an authored clip, scrub `clip.time = duration * smoothedProgress` with no second damping layer; stacked smoothing reads soft. (Scroll adapters belong to the scroll lane.)


**Sources**: VG (MIT), MJ (MIT), MT (MIT), PI (MIT frontmatter), AEC (MIT), MC (NOASSERTION), EnzeD.

---

## 7. Interaction, raycasting, physics (brief)

- R3F raycasts only handler-bearing objects, bubbles by distance; `stopPropagation` also blocks farther hits; use `onPointerMissed` for deselect, simple hit proxies/layers/`<Bvh>` for heavy picking, `state.events.update()` only when the camera moves under a still pointer. (EnzeD interaction, AT)
- One active drei control per camera; `makeDefault` lets TransformControls pause orbit. In scroll worlds the hit proxy uses the camera's *rendered* pose while availability uses exact chapter state; give tiny objects DOM controls on mobile. (EnzeD, MT QA §7)
- Physics (Rapier): sim state outside render components, input to the step not the mesh, fixed-step accumulator. Rarely needed on marketing pages. (openai [no licence], MJ)

## 8. Visual validation, QA loops, debugging

**Claim-scoped verdicts** (LG visual-validation, ISC; SS validation protocol, MIT): predeclare each claim (class: visual / mechanism / temporal / performance / GPU attribution / resource / lifecycle) with invariant, truth source, observable, metric, gate fixed **before** looking, and blocking failure. Label numbers Authored / Derived / Measured / Gated. A verdict covers only its claim; appearance evidence cannot substitute for timing or lifecycle proof. Missing evidence is `unmeasurable`, never a pass.

**Procedure**
1. Write a **visual contract** before tuning: subject, silhouette, material separation, motion, camera envelope (near/design/far), observable invariants ("rim visible without bloom"), allowed divergences, frame + memory budgets. (SS)
2. Freeze: three.js revision, backend actually initialised, camera matrices/bookmarks, seed, time or fixed step, viewport, DPR, quality tier, asset versions, colour/output graph.
3. Capture design view + near + far + **no-post baseline** + one diagnostic of the controlling field/pass + one stress case. Controls must change the real pipeline (a label-only debug toggle is worse than none).
4. Test the camera path (MT QA §3): slow forward/reverse, fast flick across 2+ chapters, scrollbar drag, anchor clicks both ways, reload mid-segment, resize/rotate mid-segment, tab hidden 10 s. Evidence matrix per chapter × (1440×900, 768×1024, 390×844, reverse seam, interaction, fallback, ms/calls/tris); toggle DOM copy off, and if the 3D is meaningless it is not carrying the story.
6. Temporal: record t=0 reset, first response, steady, invalidation, recovery; judge at normal speed and frame by frame; stills cannot prove absence of shimmer. (SS, LG)
7. Performance: warm up first, separate compile from steady state, cold and sustained windows on the named target; GPU time needs timestamps (`trackTimestamp: true` before init on WebGPU), never CPU time. Lifecycle: repeat resize/DPR/tier changes and teardown until memory plateaus. (LG, SS)
8. Sign-off record: contract, versions/backend, viewport/DPR/seed/camera/time, modes inspected, metrics, known defects, decision; repeat when mechanism, three version, backend, camera or tier changes.

**Scorecard** (MJ, MIT): 10 categories 0–3 (art direction, hero, obstacles, rewards, world, materials, lighting/render, VFX/motion, UI, performance evidence); *score active-play screenshots, not showrooms*; premium = every category ≥2 and avg ≥2.3; showcase = none <2, ≥6 at 3, avg ≥2.7 + before/after perf. Automatic failures: placeholder primitive plus glow, fog/bloom standing in for geometry, UI overlap/clipping, no active screenshot, no renderer diagnostics. Adapt category names to marketing scenes (hero object, environment, copy-vs-3D hierarchy).

**Determinism hooks** (MJ harness): test hooks `seed`, awaited `setState` (throws on unknown), `setPausedForScreenshot`, `setReducedMotion`, `hideDebugUi`; order unpause, seed, state, freeze, stabilise noise/shake/post, hide debug, await fonts + frames. Playwright `maxDiffPixelRatio` low for UI, a little higher for WebGL AA, never high enough to pass real regressions. Headless SwiftShader FPS is unreliable (PI).


**Debug triage order** (MJ playbook): reproduce on the same URL, read console/page/network errors, confirm the expected build is on that port, find the owner. Blank canvas: element exists, CSS size non-zero, drawing buffer matches DPR, context created, exactly one loop, camera aspect/near/far/aim, objects at expected scale. Delta in seconds, clamped for tab sleep; expose `renderer.info` for harness reads; never test via `file://`.

**Sources**: LG (ISC), SS (MIT), MJ (MIT), MT (MIT), MC (NOASSERTION), VG (MIT).

---

## Conflict ledger

| Topic | Claim A | Claim B | Verdict |
|---|---|---|---|
| Canvas `linear`/`flat` | ZB: use for correct colours | EnzeD: not a generic fix | EnzeD [V manual] |
| AO UV set | CAI/MT: copy `uv`→`uv2` | EnzeD: use `texture.channel` | EnzeD [P] |
| Shadow map type | MT: `PCFSoftShadowMap` | EnzeD: `"percentage"` on r182+ | EnzeD [P] |
| Power-of-two | AEC: always | EnzeD: not a WebGL2 rule | EnzeD |
| Post class | CAI/AEC/full-stack: `PostProcessing` | DG/EnzeD: `RenderPipeline` (r183) | DG/EnzeD [V source] |
| Compute | AEC: always `computeAsync` | DG: deprecated r181 | both work in r186; prefer init + `compute()` [V source] |
| Adaptive quality | MT: 120 frames > 22 ms, one-way | VG: 4 hardening rules | VG (measured false positives) |
| Draw-call budget | AEC <100 / AT <100 | MJ ≤300 desktop | MJ for marketing scene; make it a config |
| Bloom selectivity | EnzeD: HDR threshold ok | VG/DG: MRT emissive | threshold first, MRT when bright non-emissive surfaces bleed |

## Gaps

- No source covers Next.js 16 / RSC boundaries for R3F (`use client`, `ssr:false`, lazy Canvas mount, pausing off-screen); needs first-party docs.
- iOS 26 Safari WebGPU availability unverified; check before recommending WebGPU.
- `customProgramCacheKey`, KTX2 profiles, `compileAsync` semantics came from three docs/memory, not fetched this run; re-verify in factcheck.
- Animation (mixer/clips) and physics only skimmed.

## Router signals

| User says | Route to |
|---|---|
| "set up a canvas", "R3F boilerplate", "Next + three", "context lost", "strict mode double mount", "Canvas re-renders" | §1 scene/R3F |
| "washed out", "too dark", "colours off", "black metal", "env map", "tone mapping", "exposure", "make it look premium/cinematic", "lighting rig", "shadows acne/floating" | §2 materials/lighting/colour |
| "custom shader", "glow/fresnel/dissolve", "patch standard material", "TSL", "WebGPU", "compute", "particles on GPU" | §3 shaders (GLSL vs TSL first) |
| "bloom", "glow only on X", "depth of field", "vignette/grain", "LUT", "post effects slow" | §4 postprocessing |
| "load GLB", "preloader", "freeze after loading", "first frame jank", "compress model", "KTX2/Draco" | §5 loading (glTF pipeline detail in the asset lane) |
| "laggy", "FPS drops", "mobile hot", "memory climbs", "too many draw calls", "stutter on scroll", "adaptive quality", "scroll feels soft" | §6 performance |
| "click/hover object", "drag", "raycast", "physics" | §7 interaction |
| "does it look right", "verify", "screenshot evidence", "QA the scene", "regression", "is it premium enough", "blank canvas", "why is it black" | §8 validation/debug |
| "make it better/prettier" with no named system | §2 art-direction mapping, never straight to post (SS router rule) |
