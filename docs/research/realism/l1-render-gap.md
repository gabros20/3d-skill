# L1 — Offline path tracing vs real-time three.js: the render gap

Date: 2026-10-16. Versions: three r186, R3F 9, drei 10, pmndrs postprocessing 6.39, Blender 5.2.

**Evidence caveat.** This lane did not re-fetch pages in-session (no installs, read-only). Claims come from primary docs/source the author knows well; each carries a URL and a grade. Grades: [V] official docs/source, [B] measured/benchmark, [P] practitioner, [U] unverified. Every ms figure is [P]/[U] unless stated: costs vary 3-10x with resolution, GPU and scene, so treat them as order-of-magnitude and **measure on the target device**. Items marked "check r186" depend on a three.js release newer than the author's firm knowledge.

Sources used (all dated as read 2026-10-16 from prior knowledge, not re-fetched):
- S1 Blender manual, Cycles: https://docs.blender.org/manual/en/latest/render/cycles/ [V]
- S2 Blender manual, EEVEE: https://docs.blender.org/manual/en/latest/render/eevee/ [V]
- S3 three.js docs/examples: https://threejs.org/docs/ , https://threejs.org/examples/ [V]
- S4 pmndrs postprocessing: https://github.com/pmndrs/postprocessing [V]
- S5 three-gpu-pathtracer / three-mesh-bvh (gkjohnson): https://github.com/gkjohnson/three-gpu-pathtracer [V]
- S6 N8AO: https://github.com/N8python/n8ao ; GTAO in three examples [V]
- S7 Khronos PBR Neutral: https://github.com/KhronosGroup/ToneMapping [V]
- S8 Blender AgX/Filmic: https://docs.blender.org/manual/en/latest/render/color_management.html [V]
- S9 three.js MeshPhysicalMaterial docs (clearcoat, sheen, iridescence, anisotropy, transmission, dispersion) [V]
- S10 Karis, "Real Shading in UE4" (SIGGRAPH 2013) and Filament docs: https://google.github.io/filament/Filament.html [V]
- S11 WebGL2 / WebGPU specs and caniuse (half-float render targets, EXT_color_buffer_float) [V]

---

## 1. Feature matrix

Visibility: **S** subtle, **O** obvious, **D** defining (dominates photoreal read).

