# L2 — three.js / R3F realism toolbox (r186)

Grades: [V] source/official, [B] measured, [P] practitioner, [U] unverified/estimate. Facts checked 2026-10-16 via `gh api` (three r186 tag, library repos) and `npm view`. Costs in ms are order-of-magnitude [U] unless marked; they scale with resolution and GPU, so measure on target.

Versions seen [V, npm]: three 0.186.1; R3F 9.8.2; drei 10.7.9; @react-three/postprocessing 3.2.0; postprocessing 6.39.5 (peer three <0.187); n8ao 2.0.1; three-gpu-pathtracer 0.0.27 (peer three >=0.185); @react-three/gpu-pathtracer 0.3.2; realism-effects 1.1.2; @sparkjsdev/spark 2.3.1; three-mesh-bvh 0.9.16.

## 1. Ranked table (impact per cost)

| # | Technique | Fixes | WebGL | WebGPU | Cost | Impact |
|---|---|---|---|---|---|---|
| 1 | Contrasty custom IBL (PMREM from a scene with strip/softbox emitters) | Flat, plasticky metals; no reflection shape | yes | yes | one-off bake, ~0 per frame | Highest |
| 2 | Tone mapping choice + exposure (AgX / Neutral / ACES) and correct color space | Clipped highlights, washed colour | yes | yes | ~0 | Very high |
| 3 | Material correctness (metalness 1, roughness map, normal detail, anisotropy, clearcoat) | CG-looking surfaces | yes | yes | low (texture memory) | Very high |
| 4 | Baked AO / lightmaps / baked env from Blender | Missing contact darkening and bounce | yes | yes | 0 runtime; texture MB | High |
| 5 | Shadows: PCSS / VSM / contact + accumulative baked | Hard or floating shadows | yes | yes (VSM) | low–med | High |
| 6 | N8AO / GTAO ambient occlusion | Crevice darkness for dynamic scenes | yes | GTAO node | 0.5–2 ms [U] | High |
| 7 | Bloom (luminance threshold or selective) | Specular glints, emissive glow | yes | yes | ~0.5–1.5 ms [U] | Med–high |
| 8 | Grade: LUT, vignette, grain, mild chromatic aberration | "Photographic" finish | yes | yes | ~0.3 ms [U] | Medium |
| 9 | Anti-aliasing: MSAA / SMAA / TRAA | Shimmering thin highlights | yes | TRAA node | MSAA mem; SMAA <1 ms | Medium (high for thin blades/edges) |
| 10 | RectAreaLight (LTC) | Soft rectangular specular highlights on glossy surfaces | yes (needs UniformsLib) | yes | med; no shadows | Med–high for studio looks |
| 11 | DOF (bokeh) | Missing lens depth cues | yes | `DepthOfFieldNode` | 1–3 ms [U] | Medium |
| 12 | Planar reflections (MeshReflectorMaterial / Reflector) | Floor reflections | yes | `webgpu_reflection*` | scene re-render | Medium (one plane only) |
| 13 | SSR | Dynamic reflections of objects | `SSRPass` | `SSRNode` | 2–4 ms [U] | Medium; artifacts |
| 14 | Screen-space GI (SSGI) | Colour bleed, bounce light | no first-party (realism-effects stale) | `SSGINode` | 3–8 ms [U] | Medium; noisy |
| 15 | Voxel GI (VXGI) / LightProbeGrid | Diffuse bounce for moving lights | no | r186 addons | heavy; probe bake cheap at runtime | Medium |
| 16 | Transmission / dispersion / iridescence | Glass, gems, thin-film | yes | yes | transmission = extra scene pass | Material-specific |
| 17 | Godrays / volumetrics | Atmosphere | postprocessing GodRaysEffect | `GodraysNode` | 1–3 ms [U] | Mood only |
| 18 | Motion blur | Fast-motion smear | custom | `MotionBlur.js` | 1–2 ms [U] | Medium for video |
| 19 | Progressive path tracing | Everything (true GI, soft shadows, caustics-ish) | deprecated WebGL backend | `WebGPUPathTracer` | seconds–minutes to converge | Ceiling |
| 20 | Gaussian splats | Captured-scene realism | yes (Spark) | — | MB heavy; static | Shortcut for captured scenes only |

