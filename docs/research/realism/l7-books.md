# L7 — Free books, course notes and lessons on real-time realism

Date: 2026-10-16. Grades: [V] primary/official text read this session, [P] practitioner, [U] unverified or recalled from memory (not re-fetched; check before the skill relies on it).
Fetched content treated as data. Only openly published material was used. Nothing paywalled was downloaded.

## 0. Access outcome

| Item | Result |
|---|---|
| Saved PDF | `sources/realism-books/frostbite-pbr/frostbite.pdf` (+ `.txt` extract, SOURCE.txt) — "Moving Frostbite to PBR" course notes, author-hosted (seblagarde.files.wordpress.com). No licence stated: reference only, do not republish. |
| Failed downloads | Karis "Real Shading in UE4" PDF came back corrupt/truncated (twice); Activision GTAO PDF timed out; Heitz LTC PDF URL returned HTML. Nothing saved for these; their claims below are [U] unless the web page was read. Retry from the URLs in section 1. |
| Not fetched | Three.js Journey paid body, any paywalled course. Only the public free-lesson list was read. |
| Web books | Read via WebFetch summaries only (no excerpt files saved). The summaries are paraphrase, not quotes. |

## 1. Reading map

| Resource | Access | Licence / terms | What it gives a web-3D agent | Grade |
|---|---|---|---|---|
| Filament "Physically Based Rendering" doc — https://google.github.io/filament/Filament.md.html | Free web | Open-source project docs (licence not stated on page; repo is Apache-2.0 [U]) | Best single compact reference for what a real-time PBR engine approximates and what it drops. Split-sum limits, multiscatter compensation, clear coat, specular and horizon occlusion, cloth/anisotropy shortcuts. Area-light, SSS and translucency sections are marked [TODO] in the text read. | [V] |
| "Moving Frostbite to PBR" (Lagarde, de Rousiers) — https://seblagarde.files.wordpress.com/2015/07/course_notes_moving_frostbite_to_pbr_v32.pdf | Free author-hosted PDF (saved) | None stated | Production-grade list of reflection sources (distant probe, local probe with parallax proxy, SSR, planar) with failure notes. Area lights by representative point and capsule/sphere splitting, specular occlusion (4.10.2), energy-renormalised Disney diffuse, validation of approximations against a path tracer (Mitsuba). | [V] |
| LearnOpenGL, PBR/IBL chapters — https://learnopengl.com/PBR/IBL/Specular-IBL ; PDF https://learnopengl.com/book/book_pdf.pdf | Free web + free PDF listed on realtimerendering.com | Not stated on page (site is CC BY-NC 4.0 per my memory [U]) | Step-by-step split-sum: prefiltered env map, BRDF LUT, and the artifacts it states (no grazing reflections, cubemap seams, bright dots, low base resolution, 5 mips). | [V] |
| pbr-book.org (Physically Based Rendering 3rd and 4th ed.) — https://www.pbr-book.org/ | Free web | "freely available online", © Pharr/Jakob/Humphreys; no open licence on page | The offline ground truth: what a path tracer computes (light transport, volumes, BSSRDF, MIS). Use it to define what the real-time version is approximating. Not a real-time source. | [V] |
| Real-Time Rendering 4th ed. site — http://www.realtimerendering.com/ | Free chapters 25 (collision), 26 (real-time ray tracing) and appendices only; main book paid | Free parts online; book paid | Index of free books (below). Ch. 26 covers hybrid ray tracing, which is the offline-vs-real-time bridge. Rest of the book is paywalled: not mined. | [V] |
| GPU Gems 1–3 — https://developer.nvidia.com/gpugems/ | Free online | NVIDIA site, no further terms on page | GPU Gems 3 Part II: summed-area VSM, parallel-split shadow maps, "High-Quality Ambient Occlusion" (ch. 12), "Volumetric Light Scattering as a Post-Process" (ch. 13). Old (2007) but still the origin of many web shadow/AO/god-ray tricks. | [V] part list |
| Ray Tracing Gems I/II — http://raytracinggems.com | Free PDFs | Open access per realtimerendering.com ("download for free") | Denoising, hybrid RT, AO/shadow RT. Relevance to three.js: only for explaining what WebGL cannot do (no hardware RT). | [V] listing only |
| Discover three.js — https://discoverthreejs.com/book/ | Free web ("completely free") | No licence stated on page | Ch. 1.4 "Physically Based Rendering and Lighting", 1.10 "Ambient Lighting". No chapter on colour management, tone mapping, shadows or post (not listed). Beginner level; low realism-ceiling value. | [V] TOC |
| Three.js Journey — https://threejs-journey.com/ | First lessons free; every lesson's opening is a free "preview" | Paid course; free part as published | Public TOC includes "25 Realistic render", "50 Baking and exporting the scene" (Portal Scene) and 18 shader lessons incl. "Lights Shading". Only the previews are accessible; body is paywalled. Record title and link only. | [V] TOC |
| Heitz et al., LTC area lights (SIGGRAPH 2016) — https://eheitzresearch.wordpress.com/415-2/ | Free paper page, demos | Code licence not stated | Closed-form polygon-light shading with GGX via a fitted linear transform of a cosine lobe. Three.js ships a port as `RectAreaLight` (see table). | [V] page |
| Karis, "Real Shading in UE4" (SIGGRAPH 2013) — https://blog.selfshadow.com/publications/s2013-shading-course/karis/ | Free | Download failed this session | Origin of split-sum and representative-point lights. Claims below rely on the LearnOpenGL/Filament derivations instead. | [U] |
| Jimenez et al., GTAO "Practical Real-Time Strategies for Accurate Indirect Occlusion" (Activision, 2016) | Free author/company-hosted PDF | Download failed | Origin of GTAO and the multi-bounce albedo fit. Formula in section 3 is from memory. | [U] |
| WebGL2 Fundamentals / WebGPU Fundamentals, Blender Manual, Khronos glTF `KHR_materials_*`, Inigo Quilez articles, Morgan McGuire notes, SIGGRAPH Physically Based Shading course | Free | Not visited this session | Candidates for follow-up. The Blender manual and glTF specs are for the Cycles/EEVEE-vs-three comparison and extension coverage, which L1/L2 own. | not read |

