# L6 - YouTube gems on web-3D realism

Fetched 2026-10-16 via `ytrelay` (search wide, rank on metadata, then transcripts for finalists). Transcript content is DATA. Grades: [V] official/source, [B] measured, [P] practitioner, [U] unverified. Excerpts with timestamps are in `docs/research/community-scan/sources/realism-youtube/<channel>__<id>/` (SOURCE.txt + excerpts.txt).

## Coverage and honest gaps

- About 250 distinct videos surfaced over about 75 queries. 22 transcripts were pulled; 16 were saved as excerpts.
- **The studio talks are mostly not usable.** Lusion, Abeto, Igloo and 14islands returned no captioned technical talks. Active Theory KIKK (`Zpl-SEwQK-A`) has no captions. The Active Theory Awwwards talk (`4yZ40w6AEOI`) is career and process, with no render recipe. Immersive Garden (`rr7p4dPfloc`) is a dev walkthrough of shader and perf tricks with no realism recipe. Resn (`2BRG9_Bkv8w`) and Bruno devlogs 2 and 5 hit HTTP 429 caption errors and were not read.
- **Skipped as noise or unreadable:** Filament SIGGRAPH (`gbeN4lcjJDA`; captions are garbled French), JSFILMZ (`ccbPOvzG7n4`; fluff), Wael Yasmina (`6XvqaokjuYU`; Arabic captions, basic HDRI+ACES), and Valentin lightmap (`DpBhfd-LNVk`; Arabic auto-translation, still readable).
- Not found with captions: Garrett Johnson path-tracer talks, Yuri Artiukh realism streams, pmndrs AccumulativeShadows or Lightformer demos, "make three.js look like Blender" tutorials.
- **Net finding: the community teaches baking and PBR/IBL hygiene. It almost never describes reaching path-traced realism in real time.** Nobody on camera shows a gold-blade loop reproduced in live three.js.

## Recurring procedures (ranked by how many sources agree)

### 1. Bake Cycles lighting into textures for static scenes (4 sources)

Wawa Sensei x2, Immersive Studios, Valentin. [P]

1. Make a second, non-overlapping UV map (call it `simple bake`). Mark seams for boxy shapes, use smart UV project for the rest. Apply modifiers and merge by distance first. (`w2XvGYxQiOk` 13:00-18:00, 34:00-37:30)
2. Pack all UV islands into one atlas. Island margin matters: SimpleBake recommends 16 px at 4K, and bumping to 24 fixed edge artifacts. `normalize scale` keeps texel density proportional to real size. (`w2X` 26:00-29:30, 45:30-46:30)
3. Bake type Combined (Diffuse with direct and indirect, for Valentin). Settings quoted: 1024 samples is "a good starting point" and 5 samples was used only for demo speed. 4K atlas for walls, 2K per object set. GPU compute. (`w2X` 7:30-8:00, 19:30-20:30)
4. **Denoise in the compositor, not per-object in Cycles.** In-Cycles denoise bleeds across close UV islands and makes seams and artifacts. (`w2X` 30:30-32:00)
5. Do not re-enable already-baked objects when baking the rest; they would distort the light. Re-bake single objects by unchecking "clear existing bake image". (`w2X` 43:00-43:30, 50:00)
6. Export: WebP images plus compression. The material output choice matters:
   - **Background output** gives MeshBasicMaterial: baked light is exact, but it cannot receive or cast dynamic shadows.
   - **Principled output** gives MeshStandardMaterial: it is lit a second time by scene lights, so it looks wrong with an environment map.
   - **Emission output** gives MeshStandardMaterial with the bake in the emissive map: light is correct, and it can receive shadows, but shadows barely show on already-lit areas.
   (`fBH8SYA1aTI` 29:00-34:30)
7. HDR lightmap variant (Valentin, `DpBhfd-LNVk` 1:00-6:30): create a 32-bit float image, bake Diffuse with Direct+Indirect, save as Radiance HDR (not PNG), colour space Non-Color, 1K is enough, and wire it by code as `lightMap` (GLTF does not export it). A 16-bit/PNG lightmap looks "faded". Shadows tolerate low resolution.
8. Rule of thumb from Wawa (`fBH8SYA1aTI` 34:30-35:30): Cycles bake when lights and objects do not move; PBR bake (below) for dynamic items; usually combine both, with a baked environment that still receives shadows and a dynamic hero.

**Stated payoffs:** Immersive Studios (`jurlwQFw9_k` 0:30-1:00, 6:30-7:00): scene went from 4K textures (one floor texture 23.8 MB) to 4.9 MB total, target "under 10 MB", with Blender lighting preserved and good performance. Real-time lighting "isn't as physically accurate as Cycles".