Rule: do 1–5 before any screen-space effect. Most "AI path-traced" looks that fail in real time fail at #1, #3 and #4, not at GI.

## 2. Recipes

### 2.1 Custom contrasty environment (the highest-value trick)
Why: metal and glossy materials show only what the environment contains. An HDRI of a sky gives soft, low-contrast reflections; photographic product looks use dark rooms with a few bright strips.

Vanilla [V PMREMGenerator.js r186: `fromScene(scene, sigma=0, near=0.1, far=100, options)`, `fromEquirectangular`, `fromCubemap`]:
```js
const envScene = new THREE.Scene(); envScene.background = new THREE.Color(0x050505);
const strip = new THREE.Mesh(new THREE.PlaneGeometry(4, 0.4),
  new THREE.MeshBasicMaterial({ color: new THREE.Color(1,1,1).multiplyScalar(30), side: THREE.DoubleSide }));
strip.position.set(-3, 2, -2); strip.lookAt(0,0,0); envScene.add(strip);   // add 2–4 strips, one warm rim, one cool fill
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(envScene, 0.02).texture;              // small sigma keeps edges crisp
```
- Emitter intensity must be >1 (10–50) so reflections survive tone mapping; use a half-float pipeline (default).
- R3F: drei `<Environment resolution={256} frames={1}><Lightformer form="rect" intensity={20} position={[-3,2,-2]} scale={[4,0.4,1]} /></Environment>` [V drei src/core/Environment.tsx, Lightformer.tsx]. `frames={1}` bakes once; omit it only for animated emitters.
- Cost: PMREM bake is one-off (tens of ms); memory ~ cubemap 256² x 6 + mips (a few MB).
- Pitfalls: emitters outside the camera of the cube render are invisible; background stays separate (`scene.background`) unless you want it; `environmentIntensity` and `backgroundBlurriness` are scene/material properties in r186 [V Environment.tsx props].
- Not for: scenes that need real environment context in view (outdoor products) — use an HDRI and add strips on top.

HDRI path: `HDRLoader` (renamed from RGBELoader; pathtracer changelog confirms [V]) or `UltraHDRLoader` -> `pmrem.fromEquirectangular`. 1k–2k HDR is enough for IBL; 4k only if visible as background.

### 2.2 Tone mapping and colour
`renderer.toneMapping`: `AgXToneMapping`, `NeutralToneMapping` (Khronos PBR Neutral), `ACESFilmicToneMapping` exist in r186 [V constants.js]. Neutral preserves albedo (good for product gold/colour fidelity); ACES saturates and crushes; AgX is desaturating highlights gracefully. Set `toneMappingExposure` per scene. In pmndrs postprocessing, disable the renderer's mapping and use `ToneMappingEffect`, otherwise it is applied twice or not at all [P]. Gold needs `color` ≈ (1.0, 0.77, 0.34) linear-ish base with metalness 1 and low-mid roughness; verify with the env, not under a flat ambient.

### 2.3 MeshPhysicalMaterial features [V r186 MeshPhysicalMaterial.js: anisotropy, clearcoat, dispersion, iridescence, sheen, transmission, retroreflectivity (new)]
| Feature | Use | Notes |
|---|---|---|
| `anisotropy` + `anisotropyRotation` (+ map) | Brushed metal streaks, hair, satin | Needs tangents (glTF `KHR_materials_anisotropy` supported; examples `webgl_loader_gltf_anisotropy`) |
| `clearcoat`, `clearcoatRoughness` | Car paint, lacquer, wet look | Extra specular lobe; cheap |
| `sheen*` | Cloth | Not for metal |
| `iridescence*` | Oil film, soap, anodised metal | Cheap |
| `transmission`, `thickness`, `ior`, `attenuation*` | Glass, liquids | Triggers an extra opaque-scene render for transmissive objects; blur via mips; costly with many objects |
| `dispersion` | Gems, prism fringe | Requires transmission; multiple samples in shader |
| `specularIntensity/Color` | Tune dielectric F0 | Do not use to fake metals |
Pitfall: stacking many physical features multiplies shader cost on mobile.