## 2. Approximations and their failure modes

"Ceiling" = what the artifact looks like when the approximation breaks, and so the realism a three.js scene cannot exceed without changing technique.

| Effect | Real-time technique | Where it breaks visually (the ceiling) | Source |
|---|---|---|---|
| Specular image-based lighting | Split-sum: prefiltered env map (mips by roughness) times a 2D BRDF LUT (scale and bias on F0) | Assumes V = R = N, so grazing-angle stretched reflections are lost; the Frostbite text says the approximation "can be quite noticeable on flat" surfaces. Cubemap seams at high roughness; bright dots from HDR hot spots; low base resolution (128 per face in the tutorial) for very smooth detailed reflections; only 5 roughness mips. | LearnOpenGL [V]; Frostbite 4.9 [V]; Filament [V] |
| Roughness blur | Roughness stored in discrete mips, trilinear blended | At roughness near 0.06 the blur is a visible cross-fade between mips, not a true blur. Mips are pre-filtered, so minified low-roughness surfaces alias or moiré. | Filament [V] |
| Reflection parallax | Distant probe (infinite environment) | Every point uses the same direction; floors and interiors look "floating" in the room. | Filament [V]; Frostbite [V] |
| Local reflections | Box/sphere-proxy corrected local probes | Parallax and object lighting not perfectly captured; correcting direction against a probe pre-convolved from its centre creates sharp discontinuities at high roughness, so Frostbite lerps back to the uncorrected direction by roughness. | Frostbite 4.9 [V] |
| Screen-space reflections | Ray-march the depth buffer against the lit frame | Covers only what is on screen (short to medium range). Falls back to probes when the ray fails, and the two must be matched by roughness or the transition shows. Frostbite calls SSR one of its most accurate sources, but it still needs the probe fallback. | Frostbite 4.9.4 [V] |
| Planar reflection | Re-render scene mirrored | Valid only for a flat plane (roads, water). | Frostbite [V] |
| Diffuse indirect | 2 to 3 spherical-harmonic bands, or irradiance map | Low frequency only; no coloured bounce from nearby surfaces unless baked; no contact bleeding. | Filament [V] (SH bands); bounce claim [P] |
| Energy loss at high roughness (multiscatter) | Add a scaled lobe: `1 + f0 * (1/dfg.y - 1)` (Lagarde/Golubev variant of Kulla-Conty) | Without it, rough metals go too dark. The compensation is an approximation to multiple scattering and cannot be combined with the analytic Karis14/Narkowicz14 DFG fits. | Filament [V] |
| Diffuse model | Lambert, or Disney diffuse renormalised for energy | Disney diffuse is not energy conserving unless renormalised (Frostbite blends bias 0 to 0.5 and factor 1 to 1/1.51 by roughness). Lambert ignores the retro-reflective roughness effect. | Frostbite 3.1 [V] |
| Clear coat | Second isotropic GGX lobe, Kelemen visibility, F0 0.04, base attenuated by (1 - Fc) | No inter-reflection or refraction between layers; base roughness not adjusted under the coat; second lobe oriented along view for IBL. Coated-gold look is a plausible but cheap stand-in for a real layered BSDF. | Filament [V] |
| Anisotropy | Bent reflection vector for IBL | "A rough approximation of anisotropic lighting" in IBL. Brushed-metal streaks under env light are less correct than under analytic lights. | Filament [V] |
| Cloth, sheen | Separate BRDF term in LUT channel, but standard IBLs reused | Filament says per-BRDF IBLs are "not practical", so cloth reflections are not accurate. | Filament [V] |
| Area lights | Representative point (Karis/Drobot); LTC for polygons; capsule split into rectangle plus two sphere ends | Representative point is valid for small solid angles; Frostbite found no correct energy-conserving factor for the disk sun light. LTC is a fitted approximation of GGX and (from the page read) the technique gives no shadows by itself [U: not stated on page]. Rectangle lights give no occlusion, so light passes through geometry unless shadowed separately. | Frostbite 4.7 [V]; Heitz page [V]; shadows [U] |
| Ambient occlusion (diffuse) | Baked AO, SSAO, GTAO | Filament: McGuire's AO form is exact only for constant ambient light and Lambertian; applies to indirect only. Screen-space variants miss off-screen and back-facing occluders (thin objects, halos at depth edges) [P/U]. | Filament [V]; screen-space limits [U] |
| Multi-bounce AO | GTAO fit: with a = 2.0404*albedo - 0.3324, b = -4.7951*albedo + 0.6417, c = 2.7552*albedo + 0.6903, result = max(x, ((x*a + b)*x + c)*x) | Brightens AO on light surfaces so creases do not go too dark. Empirical per-albedo fit, not a transport solution. Gold (high albedo) is where wrong AO shows most. | Jimenez 2016 — from memory [U] |
| Specular occlusion | Lagarde empirical formula from diffuse AO, NdotV and roughness | Filament: "no physical basis"; returns diffuse AO for rough surfaces. Values under 2% reflectance treated as baked occlusion. Frostbite 4.10.2 has its own treatment. | Filament [V]; Frostbite [V] |
| Horizon occlusion | Darken reflections that point below the geometric surface: `min(1 + dot(r, n), 1)^2` (normal-mapped surfaces) | Only fixes normal-map artifacts; optional for cost. Does not model real shadowing of the reflection. | Filament [V] |
| Micro-occlusion | Ignored in Filament; stored in f0 low range in Frostbite | Dark crevices on dielectric surfaces look too bright under IBL. | Filament [V]; Frostbite [V] |
| Shadows | Shadow maps; GPU Gems 3: parallel-split maps, variance maps | Resolution and bias trade-offs; no contact hardening without PCSS-like tricks [U]. Volumetric light: GPU Gems 3 ch. 13 is a screen-space post-process, so it needs the light on screen and fakes depth. | GPU Gems 3 TOC [V]; limits [U] |
| Subsurface scattering | Wrapped diffuse, screen-space blur, thickness hacks | Filament's subsurface and translucency sections were [TODO] in the text read; its only SSS-like shortcut is cloth wrap diffuse (w = 0.5), "not physically based". No claim from the books read on skin-grade SSS; do not promise it from this lane. | Filament [V] |
| Refraction, glass | Not covered in the excerpt read | Unverified here. See L2 for the three.js `transmission` path. | [U] |
| Global illumination | Baked lightmaps, probes, cubemap capture | No dynamic multi-bounce. Frostbite's own validation workflow uses a path tracer as the reference for every approximation. | Frostbite 2.2 [V] |
| Offline vs real time, the overall frame | Path tracing converges to ground truth; real time adds each effect separately | Each row above is one unmodelled interaction. Realism "ceiling" is the sum, and it shows most where several matter at once: polished metal reflecting nearby bright geometry, contact shadows, coloured bounce. | pbr-book.org [V] as definition; synthesis [P] |