| Feature | Cycles (physical) | EEVEE Next | three.js native | three.js approximation (technique, lib, cost) | Impossible live in browser | Gap |
|---|---|---|---|---|---|---|
| Global illumination, multi-bounce | Unbiased path tracing, N bounces, every surface a light receiver [S1] | Screen-space + light probes + virtual shadow maps; "horizon scan" GI and ray-traced-ish probes, one-ish bounce [S2] | Only direct lights + single env/IBL; no bounce | Baked lightmaps (Blender bake to texture; zero runtime cost, static only); light probes / `LightProbe` SH; env map from a baked cube; fake bounce with coloured low-intensity fill lights or emissive cards; `three-gpu-pathtracer` progressive (seconds to converge, static camera) [S5] | Per-frame dynamic multi-bounce GI on a moving camera + moving blades at 60 fps with full quality | **D** |
| Inter-reflection (blade A in blade B) | Exact, recursive mirror/glossy bounces | Only via screen-space reflections or probes: misses off-screen and back faces | Env map only: object does not see neighbours | Per-object `CubeCamera` (6 renders, 1-3 ms each at 256-512 px; few objects only) [P]; SSR; **bake** the neighbour reflections into the env/lightmap if the scene is rigid; for a rigid blade ring, render one reflection cube from the ring centre | Exact N-object mutual reflection live at scale | **D** for polished metal |
| Reflections | Ray traced, any roughness, exact | SSR (screen only) + reflection probes + planar probes [S2] | `envMap` / scene.environment prefiltered by PMREM; no SSR/planar built in (Reflector in examples is planar) [S3] | PMREM IBL (cheap); drei `<MeshReflectorMaterial>` for floors (+1 scene render, ~1-3 ms [P]); SSR via pmndrs postprocessing `SSRPass`/realism-effects (2-5 ms [P], artefacts at edges); box-projected env [P] | Rough, off-screen, multi-bounce glossy exactness | **D** on metal/floor |
| Refraction, transmission, caustics | Dispersion, nested IOR, true caustics (with MNEE/photon caveats) [S1] | Refraction via screen-space; no caustics | `MeshPhysicalMaterial.transmission`, `ior`, `thickness`, `dispersion` (renders a transmission pass of opaque scene; no transparent-through-transparent) [S9] | drei `MeshTransmissionMaterial` (extra FBO, 2-6 ms [P]); fake caustics via animated projected texture on the floor | Real caustics, thick nested glass, light focusing | **O** (D if scene is glass-led) |
| Area lights, soft shadows, contact hardening | Physically sized lights, exact penumbra that widens with distance | Area lights + virtual shadow maps with light-size soft shadows [S2] | `RectAreaLight` (no shadows, LTC shading, needs `RectAreaLightUniformsLib`, MeshStandard/Physical only) [S3]; PCF / PCFSoft / VSM shadow maps; shadows limited by map res | Big soft key = `RectAreaLight` + baked soft shadow/contact texture on the floor; PCSS shader patch (examples) for contact hardening (+2-4 ms [P]); drei `<AccumulativeShadows>` / `<SoftShadows>` accumulate jittered shadow renders for a baked-soft look (static) [P] | Real-time exact area-light shadows with correct penumbra | **O** |
| Ambient occlusion, contact shadows | Falls out of GI | SSAO / horizon scan [S2] | None built in | GTAO (three examples) or N8AO [S6] (1-3 ms half-res [P]); baked AO in texture (free); drei `ContactShadows` (1 render, ~0.5-1 ms [P]) | n/a, good approximation exists | **O** if missing, **S** if present |
| Subsurface scattering | Random-walk SSS [S1] | Screen-space SSS [S2] | None (no SSS in MeshPhysical) | Thickness-map trick / wrap lighting in `onBeforeCompile`; transmission+attenuation as a rough stand-in [P] | Accurate volume SSS | **S** for metal blades (irrelevant to gold) |
| Volumetrics, fog, god rays | Ray-marched volumes, scattering, shadows in fog [S1] | Froxel volumetrics [S2] | `Fog` / `FogExp2` (depth fog only) | Cheap: additive cone meshes + noise-textured billboards (fake rays), pmndrs `GodRaysEffect` (screen-space radial, ~1-2 ms [P]); ray-march quad (fullscreen shader, 2-8 ms [P]) | Lit shadowed volume with multiple scattering at full res | **O** when haze is visible in reference |
| Emission that lights the scene | Emissive surfaces are real lights (MIS) | Emission contributes via probes/GI | Emissive does **not** light neighbours | Pair each emissive with a real light or `RectAreaLight`; bake emissive bounce into lightmap; bloom for the glow look | Automatic emissive GI | **O** |
| Bloom / glare | Compositor Glare node (post, so same class as live) or physical lens flare | Bloom (post) | None native | pmndrs `BloomEffect` (mipmap blur, luminance threshold, ~0.5-1.5 ms [P]) or three `UnrealBloomPass`; selective bloom via layers or emissive > 1 with half-float [S4] | Physically accurate diffraction glare / star streaks (can be faked with a kernel) | **S** |
| Motion blur | Real shutter-integrated, per-object, rotation-correct [S1] | Post, camera + object velocity [S2] | None | Velocity-buffer blur (realism-effects / custom, 1-3 ms [P]); accumulation of N sub-frame renders (N× cost, perfect result, fine if scene is cheap); for a looping video, **pre-render frames** | Per-pixel exact blur of 1000s of instanced blades at 60 fps cheaply | **O** for fast spin, **S** for slow |
| Depth of field / bokeh | Real aperture, blades, bokeh shape, cat-eye [S1] | Post DoF [S2] | None | pmndrs `DepthOfFieldEffect` (1-3 ms [P]) or `BokehPass`; scatter-based bokeh costs more | Optical-accurate bokeh with highlights occlusion | **O** (strong "photographic" cue) |
| Anti-aliasing, sampling, noise | Many spp, stochastic, converges clean; film filter | TAA with sample accumulation; viewport samples [S2] | MSAA on WebGLRenderTarget (`samples`), FXAA/SMAA in post; canvas `antialias:true` | MSAA 4x on render target + SMAA; TAA (`TAARenderPass` in examples) with jitter, or **accumulate** jittered frames when the camera is still (free supersampling) [P]; render at DPR 2 | Sub-pixel stochastic converged AA on specular aliasing at motion | **S** if MSAA+TAA, **O** shimmer on thin blades otherwise |
| Denoising | OIDN / OptiX, makes 128 spp look clean [S1] | None needed | n/a | Not needed unless using `three-gpu-pathtracer` (it accumulates; no denoiser by default, check repo) [S5] | Live ML denoiser in-browser at 60 fps | n/a |
| Tone mapping / colour management | Filmic, AgX (default 4.x+), Khronos PBR Neutral, scene-referred linear then view transform [S8] | Same view transforms | `ACESFilmic`, `AgX`, `Neutral` (Khronos PBR Neutral), `Reinhard`, `Cineon`, `Linear`; `renderer.toneMapping` [S3,S7] | Pick **AgX** to match Blender 4/5 defaults; exposure matched; or Neutral for colour fidelity. Tone mapping happens only in the final output pass, so with post stacks use `ToneMappingEffect` last [S4] | Perfect parity (AgX variants differ in look/looks) | **D** (gold hue and highlight rolloff) |
| Texture res, anisotropic filtering, micro-detail, normal-map limits | 8K+ textures, true displaced micro-geometry | Same GPU limits as three, plus displacement | `texture.anisotropy` up to `renderer.capabilities.getMaxAnisotropy()` (typ. 16); mipmaps; normal map | KTX2/Basis for VRAM; tile + detail normal; roughness-variation map; 4K textures cost 64 MB RGBA uncompressed [V] | 100M-poly detail; per-pixel micro-glints (sparkle) faithfully | **O** on brushed/hammered gold |
| Anisotropic / brushed metal | Anisotropic GGX with tangent control [S1] | Same | `MeshPhysicalMaterial.anisotropy`, `anisotropyRotation`, `anisotropyMap` (needs tangents / UVs) [S9] | Native; quality good with PMREM IBL but stretched highlights depend on env detail | Anisotropy in multi-bounce reflections | **O** |
| Clearcoat / sheen / iridescence | Principled BSDF: coat, sheen, thin-film [S1] | Principled | `clearcoat`, `clearcoatRoughness`, `sheen`, `iridescence` (+ thickness range) [S9] | Native and cheap; clearcoat second specular lobe doesn't see GI | Layered BSDF energy conservation across lobes | **S** |
| Displacement, geometry detail, poly budget | True displacement, adaptive subdivision, 10-100M tris [S1] | Bump/displacement, millions of tris on desktop | `displacementMap` needs dense mesh; draw calls; no tessellation | Bake detail into normal map; `InstancedMesh`, LOD, `BatchedMesh`; budget ~1-3M visible tris desktop, ~200-500k mobile [P/U]; WebGPU compute helps culling [S3] | Micro-displacement everywhere; adaptive tessellation | **O** at silhouettes, **S** otherwise |
| Shadows (resolution, acne) | Exact, no maps | Virtual shadow maps, near-pixel-accurate [S2] | Shadow maps: `mapSize`, `bias`, `normalBias`, `radius`, `blurSamples` (VSM) [S3] | `normalBias` 0.02-0.05 kills acne; cascades by hand (CSM addon in examples); tight orthographic frustum fitted to subject; bake static shadows [S3,P] | Virtual-shadow-map quality across huge scenes | **O** (acne/peter-panning read as "CG") |
| HDR range/precision on web | Float32 scene-referred, unlimited | Float | `HalfFloatType` render targets (WebGL2 `EXT_color_buffer_float`/`_half_float` widely available) [S11]; default canvas output is 8-bit sRGB (banding in dark gradients) | pmndrs `EffectComposer` defaults to half-float frame buffers; add subtle **dither/noise** pass to kill banding; UltraHDR/`rgba16float` canvas via WebGPU `colorSpace display-p3`/`toneMapping: extended` where supported (check r186) [S11,U] | HDR displays via standard WebGL canvas; true >8-bit output on most browsers | **O** (banding in dark gradients) |
| Mobile GPU limits | n/a | n/a | tile-based GPUs, small fill-rate; WebGL2 only on older iOS; half-float render targets usually OK | Cap DPR at 1.5-2; drop SSR/DoF/god rays; ≤1 post pass; no MSAA on large RTs; bake everything; fixed fps budget 16.6 ms, mobile realistic 8-10 ms of work [P/U] | Full desktop stack on phones | **D** (it forces the ceiling down) |