### 2.4 Textures and detail
- Normal + roughness detail at 1k–2k beats geometry for micro-scratches. Pack ORM (AO/rough/metal) in one texture. KTX2/Basis (via `KTX2Loader`) cuts VRAM ~4–6x.
- Budget [U]: 4 maps of 2k with mips ≈ 4 x 21 MB uncompressed RGBA; on mobile keep total <150 MB GPU.
- Anisotropic filtering: `texture.anisotropy = renderer.capabilities.getMaxAnisotropy()` for floors/blades at grazing angles.
- Not for: large textures on tiny on-screen objects.

### 2.5 Baked lighting from Blender (strongest "path-traced look" per ms)
1. Blender Cycles: bake Combined/Diffuse-light or AO to a second UV set (UV1) with Smart UV unwrap + margin.
2. Export GLB. glTF only carries `occlusionTexture`; three maps it to `aoMap` and applies `texture.channel = texCoord` [V GLTFLoader.js r186 lines ~3448–3451, 3709]. glTF has no lightmap slot: assign `material.lightMap = bakedTexture` manually and set `bakedTexture.channel = 1` (the r186 `Texture.channel` property [V Texture.js]; this replaces the old `uv2`).
3. Colour spaces: lightMap bake sRGB texture -> `colorSpace = SRGBColorSpace`; AO/ORM linear.
4. Use `lightMapIntensity` / `aoMapIntensity` to tune [V webgpu_materials_lightmap example uses `lightMapIntensity`].
5. Baked env per object: render `CubeCamera` once from object centre (or bake Cycles HDR probe) -> `material.envMap`; `envMapIntensity` to taste.
Cost: zero runtime; the price is static lighting (no moving lights, motion-blades casting live bounce).
Pitfall: lightmapping a diffuse-only bake on a mirror-like material adds nothing; bake for diffuse parts, keep specular live.
Hybrid: static scene baked + hero object live with custom IBL.

### 2.6 Lights
- RectAreaLight (WebGL): `RectAreaLightUniformsLib.init()` once [V addons/lights/RectAreaLightUniformsLib.js; the class "is only relevant when using RectAreaLight with WebGLRenderer"]. Works only with `MeshStandardMaterial`/`MeshPhysicalMaterial`; no shadows, no light through RectAreaLight to transmission. WebGPU has `RectAreaLightTexturesLib` and `webgpu_lights_rectarealight` [V].
- Light probes: `LightProbe` + `LightProbeGenerator` (SH from cube map) for ambient fill from a baked env [V `src/lights/LightProbe.js`, `addons/lights/LightProbeGenerator.js`]. r186 adds `LightProbeGrid` (WebGPU, bakes SH grid from cubemap captures; `LightProbeGridWebGL.js` also exists) with examples `webgpu_lightprobes*`, `webgl_lightprobes*`, sponza [V]. Use for moving objects inside a baked scene; grid size drives bake time.
- Spot/Dir/Point: use 1–3 key lights with shadows; many lights with shadows are the main performance trap.
- Not for: RectAreaLight when you need shadows — fake with a spot + soft shadows.

### 2.7 Shadows
| Option | API | Notes |
|---|---|---|
| PCF | `PCFShadowMap` (r186: `PCFSoftShadowMap` deprecated -> PCF) [V constants.js] | Default; use `shadow.radius`, `blurSamples` with VSM |
| VSM | `VSMShadowMap`; "all receivers also cast" [V constants.js]; example `webgpu_shadowmap_vsm` | Soft, can light-bleed |
| PCSS | drei `<SoftShadows size samples focus />` [V softShadows.tsx] — patches shader chunk globally | Contact-hardening look; global shader patch, remove before changing materials; costly in samples |
| ContactShadows | drei `<ContactShadows opacity blur far resolution />`; three `webgl_shadow_contact`, `webgpu_shadow_contact` [V] | Cheap grounding for floating products; single plane |
| AccumulativeShadows + RandomizedLight | drei: `frames`, `temporal`, `blend`, `limit`, `alphaTest`, `colorBlend` [V AccumulativeShadows.tsx] | Baked soft area-light shadow over N frames; static only |
| Progressive/baked | `webgpu_shadowmap_progressive` [V] | Static scenes |
Rule: for a static hero, use AccumulativeShadows (or Blender bake). For dynamic, PCF + ContactShadows + AO.