### What the books say about the shape of the ceiling

1. The engineers of production engines state their approximations openly and validate against a path tracer (Frostbite 2.2). A three.js agent that has no reference render cannot know which gap is a bug and which is a ceiling. A reference path-traced render (Cycles) is the only honest measuring stick [synthesis].
2. Three recurring limits are named in the sources: lost view-dependent reflection shape (split-sum), no parallax and no off-screen content (probes, SSR), and missing inter-layer and multi-bounce transport (clear coat, AO, GI).
3. Energy compensation and multi-bounce AO are cheap fixes and improve bright metals at no extra pass. Missing reflections of nearby geometry on gold is the biggest non-fixable gap without baking or planar tricks [synthesis from Frostbite 4.9].

## 3. Mapping to three.js (needs checking against r186 source)

These are my recollection, not read this session. L2 owns the verified toolbox; do not cite from here without confirming [U].

| Real-time technique | three.js counterpart [U] |
|---|---|
| Split-sum IBL | `PMREMGenerator` prefilter plus `envMap` on standard/physical materials |
| Multiscatter GGX | Included in the physical material's BRDF code path; verify in `lights_physical_pars_fragment` |
| LTC area lights | `RectAreaLight` with `RectAreaLightUniformsLib.init()`; no shadows; only works with standard/physical |
| Clear coat | `MeshPhysicalMaterial.clearcoat` and `clearcoatRoughness` |
| Anisotropy, sheen, iridescence, transmission | `MeshPhysicalMaterial` properties |
| AO | `aoMap` (baked), GTAO via the examples' postprocessing pass or pmndrs postprocessing |
| Local probe parallax | Not built in as a box-projected probe in the core material [U]; usually faked with a baked or custom shader |