---

## 2. Defining gaps, ranked by how much they dominate a photoreal look

Ranked for the failing case: polished gold blades in a dark studio, AI-generated and path-traced-looking.

1. **Inter-reflection and glossy reflection of the surroundings (D).** In path-traced polished metal, every blade carries a distorted picture of its neighbours, the floor, and the lights. three.js shows only one prefiltered env map. Result: blades look like uniformly shaded plastic-gold. The single biggest gap. *Fix class:* bake or per-ring CubeCamera, plus a purpose-built env map (see §3).
2. **Global illumination / indirect colour bleed (D).** Warm gold bounce on neighbours, dark values lifted by bounced light, no pure-black crush. three.js has none dynamically. *Fix class:* baked lightmaps, coloured fills, emissive cards in the env, AO baked.
3. **Light shape and softness of highlights (D).** Path tracing yields large soft area-light reflections with long specular streaks across curved metal. Point/spot lights give tiny hot dots. *Fix class:* put the lighting **in the environment** (a custom HDR / canvas-painted env with big softboxes and strip lights) so reflections show shaped light; `RectAreaLight` for diffuse fill.
4. **Tone mapping and highlight rolloff (D).** Gold hue shifts toward white or orange depending on view transform. The reference's smooth specular rolloff comes from a filmic/AgX transform on scene-referred values. *Fix class:* AgX (or Neutral), HDR highlights above 1.0, half-float targets, matched exposure. Cheap and high-yield; most often wrong by default.
5. **Contact shadows / AO / grounding (O).** Missing contact darkness makes objects float. *Fix class:* N8AO/GTAO + `ContactShadows` or baked.
6. **Optical camera artefacts: DoF, motion blur, bloom/glare, film grain (O).** The "shot on a camera" feel. All are post effects in both engines, so they are **achievable** at 1-6 ms combined. Absent = CG look; present but too even = fake.
7. **Micro-detail and sparkle (O).** Brushed grain, tiny scratches, specular glints. Needs high-res roughness/normal maps and anisotropy; ok within limits, but true glints under motion are not.
8. **Volumetric haze and light shafts (O).** If the reference has atmosphere, flat black backgrounds read as CG. Fake with sprites/cones or a screen-space pass.
9. **Anti-aliasing / shimmer (S to O).** Thin blade edges with high-contrast specular shimmer in motion without TAA.
10. **Banding in dark gradients (O on dark scenes).** 8-bit output + dark vignette = visible steps. Fix with dithering.