### 2.8 Ambient occlusion
- N8AO: `n8ao` 2.0.1, `N8AOPass` / `@react-three/postprocessing` `<N8AO>`; half-res mode; neural denoise quality modes `Neural-Low/Medium/High` (4/8/16 denoise samples at 16 AO samples, full res) [V n8ao README]. Best default AO on WebGL. Color option approximates tint bounce.
- three GTAO: `GTAOPass` (WebGL) [V postprocessing/GTAOPass.js]; `ao()` node `GTAONode` with prepass depth+normal, applied via `builtinAOContext` [V GTAONode.js docblock]. Also `SSAOPass`, `SAOPass` (older/noisier).
- Pitfall: AO applied after lighting darkens speculars/emissives; apply on diffuse (node `builtinAOContext`) or keep radius small. Not for: scenes with fully baked AO (double darkening).

### 2.9 Reflections
- Planar: drei `MeshReflectorMaterial` (blur, mixStrength, resolution) — floor only, re-renders scene at reduced res [V src/core/MeshReflectorMaterial.tsx]. three `Reflector`; WebGPU `webgpu_reflection`, `_blurred`, `_roughness` [V].
- CubeCamera: update once for static, or every N frames; drei `<CubeCamera>` [V].
- SSR: WebGL `SSRPass` (+`ReflectorForSSRPass`) [V]; WebGPU `ssr()` `SSRNode` with `stochastic`, `reflectNonMetals`, `binaryRefine`, `environmentNode` options (equirect with CPU data, not PMREM) [V SSRNode.js docblock]; denoise example `webgpu_postprocessing_ssr_denoise`. Fails on off-screen content and edges: always fall back to env reflection. Not for: glossy metal that mostly reflects the environment (the env already does it).

### 2.10 Screen-space and voxel GI
- WebGPU `ssgi()` [V SSGINode.js]: recommended `sliceCount`/`stepCount` with TRAA: low 1/12, medium 2/8, high 3/16; total samples = slice*step*2; example `webgpu_postprocessing_ssgi` uses scene pass + MRT (diffuse, normal, velocity) then `traa`. Also `webgpu_postprocessing_ssgi_ballpool`.
- WebGPU `vxgi()` voxel cone tracing: `vxgi(depth, normal, scene, camera, 64)`, `coneCount` 2–8, `coneAngle`, `bounces` 0–2, needs TRAA to resolve noise [V webgpu_vxgi.html]. Examples `webgpu_vxgi`, `webgpu_vxgi_sponza`.
- WebGL: pmndrs realism-effects (SSGI, SSR, TRAA, motion blur) — repo `0beqz/realism-effects` last pushed 2024-02-04; npm 1.1.2 published 2023-05-12; README says a v2 is "in the works" on a branch [V repo/npm]. Treat as unmaintained: expect breakage with postprocessing 6.39/three r186 [U compat]. No first-party WebGL GI. In WebGL, fake GI with baked lightmaps + light probes + coloured AO.
- Not for: mobile; scenes dominated by a single hero object (the bounce light is invisible).

### 2.11 Anti-aliasing
MSAA (`samples: 4` on render target / WebGL `antialias: true`) is cheapest and best for thin geometry (blade edges) but incompatible with TRAA ("MSAA must be disabled when TRAA is in use" [V TRAANode.js]). SMAA (`SMAAPass`, pmndrs `SMAAEffect`) is a cheap post fallback. TRAA is required to clean SSGI/VXGI/stochastic SSR noise, introduces ghosting on fast motion (needs velocity MRT). WebGL: `TAARenderPass`/`SSAARenderPass` for stills (accumulate N jittered frames when idle).

### 2.12 Bloom and finish
- Luminance-threshold bloom: pmndrs `BloomEffect` (`luminanceThreshold` >1 only with HDR buffers + `mipmapBlur`). Selective: pmndrs `SelectiveBloomEffect` with `Selection`; three `webgl_postprocessing_unreal_bloom_selective`; WebGPU `webgpu_postprocessing_bloom_selective` and `_bloom_emissive` (MRT emissive) [V examples].
- Grade: `LUT3DEffect`/`LUTPass`/`Lut3DNode` (`webgpu_postprocessing_3dlut`), `FilmNode`/`FilmPass` for grain, `ChromaticAberrationNode` (`webgpu_postprocessing_ca`) [V]. Keep CA ≤0.002 UV, grain 0.03–0.08, vignette subtle. Apply grain after tone mapping and AA.
- Not for: bloom on everything (it reads as "CG glow"); a real path-traced still has little bloom unless a lens effect was added.

