# L5 - Written practitioner case studies: how studios get realism in web 3D

Fetched 2026-10-16. Grades: [V] official/docs/source, [B] measured, [P] practitioner, [U] unverified.
Method: WebSearch + WebFetch (small-model summaries, paraphrase) + curl through the r.jina.ai reader (verbatim text; used where Codrops/discourse blocked WebFetch with 403). Excerpts: `docs/research/community-scan/sources/realism-written/<slug>/SOURCE.txt` (each marked verbatim vs summary).

## 0. Coverage and gaps (read first)

- **Honest headline:** the public written record contains very few studio-grade numeric lighting procedures. Studios publish asset/perf/compression numbers and shader tricks; they almost never publish bake samples, light rigs, env intensities or bloom thresholds. Those fields are marked "not published" below, not inferred.
- **Found with real procedure + numbers:** Andrew Woan (Codrops 2025, the best bake recipe), Windland (Codrops 2022), ZERO (Codrops 2026), Lusion studio-site (Awwwards), Lusion Oryzo BTS pt 2, Heckel caustics/refraction, drei docs, discourse maintainers' answers.
- **NOT found (treat any claim as [U]):** Active Theory (Medium blocked by the reader; search snippets only say they replaced three's material/lighting with custom shaders and planned PBR + spherical-harmonic GI [U]), Igloo (Abeto's Awwwards page has no baking/lighting/material detail), 14islands, Resn, Dogstudio, Unseen, Merci-Michel, Immersive Garden, Exo Ape. Lusion Oryzo BTS parts 4-7 ("WebGL/Three.js tricks") were not published at fetch time (blog index showed parts 1-3). Three.js Journey lesson bodies are paywalled (preview only). No Garrett Johnson blog post exists in search; only repo/forum. Maxime Heckel "On Shaping Light" URL could not be fetched.
- **Nothing found** that states a "when to stop polishing" rule for visual realism. Only time-boxing statements (section 3).

## 1. Procedures that recur across studios (ranked)