Subtle (S): SSS (irrelevant for metal), clearcoat/sheen details, denoising (no-op), most mobile concerns beyond the framerate.

---

## 3. What three.js genuinely can match

With budget ~6-10 ms of GPU on a mid laptop at 1080p-class:

- **Material model** for metals: `MeshPhysicalMaterial` with metalness 1, tuned roughness, anisotropy, clearcoat. Matches Principled for single-bounce IBL closely. [V S9, S10]
- **Studio-quality reflections of designed lighting**: a custom env (HDR or painted equirect / `RoomEnvironment` as a base, `PMREMGenerator`) containing big softboxes and strip lights. Convincing for static or slowly-rotating metal. [V S3]
- **Baked GI/AO/shadows from Blender** into lightmaps/AO maps/env for rigid content. This can approach Cycles stills for the baked part; it just cannot respond to changes. [P]
- **Filmic colour pipeline**: AgX / Khronos Neutral, half-float buffers, exposure, dithering. [V S3, S7]
- **Camera post stack**: bloom, DoF, vignette, grain, chromatic aberration, light motion blur, SMAA/TAA. [V S4]
- **Soft grounding**: contact shadows + GTAO/N8AO + soft shadow accumulation. [V/P S6]
- **Offline-quality still frames in-browser**: `three-gpu-pathtracer` for progressive convergence on a static camera (proof of reference look, not for scrolling animation). [V S5]
- **Looped motion with pre-rendered passes**: if the animation is deterministic (loop), render frames or layers offline (Blender/three-gpu-pathtracer) and play them as video/sprite, with live three.js only for parallax/interaction. This sidesteps nearly every gap above, at the price of file size and interactivity. [P]