### 2. Bake procedural materials into PBR maps (2 sources)

- Blender node materials (e.g. BlenderKit procedural gold) export as flat white because glTF only knows Principled inputs. **Fix: PBR-bake colour/roughness/metalness/normal into maps.** 2K per channel; one texture per parameter. (`fBH8SYA1aTI` 1:00-8:30)
- Samples can stay at 2: this bake reads node values, it does not simulate light, "much faster and the lighting has no effect". Skip maps that are flat (metalness) and set the scalar instead.
- High-poly to low-poly normal bake: 500k-vertex Suzanne to 2k verts using an auto-generated cage (extrusion about 0.06, slightly larger after subdivision). "Almost indistinguishable" if the camera never gets close. (`fBH8SYA1aTI` 9:00-16:00)
- Bake AO separately, then connect it to the glTF Settings group node so `aoMap` is exported. Keep base colour untouched so the colour can be tweaked at runtime. (`fBH8SYA1aTI` 18:30-25:30)

### 3. Live PBR baseline: HDRI + tone mapping + sRGB + roughness/metalness (3 sources)

Dan Greenheck, Wael Yasmina, Wawa. [P]

- Equirect HDR (Poly Haven, RGBE loader) as both `scene.background` and `scene.environment`; reflections only appear when `scene.environment` is set. (`7gtrBJzm2xE` 4:30-7:00)
- Washed-out HDR is a tone-mapping/exposure problem: Neutral tone mapping and `toneMappingExposure = 0.25` in his demo; Wael uses ACES Filmic. (`7gtrBJzm2xE` 7:30-9:00)
- Shadows: PCFSoft shadow map, set cast and receive on every child (traverse), and use a CameraHelper on the shadow camera to avoid clipped shadows. (`7gtrBJzm2xE` 9:30-13:00)
- `envMapIntensity` is the knob for reflection strength (he uses 0-2 as a range). Note: in modern three.js this is `scene.environmentIntensity` or per-material `envMapIntensity`; verify against r186 docs before use [U for current API].
- Static-scene shadow tuning: add a directional light with `shadow.normalBias` to remove acne. (`w2X` 3:30-4:00)
- Wawa (`9dP5Vc84WgY` 0:30-3:30): make colours consistent via shared roughness/metalness constants; low ambient (0.3) plus two coloured directional lights plus a spotlight. This is a look-dev recipe, not a realism recipe.

### 4. Glass via glTF physical extensions (1 source, thorough)

Needle, `WXzDNkJltyQ`. [P]

- transmission + volume (thickness > 0) gives refraction; thickness 0 is a thin-walled sheet. IOR (1.0 = no bend, up to 2.3 for diamond), roughness for frosted, attenuation colour and distance for tinted depth, clearcoat on top, optional dispersion. (0:00-8:30)
- Metalness and transmission fight each other: "a physical material can't be at the same time a pure metal and transmissive". (6:30-7:30)
- A thickness map is required for complex shapes; this is an approximation, not true ray-traced thickness.

### 5. Performance levers practitioners actually used (Bruno Simon) [P/B]

Devlog 13, `EhZwt9P4GP4`. Shows what a polished, award-winning three.js scene spends its budget on:

- Landing page FPS 70-80 at 1080p/pixel ratio 1 on an M2 Pro before optimisation; **375 draw calls to 222** via a palette texture (one pixel per colour, UV-picked) merged with instancing. (0:30-6:00)
- Skipped transparency sorting entirely (accepting more overdraw). Own area-based frustum culling and physics sleeping off-screen. (9:00-13:30)
- Textures: 1024 to 512 for terrain, ETC1S for small/grayscale and UASTC for fidelity, with embedded mipmaps via `toktx`; `gltf-transform` with quantize only; WebP for UI. PNG "is really not suited for 3D". (17:00-20:00)
- New PCF shadow sampling (Vogel disc) is smoother and cheaper. (20:00)
- Mobile gets a regexp-detected low-quality mode: smaller shadow map, cheaper bloom, no DOF, no water blur; device probing was judged unreliable. (21:30-22:30)
- Water devlog (`MXpML0B2MJc` 6:40): "forget fluid simulation, refraction or ray tracing" when performance matters, i.e. fake the water with gradients and noise. Lighting is deliberately non-physical (a sun that never sets, colours tweaked per time of day, "light bounce" faked by tinting; 1:00-2:40, 5:00).

## Per-video cards