### 2.13 DOF, motion blur, godrays
- DOF: `BokehPass` (WebGL), pmndrs `DepthOfFieldEffect`, WebGPU `DepthOfFieldNode` (`webgpu_postprocessing_dof`, `_dof_basic`) [V]. Use sparingly; wrong focus ruins scale.
- Motion blur: WebGPU `MotionBlur.js` node [V]; WebGL via realism-effects (stale). For rendered video prefer accumulation: render N sub-frames per output frame and average (offline-in-browser, section 3.3).
- Godrays: pmndrs `GodRaysEffect`; WebGPU `godrays(depth, camera, light)` needing full shadow setup, directional/point only, bilateral blur + `depthAwareBlend` [V GodraysNode.js].

### 2.14 In-browser path tracing
`three-gpu-pathtracer` (gkjohnson), 0.0.27, 1.9k stars, pushed 2026-10-12 [V].
- Status change: v0.0.25 (2026-09-28) added `WebGPUPathTracer` (import from `three-gpu-pathtracer/webgpu`, WebGPU compute, min three r185) and **deprecated `WebGLPathTracer`** ("will be removed") [V releases]. The older WebGL path is still in the three.js example `webgl_renderer_pathtracer` [V]. 0.0.27 adds SunLight support and `visibleToCameraRays` area lights [V].
- Usage: `new WebGPUPathTracer(renderer)`; `setScene(scene,camera)`; call `renderSample()` per frame; knobs `maxBounces`, `maxSamples`, `frameBudget`, `filterGlossyFactor`, `multipleImportanceSampling`, `transmissiveBackground`; `OIDNDenoiser` and `FSRUpscaler` helpers; `BlurredEnvMapGenerator` to speed convergence; random strategies PCG/Sobol/blue-dither [V API.md].
- Limits [V README]: requires WebGPU; only Standard/Physical materials; Spot/Dir/Point lights only with MIS; emissives not MIS-sampled (use area lights for light that must be noise-free); background alpha caveats with upscaling.
- Demos: physically-based materials, equirect interior, DOF, area lights, denoise, material orb, model-viewer fidelity comparisons, **animation rendering** (`renderVideo.html`) [V README links].
- Speed [U]: a converged still takes seconds to minutes on a laptop GPU, depending on bounces and resolution; no authoritative benchmark found. Measure.
- Use for: hero stills, poster frames, "refine when idle" swap-in over the real-time view (render loop pauses, accumulate; on any input reset), and frame-by-frame clip rendering exported to MP4/WebP, which becomes a pre-rendered video asset. Do not use for live interaction.
- `@react-three/gpu-pathtracer` 0.3.2 (`<Pathtracer>`), last push 2025-07-07 [V]; wraps the older WebGL tracer -> assume it lags the deprecation; check before depending on it.
- Pitfalls: needs `three-mesh-bvh` build per scene (rebuild on geometry change); animated geometry resets accumulation; WebGPU unavailable on part of mobile/Safari fleet [P]; headless capture needs a GPU browser.

### 2.15 Gaussian splats
Spark (`@sparkjsdev/spark` 2.3.1, three >=0.180) and older `@mkkellogg/gaussian-splats-3d` 0.4.7 (last release 2025-01) [V npm]; drei `<Splat>` exists [V]. Shortcut for captured real places/objects: photoreal, static, lighting baked in, tens of MB, sorting cost. Not for: relighting, animation, or sharp CAD-like edges, or anything that must interact with PBR lights.