## 4. What is essentially out of reach live (honest ceiling)

- Dynamic multi-bounce GI and exact mutual reflections between many moving polished objects at 60 fps.
- True caustics and thick nested glass.
- Physically exact area-light penumbrae on every object in motion.
- Per-pixel micro-geometry glints and 8K-plus detail.
- Full Cycles look on mobile GPUs.

**Rule for the skill's feasibility gate:** if the reference's look depends mainly on #1-#3 (polished metal + mutual reflections + soft area light) and the scene must be fully dynamic, the ceiling is "convincing-but-recognisably-real-time" unless baked or pre-rendered. State that up front and offer: (a) baked-hybrid, (b) pre-rendered video/frames, (c) accept the three.js ceiling.

---

## 5. Why AI-generated reference video looks "too real" for real-time (and is physically inconsistent)

Evidence here is mostly [P]/[U]: video models are not documented physically; this is observation of their output plus the structure of how they are trained (large corpora of photographs and renders, learned appearance priors rather than a light-transport simulation).

- **They learn photographic appearance, not light transport.** Highlights, bounce light and reflections are plausible *per frame* but need not obey one consistent light/geometry. A path tracer is globally consistent; the model only imitates. [P]
- **Implicit lens/film rendering baked in**: shallow DoF, bokeh, halation, grain, chromatic fringing, lens bloom, vignette, compression-friendly smoothness. These are post/optical effects; reproducible only as a stack of post passes (§3), so the gap is bigger than any single material. [P]
- **Inconsistent reflections**: a reflected shape may not match the real surroundings, or change shape between frames, or "morph" with time. A real-time engine would *correctly* show the wrong thing as wrong. The target is therefore **not a physically valid target**, so exact reproduction is impossible and only a stylistic match is achievable. [P]
- **Light-source ambiguity**: highlights and gradients appear without a locatable source, and the apparent lights can drift between frames. Matching needs an *authored* env/lights that produce the same look, not a measured setup. [P]
- **Geometry drift**: blade count, spacing, edge sharpness, and small details are not exactly regular; the loop may not close; pseudo-random micro variation reads as organic. A procedural, instanced scene reads as "too clean/regular" by comparison; add controlled imperfection (per-instance tilt, roughness, tiny scale variation). [P]
- **Temporal coherence tricks**: motion is smoothed/interpolated; motion blur and DoF vary by frame. Real-time is exact per frame, which looks stiffer. [P]
- **Exposure and tone mapping are implicit**: AI video has a strong baked-in grade (lifted blacks, rolled highlights, saturation curve). Replicate by matching *measured* values from the frames (histogram, black point, highlight rolloff) rather than by eye. [P]
- **Implication for the skill:** treat the reference as an art direction target. Measure (colour, contrast curve, bloom radius, DoF, grain), build an authored env + post stack to hit the measured numbers, and declare in advance that frame-exact physical correspondence is not a goal.

---

## 6. Practical notes for the skill

- Order of work that most efficiently closes the gap: (1) env map + tone mapping + exposure, (2) bake/AO/contact shadows, (3) per-ring reflection probe, (4) post stack (bloom, DoF, grain, dither), (5) micro-detail maps, (6) motion blur/TAA.
- Perf budget at 1080p, mid laptop (Apple M-series / GTX 1660 class) [P/U]: scene 3-6 ms + bloom 1 ms + AO 1-3 ms + DoF 1-3 ms + SMAA 0.5 ms + grain/dither 0.1 ms. SSR + volumetrics + motion blur together usually exceed 16.6 ms.
- Validate with a numeric comparison (luminance histogram, mean colour of highlights, SSIM on blurred versions) rather than critic prose, so "stuck" can be detected as "no metric improved in 2 iterations".
- Stop mechanism trigger: when remaining deltas map only to rows in §4, report the ceiling and ask for a direction.