| # | Procedure | Sources stating it | Strength |
|---|---|---|---|
| 1 | **Static lighting is baked/pre-rendered offline; the live scene only adds cheap dynamics.** Cycles bake to textures (Woan, Windland, Journey), Redshift video + real-time overlay (Lusion), pre-rendered AO/normal/thickness maps + matcaps (Lusion), baked lighting textures crossfaded on a skinned mesh (ZERO), Houdini sims stored as textures (Lusion). maintainers: "a realtime engine like three.js generally needs baked lighting for that kind of look" (donmccurdy) | 7 | Strongest |
| 2 | **Environment map is the single biggest runtime-realism lever for metal/glass; metal without one renders dark/plastic.** drcmda: envmaps "the single most important step for runtime realism w/o baking or path tracing"; Mugen87 "Blender shows reflections which is not yet true for your app"; Park: transmission "dull" until env added; multiple threads: missing `EquirectangularReflectionMapping`/PMREM = black metal | 6 | Strongest |
| 3 | **Fake the expensive light interaction with a purpose-built cheat, not physics**: caustics from area-ratio of refracted normals (Heckel: "absolutely going to cheat our way through this"), accumulated soft shadows (drei), planar projected reflector, matcaps for translucency (Lusion), per-channel IOR for dispersion | 5 | Strong |
| 4 | **Do the work in the DCC where it is cheap, ship the result as data**: sims -> vertex-animation textures (Lusion cloth 983 KB; Houdini VAT), splats for props/reflections only (Oryzo), volume VDB -> custom exporter (Igloo) | 5 | Strong |
| 5 | **Tune look live with GUI sliders in-browser against the reference; Blender's render "is not always great in three.js with default parameters"**: Windland "impossible to get the colors and intensities right by guessing the numbers" (dat.GUI); Igloo custom live-edit tools; ZERO KTX2 previewer | 4 | Strong |
| 6 | **Colour-management correctness first** (sRGB colour textures, linear data textures, renderer output sRGB, one tone map at the end). drcmda: wrong encoding = "cheap CGI look"; McCurdy: gamma workflow gives "fake plasticky CGI look" | 4 | Strong, but only fixes the base |
| 7 | **Texel-density economics: spend texture on what the camera sees** (Oryzo centre 50% = 90% of detail; Woan: sacrifice quality where the eye isn't, bake 4K then downscale, big-feature materials to avoid repeat detail; ZERO per-asset ETC1S, 256^2 upload tiles) | 4 | Strong |
| 8 | **Post stack is small and ordered; tone mapping once; text after tone mapping** (ZERO: render, bg, glass refraction, frost, DoF, grain+ONE tone map, deferred text, shatter). Windland: BokehPass day / UnrealBloom night, swapped via insertPass/removePass | 3 | Medium |
| 9 | **Adaptive quality tiering + real-device profiling** (ZERO avgMs>22 downgrade / <12 upgrade, cooldown; Windland FPS probe at load; Bruno mobile preset) | 3 | Medium |
| 10 | **Hybrid when pure approaches fail**: splat + mesh (Oryzo), video + real-time light (Lusion), baked + live transmission | 3 | Medium |

## 2. Per-source cards

Format: studio/author - URL - date - technique - procedure - numbers - baked vs live / faked - grade.

### 2.1 Andrew Woan, "Building a Fully-Featured 3D World in the Browser with Blender and Three.js" (Codrops)
- https://tympanus.net/codrops/2025/04/08/3d-world-in-the-browser-with-blender-and-three-js/ - 2025-04-08 - verbatim in `codrops-world-blender-threejs/`
- **Technique:** full-scene Cycles bake in Blender, shipped as KTX2 texture sets on GLB.
- **Procedure (his, numbered):** (1) author in Cycles *rendered* view with Sky Texture then a PolyHaven HDRI (strength 0.4); add variation (dirt, wear, crooked) because plain materials "give sort of a CGI vibe"; (2) delete every face the camera never sees (1920x1080 camera + fly mode check); check Face Orientation (all visible = blue); (3) join static objects with same UV map before bake; split the scene into multiple textures ("otherwise it'll get super blurry"); (4) SimpleBake add-on: Cycles, Bake Type **Combined**, Denoise via Compositor, colour space Linear Rec.709, **4096x4096**, 32-bit float, export **OpenEXR**; (5) second UV map "SimpleBake", Smart UV Project + UVPackMaster to pack; slicing seams on long meshes; (6) convert EXR -> PNG in compositor; (7) `gltf-transform etc1s in.glb out.glb --quality 255` (lowest tried 155); WebP vs KTX2 trial-and-error; Draco via gltf.report; (8) env background: HDRI -> cubemap, exposure matched by hand (Figma).
- **Numbers:** bake 4K then reduce ("harder to go up"); bird baked at 256x256 on animation frame 4 (wings spread); waterfall/background = transparent Blender renders on planes.
- **Gotchas:** "Make sure to disable denoise for the renderer if you have it on otherwise it'll cause black lines across the seams" (denoise via compositor instead); deleting torch bottom faces let the point light leak into the bake; monitor colour-temperature setting skewed warm bake; typical studio workflow is *not* to bake the whole scene (size/load), he did because the scene fits a small trade-off zone.
- **Baked vs live:** all lighting baked; fire/flame, fog, particles live. **Faked:** distant mountain/waterfall = flat renders.
- **Stop-polishing:** motto "It's not perfect, but it's cool"; lists his own flaws openly. **Grade [P], best procedural source found.**

### 2.2 Windland - Codrops case study
- https://tympanus.net/codrops/2022/04/25/case-study-windland-an-immersive-three-js-experience/ - 2022-04-25 - verbatim excerpt
- **Procedure:** model in Blender; world node **Nishita** sky for natural light; trees via Geometry Nodes (cast shadow = realism); bake shadows to **one 2048x2048 floor texture**; export GLB, Draco (1.2 MB model, "sometimes 7x smaller"); trees instanced with `MeshSurfaceSampler`; tree sway in vertex shader; EffectComposer: BokehPass (day), UnrealBloomPass (night), swap with insertPass/removePass; FPS probe at load switches effects off.
- **Numbers:** target >=30 fps, <2 MB (final 1.8 MB vs 2.8 MB for a 1080p render); 2 weeks.
- **Quote:** "The result of rendering in 3D is not always great for the experience in Three.js using the default parameters ... It is impossible to get the colors and intensities right by guessing the numbers" (use dat.GUI). **Baked vs live:** shadows baked, so no shadow map. **Grade [P].**

### 2.3 ZERO (BUNQ LABS) - Codrops
- https://tympanus.net/codrops/2026/07/17/zero-the-engineering-behind-a-defiant-interactive-narrative/ - 2026-07-17 - verbatim excerpt
- **Technique:** >1 GB Blender source (8K textures) -> <10 MB at 60 fps on a budget Android.
- **Procedure:** per-asset KTX2/ETC1S via in-house previewer (side-by-side), heavier compression where unseen, mipmaps off where unneeded; atlas 50+ images into ~12; decode via `createImageBitmap`, upload in `requestIdleCallback` with `renderer.initTexture` (>5 ms budget), split big atlases into 256^2 tiles one per frame; self-host Draco/KTX2 decoders (CDN slowdown broke all decoding); explicit `highp` (Adreno/Mali treat mediump as true fp16 -> banding).
- **Lighting:** "Real time lighting on a skinned mesh would have been too expensive, and the lighting needed to match the original artwork exactly. Instead, we baked the lighting into textures and blended between them" - two slots in one atlas, mix by uProgress, premultiply alpha to avoid dark halos.
- **Numbers:** 2048^2 texture ~16 MB VRAM regardless of file size; builds 35-40 MB -> <10 MB; single 157 ms worst frame; tier thresholds avgMs >22 down / <12 up; 4-month build, first month on asset formats.
- **Post chain:** 8 ordered passes, one tone map in the fg pass; text after tone map. **Grade [P].**

### 2.4 Lusion studio site - Awwwards (SOTM May, c.2019)
- https://awwwards.com/case-study-for-lusion-by-lusion-winner-of-site-of-the-month-may.html - WebFetch summary (paraphrase)
- **Techniques:** Houdini cloth pre-sim (4 push directions blended at runtime, 220 KB gzip); character cloth as vertex-animation PNGs (983 KB desktop / 246 KB mobile); Beethoven bust = pre-rendered normal+AO+thickness+2 diffuse-illumination sets + two matcaps (translucency with two states); big-screen scene = **Redshift video + real-time point light on cursor + analytic volumetric light + reflections**, simplified glTF (~150 KB), camera look-around ~1.72 degrees; binary frame counter in video read with `readPixels()` because `currentTime` is inaccurate; 11 keyframes over 66 frames, int16 with divider.
- **Faked (their words):** blended sims "do not look as perfect as a proper cloth simulation" but extra real-time distortion makes them "somewhat realistic". **Grade [P]; re-verify numbers on page.**

### 2.5 Lusion - Oryzo AI BTS part 2 (blog.lusion.co)
- https://blog.lusion.co/oryzo-bts-part-2-7-3d-design-and-motion-graphics - 2026-04-02 - summary
- **Technique:** Houdini + Redshift (GPU) for offline look; real-time scene is **splats for props and desk reflections only + textured meshes**; hybrid ~78,233 splats desktop / 44,683 mobile after a ~900k-splat full-scene test "still showing flaws in wood details and sketch lines".
- **Procedure notes:** splat training cameras: hemispherical/spherical placement beat re-using the scroll spline; Redshift cannot bake displacement/tessellation so they rendered ortho top+front passes without reflections and stitched in Photoshop; centre 50% of desk gets ~90% of texels; bark photogrammetry ~180 RAW images; seamless looping noise for cork; rigid-body sim settles background props.
- Light rig, intensities, shaders: not published. **Grade [P].**

### 2.6 Igloo Inc - Abeto (Awwwards)
- https://awwwards.com/igloo-inc-case-study.html - 2024-10-31 - summary
- Procedural ice via crystal-growth algorithm; VDB custom exporter + compression; intro rendered in-engine, not video; UI in WebGL (SDF offset scramble); custom live-edit tools; Houdini + Blender, three.js, three-mesh-bvh. **No baking, lighting, materials, or post details.** Quote: "Iterating directly in the browser ... often leading to better results." **Grade [P], thin for realism.**

### 2.7 Bruno Simon - folio-2025 (Awwwards) + Three.js Journey lesson 50
- https://www.awwwards.com/brunos-portfolio-case-study.html (verbatim) ; https://www.threejs-journey.com/lessons/baking-and-exporting-the-scene (preview only)
- Folio: stylised, not realism. Useful: Blender preview made to match final ("I added grass, tiles, dirt, and water"); palette texture for colour; ETC1S/UASTC textures; Draco quantization; mobile preset disables water blur + DoF and cuts shadow-map size; "Most of the time, performance is the real constraint on creativity"; deadline set to stop endless polish.
- Journey bake recipe (preview): delete hidden faces -> Make Single User -> face orientation check -> apply scale -> UV -> bake; Blender 4: Bake View From = Active Camera, Margin Type = Extend; default colour management AgX. **No sample counts/texture sizes public.** Grade [P].

### 2.8 Maxime Heckel - caustics + refraction/dispersion
- https://blog.maximeheckel.com/posts/caustics-in-webgl (2024-01, summary) ; /refraction-dispersion-and-other-shader-light-effects/ (verbatim)
- **Caustics procedure:** (1) back-face normals of glass into 2000x2000 FBO from light camera; (2) fullscreen pass `refract(lightDir, n, 1/1.25)`, intensity = lightArea/newLightArea (dFdx/dFdy), `clamp` then square; (3) project onto ground plane, 16-sample chromatic blur, plane scaled from projected bbox x1.75.
- **Refraction/dispersion procedure:** render scene minus mesh to FBO, sample with `refract(eye, n, 1/ior)`, separate IOR per RGB channel, extra samples to smooth. IOR: water 1.333, diamond 2.42.
- **Cost:** two 2000^2 FBOs + full mesh re-render per frame + 48 taps/fragment; no fps given; recommends drei `Caustics` for production. **Fake:** fixed ratio 1/1.25, light = a direction. **Grade [P].**

### 2.9 pmndrs/drei docs (accumulative shadows, env, transmission, reflector)
- https://drei.docs.pmnd.rs/ (staging/accumulative-shadows, staging/environment, shaders/mesh-transmission-material, shaders/mesh-reflector-material) - fetched 2026-10-16 - verbatim [V]
- AccumulativeShadows: planar Y-up catcher, "zero performance impact after all frames have accumulated", defaults frames 40, resolution 1024, alphaTest 0.65, colorBlend 2; pair with `RandomizedLight` (example `amount={8}`, frames 100 temporal). Environment: live env via children cube camera `resolution={256}`, `frames={Infinity}` "little cost"; `ground` projection; gainmap formats smallest. MeshTransmissionMaterial: extra scene pass; "tiny resolution, for instance 32x32 ... will still look good"; defaults chromaticAberration 0.03, anisotropicBlur 0.1. MeshReflectorMaterial: `resolution={256}` default-ish low; blur/mixBlur by roughness. **Grade [V].**

### 2.10 Codrops glass tutorials (Park 2025; Milligan 2021)
- https://tympanus.net/codrops/?p=89382 (2025-03-13) ; /2021/10/27/creating-the-effect-of-transparent-glass-and-plastic-in-three-js/ - verbatim
- Park: MTM default samples **10**, resolution 128-256 acceptable (pixelated look), roughness 1.0 = invisible, IOR 1.07-1.5 animated, "Performance ... is not cheap": a separate scene render per transmissive object. Milligan: `MeshPhysicalMaterial` transmission r129+; "aiming for convincing and visually pleasing results, even if they are not scientifically accurate"; `thickness` is the magic. Both: transmission looks dull until an env map supplies something to refract/reflect. **Grade [P].**

### 2.11 discourse.threejs.org maintainer answers
- 71155 (drcmda 2024-09-30), 28106 (2021-07-17), 47976 (2023-02-13), 25617 (2021, summary), 20550 (2020-11-09), 3832 (gold ring, 2018), 41852 (metal dark, 2022)
- **drcmda's ladder (verbatim list):** path tracing "looks real, takes a long time, better for still images"; baking "looks fairly real, no runtime cost, but the scene is static"; SSGI "semi real, ... can be somewhat glitchy"; envmaps "the single most important step ... w/o baking or path tracing"; accumulative shadows "real looking shadows is half the rent"; PCSS "less real than acc-shadows ... more realistic than default shadows, some expense"; AO via pmndrs/postprocessing "improves realism greatly".
- **donmccurdy:** "You've loaded a 3D scene, not lighting or a rendering engine." Bake AO as a first step, or use three-gpu-pathtracer "just understand the framerates will not be 60 FPS". Cycles vs rasterizer: extra work = "choosing lighting carefully, baking lights or shadows".
- **Gold/metal specifics:** use MeshStandardMaterial for pure metal (no clearcoat) (Mugen87 2018); needs real cube/HDR env (not one texture on all faces); metal needs `mapping = EquirectangularReflectionMapping` (mjurczyk 2022); lightmap has no effect when metalness == 1 (works at any other value) because metal has no diffuse term to modulate (20550); "metalness and roughness visuals cannot really be baked" -> bake albedo/roughness/metalness maps instead; `envMapIntensity` 0.7 recurs, one user needed 5 to match a viewer (scene-dependent).
- **Tone map divergence:** ACES burns highlights/crushes shadows vs Blender Filmic; AgX flatter/less saturated than ACES (drcmda: "every color then becomes a tone of gray"); no Blender "Looks" in three; remedies: LUT or custom post pass (donmccurdy), pmndrs/postprocessing AgX CDL PR. **Grade [P] with maintainer authority.**

## 3. What was faked, what was impossible live, and workarounds

| Gap (stated) | Workaround stated | Source |
|---|---|---|
| Path-traced global light / soft contact shadows | bake to texture (4K Combined, EXR) or accumulate shadows over N frames | Woan, drei |
| Skinned/animated mesh lighting | bake lighting textures per keyframe, crossfade, premultiply alpha | ZERO |
| Accurate caustics | 3-pass normal-area-ratio cheat on a ground quad | Heckel |
| Translucency/SSS on a hero object | pre-render thickness/AO/diffuse sets + matcaps | Lusion |
| Offline-render quality of whole scene | ship offline video, add live light + camera nudge, sync via encoded frame counter | Lusion |
| Photoscan-like detail | Gaussian splats limited to props/reflections, meshes elsewhere (full-scene splat showed flaws) | Lusion Oryzo |
| Displacement can't bake in Redshift | ortho top+front passes without reflections, stitched | Lusion Oryzo |
| Metal lightmap | env-lit PBR for metal; bake only diffuse parts; separate metalness/roughness maps | discourse |
| Blender tone curve | custom tone map / LUT; accept divergence | discourse |
| Distant scenery | flat renders on planes | Woan |
| Performance on mobile | tier manager, FPS probe, lower pixel ratio during costly effects | ZERO, Windland, Bruno |

**Performance budgets stated:** Windland <2 MB, >=30 fps; ZERO <10 MB, 60 fps, frame budget avgMs 12-22; Lusion cloth 246 KB mobile; MTM resolution 32-256; env cube cam 256; AccumulativeShadows 1024. **When to stop:** only time-boxing: Bruno "release goal for the end of 2025"; 84-24 "Better done than perfect" (Codrops 2024-04-08, deadline = product anniversary); Woan "not perfect, but cool". No source gives a visual-plateau test.

## 4. "Blender look -> three.js look" checklist (distilled; each line cites section 2)

1. **Decide per element: bake, live, or fake** before building (section 1 #1). Static diffuse/AO/shadow = bake; metal/glass = live PBR + env; sims = textures; translucency = matcap/thickness maps.
2. **Colour management:** colour textures sRGB, data textures linear, renderer output sRGB, one tone map at the end. Blender 4 default is AgX; set three's tone map deliberately and expect ACES to burn highlights vs Filmic/AgX (2.7, 2.11).
3. **Metal/glass: give it an environment.** PMREM-prefiltered HDR/EXR (`EquirectangularReflectionMapping`); envMapIntensity is scene-specific (0.7 is a folklore start, not a rule); use the same HDRI and rotation as Blender; add Lightformers/area-style cards for studio gold look [drei Environment children, 2.9]. Pure metals: MeshStandardMaterial, no clearcoat (2.11).
4. **Do not expect a lightmap to light metal** (metalness 1 ignores it). Bake diffuse parts; keep metal live.
5. **Bake recipe (Woan):** delete unseen faces; apply scale; fix normals; join per UV; second UV pack (UVPackMaster/Smart UV + slicing seams); Cycles Combined 4K, 32-bit, EXR, denoise in compositor not in the bake (seam lines); disable ambient leaks (cap light bottoms); EXR->PNG->KTX2 ETC1S (quality ~155-255 tested); Draco.
6. **Margin/camera settings (Blender 4+):** Bake View From = Active Camera, Margin Type = Extend (Journey).
7. **Soft shadows without baking:** AccumulativeShadows + RandomizedLight (frames ~40-100, res 1024), then freeze; AO via pmndrs/postprocessing.
8. **Glass:** MeshPhysicalMaterial transmission (thickness is the lever) or drei MTM at reduced resolution/samples; one transmissive object = one extra scene pass; add dispersion per-channel IOR only for hero object.
9. **Tune against the reference with GUI sliders** (light colours/intensities, exposure, env intensity), not by guessing; keep a paired screenshot (2.2).
10. **Look variation in materials:** Woan: clean PBR reads "CGI"; add dirt/wear/crooked variation in the bake.
11. **Spend texels where the camera looks** and verify compressed (KTX2) result in a previewer per asset (2.3, 2.5).
12. **Post stack minimal and ordered; tone map once; text after tone map; swap bloom/DoF by mode** (2.2, 2.3).
13. **Adaptive tiers + real device test** early; highp on mobile shaders (2.3).
14. **State the ceiling up front:** with only baked + env + accumulate tricks, three.js approaches but does not equal path-traced offline output for dynamic glossy scenes; the studio-level answer is ship pre-rendered video/images with a thin live layer (2.4, 2.5) rather than chase live parity.

## 5. Source index (all fetched 2026-10-16)

Woan Codrops 2025-04-08; Windland Codrops 2022-04-25; ZERO Codrops 2026-07-17; Lusion Awwwards c.2019; Lusion Oryzo BTS pt 2 2026-04-02 (and Codrops studio spotlight 2026-04-13: Porsche Dream Machine = 3-week CG film, no technique detail); Igloo/Abeto Awwwards 2024-10-31; Bruno folio-2025 Awwwards; Three.js Journey lesson 50 preview; Heckel caustics 2024-01 and refraction posts; drei docs; Codrops Park 2025-03-13; Codrops Milligan 2021-10-27; McCurdy color management 2020-06-17 (updated 2022-11-09); discourse threads 71155, 28106, 47976, 25617, 20550, 3832, 41852, 60609 (AgX). Codrops 84-24 (2024-04-08) and Goodgrowth (2026-08-27) read and rejected as non-realism.