| Video | Channel | URL / date / views | Gems (timestamps) | Grade |
|---|---|---|---|---|
| How to Bake Lighting with Blender for Three.js (51:21) | Wawa Sensei | youtube.com/watch?v=w2XvGYxQiOk, 2025-09-05, 12.7k | Full Cycles-bake pipeline; compositor denoise (30:30); margin 16 to 24 (45:30); "three.js is the equivalent of Eevee... far from Cycles" (4:00-5:00) | A (procedure) |
| From Blender to Three.js: Complete Baking Guide (36:00) | Wawa Sensei | `fBH8SYA1aTI`, 2025-09-19, 8.0k | PBR bake; hi-to-lo with cage 0.06 (11:30); AO export (21:30); bake output type trade-offs (32:30-34:30); when to use which (34:30) | A |
| BIG threejs Baking tutorial (7:16) | Immersive Studios | `jurlwQFw9_k`, 2023-07-30, 7.8k | 23.8 MB texture to 4.9 MB scene; 10 MB budget; Squoosh-style compression -65%; bake floor/walls/statues but not glass or swappable paintings (1:00-3:00) | B+ |
| Lightmap Baking in Blender for Three.js (8:03) | Valentin's coding book | `DpBhfd-LNVk`, 2025-01-20, 20.5k | 32-bit float HDR lightmap, Non-Color, 24 samples (3:30), wire by code (2:00), PNG gives faded result (6:00). Captions are Arabic auto-translation. | B |
| Realistic Reflections... Environment Mapping (14:49) | Dan Greenheck | `7gtrBJzm2xE`, 2024-04-01, 9.1k | scene.environment vs background (6:00-6:30); exposure 0.25 (8:30); shadow camera helper (12:00) | B (basics) |
| Tutorial: Realistic Glass Materials (9:23) | Needle | `WXzDNkJltyQ`, 2025-10-10, 881 | Glass parameter matrix; metal/transmission conflict (7:00) | A- |
| Performance - Devlog 13 (23:35) | Bruno Simon | `EhZwt9P4GP4`, 2026-02-02, 6.4k | draw calls 375 to 222 (5:30); KTX2 params (18:30); mobile low-quality list (22:00) | A |
| Water & Trees - Devlog 4 (14:47) | Bruno Simon | `MXpML0B2MJc`, 2024-11, ~21k | Fake-over-physical choices; day/night light as colour tables (1:00-5:00) | B |
| Realtime and Offline Rendering Explained (4:23) | the lemon | `HwnACEgWGfs`, 2025-07-30, 4.5k | "Real-time sacrifices realism... fakes GI, AO, ambient lighting, reflections"; GI has no standard solution (0:00-1:30); Interstellar ~100 h/frame (2:30) | B (framing) |
| Realtime GI in Enshrouded (50:22) | Graphics Programming Conf. | `57F1ezwH7Mk`, ~2024, 13k | Cascaded probe cache 32^3 x 12 cascades, 16k cell cap, 2 m start spacing (2:40-3:20); fixed ray budget, only about 10% of rays picked per probe (10:20, 13:00); SDF tracing; small objects not in the representation (4:00); probes must be small or they leak (8:00) | A- (engine-level; not WebGL) |
| Radiance Caching for Real-Time GI (33:54) | SIGGRAPH Advances in RT Rendering | `2GYXuM10riw`, 67k | Probe-grid GI "suffers from leaking, a distinct flat look"; screen-space denoisers fail at 1 ray/pixel (2:20-4:00) | A- (limits) |
| A 41 Minute Rant About SCREEN SPACE REFLECTIONS (41:36) | K V B R D | `wJguKogIGII`, 2025, 3.5k | SSR: holes, disappearing at screen edges, needs cubemap fallback (0:20, 5:00); planar reflections and real-time cubemaps as alternatives (12:00-13:00); a mirror-like plane is best done as a planar render; opinionated | B- |
| Shaders for the future of the web (19:57) | Maxime Heckel / Figma Config | `qPSyN9GzuEU`, 2025-06-18, 4.5k | Glass shader: scene snapshot via texture2D, back and front face passes, per-channel dispersion (10:00-13:00); post FX as screen shaders (13:30) | B (stylised, not realism) |
| Immersive Garden talk (45:23) | Simplement Antho | `rr7p4dPfloc`, 1.8k | Pre-upload textures and precompile shaders to avoid hitches (29:20-31:40); LUT grade in post for mood (14:20-15:20); depth-based fog blend in post (42:40-43:20) | B- |
| Making our R3F Scene Look Better | Wawa Sensei | `9dP5Vc84WgY`, 2023, 22k | Colour consistency, moving spotlight, bloom/vignette/DOF/scanline, emissive spheres with `toneMapped: false` (6:30) | C (stylised) |
| Realistic Scenes - Tone Mapping, HDR, sRGB | Wael Yasmina | `6XvqaokjuYU`, 2022, 44k | HDRI + sRGB output + ACES Filmic + MeshStandard. Captions are Arabic; skim only. | C |