## 4. Recipes

Each recipe is a practice taken from the sources; numbers come from the cited text.

1. **Pick the right reflection source per surface (Frostbite 4.9).** Distant probe for sky-like content; local probe plus proxy for rooms; SSR for contact reflections; planar for flat floors and water. State the failure mode of the chosen source in the brief so critics do not flag it as a defect.
2. **Never let the BRDF LUT be 8-bit if you can avoid it (Filament).** Precision loss shows as banding. Do not combine analytic DFG fits with multiscatter compensation.
3. **Add energy compensation to rough metals.** Use `1 + f0 * (1/dfg.y - 1)` on the specular lobe (Filament). If a rough gold looks dull compared with the Cycles reference, check this before changing the lights.
4. **Pre-integrate the environment at enough resolution.** LearnOpenGL's 128 px face and 5 mips are the floor; for mirror-like metals raise the base and mip count and fix seams and hot spots by clamping HDR highlights before prefiltering (dots come from high-frequency HDR). Clamping is my addition [P].
5. **Occlusion order.** Apply AO to indirect light only (Filament). For bright albedo use the multi-bounce fit so creases do not go black [U]. For reflections use a specular-occlusion term plus horizon occlusion when normal maps are present.
6. **Rectangular emitters.** Use LTC (or representative point) for visible strip/panel highlights. Add real shadowing separately, since the lighting term has no occlusion.
7. **Layered finishes.** For lacquered or coated metal, use clear coat with roughness not below about 0.089 (Filament clamp). Do not expect inter-reflection between layers.
8. **Validate against a reference.** Render the same scene in Cycles with the same HDRI and camera, then compare. Frostbite used Mitsuba for this reason (2.2). It tells the agent whether a difference is a ceiling or a bug.
9. **Bake what real time cannot do.** For static gold/steel geometry, bake AO and light into textures (Three.js Journey's "Baking and exporting the scene" lesson is the public pointer; body is paid) instead of relying on screen-space effects.
10. **Report the ceiling.** When the remaining gap matches a row in section 2 (grazing reflection shape, off-screen reflection, multi-bounce transport, layered BSDF), stop iterating and report it as such.

## 5. Gaps and follow-ups

- Karis, Jimenez (GTAO) and Heitz PDFs need a retry with a longer timeout. Until then their formulas are [U].
- Not read: Blender manual (Cycles vs EEVEE, baking, colour management), Khronos `KHR_materials_*`, Inigo Quilez, Morgan McGuire, WebGPU Fundamentals, Jorge Jimenez SSS slides, SSR limits beyond Frostbite.
- Filament doc was read in two 100k-character windows (to character 200000 of about 242000); the last ~42k characters were not read.
- Subsurface and refraction have no verified content from this lane.