### 2.16 Fakes and studio tricks
- Matcap (`MeshMatcapMaterial`): zero-lighting sculpted look; works for a fixed camera only.
- Gradient/studio environment: a vertical gradient + two strips beats most HDRIs for product shots (see 2.1).
- Rim lights: two DirectionalLights behind, low intensity, coloured; or fresnel in `onBeforeCompile`/TSL.
- Fresnel shader: `pow(1 - dot(N,V), 3)` added to emissive for edge glow. Cheap.
- Baked specular: render a Cycles specular pass into `emissiveMap` or `envMap` for fixed-view hero shots.
- Fake caustics / glints: sprite or texture animated with scroll; drei `Caustics` exists [V] but costs a pass.
- Not for: any interaction where view changes by >20° (matcap and baked specular break).

## 3. Realism stack by budget

### 3.1 Mobile (target 60 fps, <3 ms post)
Custom studio env (2.1, 128–256 px, `frames=1`), Neutral/AgX tone map, baked AO/lightmap via Blender (2.5), ORM + KTX2 textures, ContactShadows or one baked shadow, MSAA x2–4 or SMAA, tiny bloom at half-res, static grain via texture. Skip: SSR, SSGI, PCSS, transmission, DOF, RectAreaLight with many instances. DPR cap 1.5–2.

### 3.2 Laptop (integrated/mid GPU, 30–60 fps)
Add: physical features (clearcoat/anisotropy), N8AO half-res, AccumulativeShadows baked at load, a RectAreaLight or two (WebGL + UniformsLib), selective bloom, LUT + vignette + grain, MeshReflectorMaterial on one floor, SMAA. WebGPU option: `ssr` with env fallback only.

### 3.3 Desktop (dedicated GPU, WebGPU available)
Add: N8AO full-res neural, TRAA, SSGI (medium preset) or VXGI for dynamic bounce, SSR on glossy dielectrics, DOF, motion blur, transmission/dispersion for glass. Expect noise/ghosting trade-offs; verify at speed.

### 3.4 Offline-in-browser (stills/clips, no real-time budget)
`WebGPUPathTracer` with MIS, denoiser (`OIDNDenoiser`) and optional `FSRUpscaler`; accumulate to `maxSamples`, export PNG. For clips: step animation time, `reset()`, accumulate, capture each frame, encode (WebCodecs/ffmpeg.wasm). Or hybrid: real-time view with path-traced swap-in when idle. Honest ceiling: this reaches Cycles-like lighting for Standard/Physical materials only; no hair/subsurface/volumes/displacement parity. If the reference needs those, render in Blender and ship video.

## 4. Reference demos (realism ceiling)
1. gkjohnson three-gpu-pathtracer demos — https://gkjohnson.github.io/three-gpu-pathtracer/index.html, `viewerTest.html` (model-viewer fidelity comparison), `renderVideo.html`. How: WebGPU compute path tracer over three-mesh-bvh, MIS env lighting, progressive accumulation + denoiser [V README].
2. three.js WebGPU `webgpu_postprocessing_ssgi`, `webgpu_vxgi_sponza`, `webgpu_postprocessing_ssr_denoise` — https://threejs.org/examples/webgpu_vxgi_sponza.html (also `webgpu_postprocessing_ssgi.html`). How: MRT scene pass + SSGI/VXGI + TRAA, TSL nodes [V examples source]. Shows what real-time GI looks like and its noise.
3. Studio-look WebGL baseline: drei Environment + Lightformer + AccumulativeShadows + N8AO — docs https://drei.docs.pmnd.rs (Lightformer, AccumulativeShadows) and n8ao demo https://github.com/N8python/n8ao [V READMEs]. How: custom emitters, baked soft shadows, AO. Cheapest route to "product render" feel.
(Commercial awwwards-style sites usually combine baked Blender lighting, custom env, bloom/grain and video; their internals are not verifiable here [U].)

## 5. Gotchas to feed the feasibility gate
- Real-time ceiling is set by lighting data, not post effects: no caustics, no multi-bounce coloured GI, no accurate glossy inter-reflections between metal parts, no hair/SSS volumes without baking.
- Fixable in real time: reflection shape (env), shadow softness, AO, edge AA, tone/grade, glints (bloom + anisotropy).
- WebGPU-only in r186: SSGI, VXGI, SSR node, TRAA, node-based post chain; WebGL stays with pass-based post, pmndrs effects and N8AO.
- Verification trap: critics compare stills; AO/SSR/TRAA behave differently when static vs moving, so judge both.