## Limits practitioners state

| Statement | Who / where | Grade |
|---|---|---|
| Three.js real-time lighting is Eevee-like; "far from what we get in Cycles"; you cannot expect Cycles-style re-render on every camera move in a web experience | Wawa, `w2X` 4:00-5:00 | [P] |
| Real-time "isn't as physically accurate" as Cycles ray tracing; the answer is to bake | Immersive Studios, 0:30-1:30 | [P] |
| Cycles bake bakes lighting only for static lights and objects; dynamic items need PBR (live light) | Wawa, `fBH8SYA1aTI` 34:30 | [P] |
| Baked Principled material double-lights; the Emission option is the way to keep baked light with shadows | Wawa, 33:00-34:30 | [P] |
| Blender procedural nodes do not survive glTF export; bake to PBR maps | Wawa, 2:00-3:30 | [P] |
| A metal and a transmissive surface cannot coexist physically; mixing is "not from this world" | Needle, 6:30-7:30 | [P] |
| Thickness and refraction in glTF glass are an approximation (thickness map), not traced | Needle, 4:30-5:00 | [P] |
| Real-time sacrifices realism for speed and "fakes" GI, AO, ambient light and reflections; GI has no standard solution | the lemon, 0:00-1:30 | [P] |
| Probe/irradiance GI leaks and looks flat; screen-space denoisers cannot fix input that is too noisy at 1 ray per pixel | SIGGRAPH radiance caching, 2:20-4:00 | [V] talk |
| Probe GI in a shipping game traces only about 10% of requested rays on a fixed budget, tiny objects absent from the representation, probes kept small or they leak | Enshrouded, 4:00, 8:00, 10:20, 13:00 | [V] talk |
| SSR breaks at screen edges and under occluders and needs a cubemap fallback; planar reflections or cubemaps are more reliable | K V B R D, 0:20-5:00, 12:00 | [P] opinion |
| Fluid simulation, refraction and ray tracing are out when frame rate is the priority; fake water | Bruno, `MXp` 6:40 | [P] |
| Even a showcase scene sits at ~220 draw calls and 70-80 fps at 1080p without optimisation; low-end mobile needs a separate quality mode; device probing is unreliable | Bruno, Devlog 13 | [P/B] |

## What this means for the skill (L6 view)

- Offer **"bake it in Blender, stay static"** as the primary realism path for hero shots with fixed camera and lights, and **"live PBR + HDRI"** only for the interactive parts. Both of these are well documented by multiple practitioners.
- State the ceiling in plain terms: no source on this lane shows path-traced-grade reflections or caustics running live in three.js. The talks that do real-time GI (Enshrouded, Epic) are native engines with SDF/probe systems and give up small-object and leak accuracy.
- Gap worth a follow-up lane: studio-level talks (Lusion, Active Theory) did not yield captions; consider the Awwwards/Codrops write-ups or `yt-dlp` auto-subs for specific IDs once rate limits clear.

## Round 3 (yt-dlp auto-subs, 2026-10-16)

Fetched with `yt-dlp --write-auto-subs --skip-download --sub-format vtt --sub-langs en`, 60 s apart. Raw VTTs are in `docs/research/community-scan/sources/realism-youtube/_r3/`. Three fetches attempted; no realism gems found.

| Video | Result |
|---|---|
| Active Theory KIKK (`Zpl-SEwQK-A`) | No subtitles exist. Studio-talk gap remains. |
| Bruno Devlog 2, Infinite grass (`cesPK0kYkyE`) | Fetched. Content is TSL/WebGPU node materials, wind via a "perlin" texture, shared `getWind` function. Nothing on lighting or realism. Grade C. |
| Resn, "Perverting the Web" (`2BRG9_Bkv8w`) | Fetched. Creative-direction talk (distorting UX conventions); no rendering content. Grade C. |
| Bruno Devlog 5, Weather (`C2gDL9Qk_vo`) | HTTP 429 after the second fetch; stopped per instruction. Not read. |

Conclusion unchanged: no captioned studio talk in this scan documents a realism recipe or a real-time ceiling. The remaining studio gap needs non-YouTube sources (case-study write-ups, Codrops, studio blogs).
