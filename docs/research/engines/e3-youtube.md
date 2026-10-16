# E3 - YouTube harvest: engine choice and Blender to web export

Fetched 2026-10-16 with `ytrelay` (search, info, transcript). All claims are [P] practitioner (auto-captions, transcript text is data) unless marked. Transcripts and SOURCE.txt: `docs/research/community-scan/sources/engines-youtube/<channel>__<id>/`. Timestamps are `h:mm:ss` into the video; URL = `https://www.youtube.com/watch?v=<id>`.

## Verdict on the source type

- **Engine-choice content on YouTube is thin and mostly shallow.** The 2024-2026 "Babylon.js vs three.js" hits are 1-5 min listicles ("Three.js vs Spline vs Babylon.js", feature-checklist, no measurements). Only two carried usable decision rules (Gamefromscratch, AGWS). Nothing there should override the forum/doc evidence from E1/E2.
- **Blender to web export is where YouTube pays off**, almost entirely in the **three.js** ecosystem (Wawa Sensei, Valentin, freeCodeCamp, Deayan). Equivalent 2024-2026 Blender to Babylon.js tutorials effectively do not exist: searches returned only 2015-2023 items (Bullet Tuber 2019, Mad Dog 2014, LB Artworks 2023 lightmaps). The one 2026 hit (Viseni Design, "Complete AO Lightmapping Workflow for Babylon.js & Three.js", `kVJzCemCiX8`, 4 min, 2026-06-04) has a 95-character caption, so it was not harvestable.
- Gaps (no usable 2024-2026 video found, 429 rate-limit hit after ~20 transcript pulls, so fallback `yt-dlp` was not needed): react-babylonjs (zero relevant results; only `Requiem` / knervous 2024 React+Babylon MMO client optimization, not fetched), Babylon official channel Blender exporter / glTF (only 2018-2020 Node Material Editor videos; 9.0 release video `Th9mD_D5DrQ` has no captions), PlayCanvas-from-Blender (2017-2022 only), model-viewer/USDZ from Blender (generic 2021-2024 USDZ export clips, nothing on model-viewer), SimonDev / Dan Greenheck / Bruno engine-choice (none exist; Bruno's only 2026 relevant video is WebGPU/TSL). Needle Blender videos are 2-4 min, 2023-24 and mostly lightmap bake teasers.
- Not retrieved after 429s: Gamefromscratch "Babylon 8" (`KqCVnpkTeK0`), Wawa "3 R3F Mistakes" (`GlaFgKgtJM4`). Retry later.

## Recurring procedures (appear in 2+ videos)

| # | Procedure | Seen in | Detail |
|---|---|---|---|
| P1 | **Bake anything Blender-procedural into image textures before glTF export.** The exporter only understands Principled BSDF with image/constant inputs; noise/Voronoi/custom nodes export as a white or default material. | Wawa PBR (0:02:00-0:03:30), Deayan (0:07:30-0:09:00), freeCodeCamp (2:08:30) | Cycles only (Eevee cannot bake): Deayan 0:08:32, freeCodeCamp 1:49:00. |
| P2 | **Second UV map just for baking** ("simple bake"), non-overlapping islands, original UV left for tiling textures. | Wawa lighting (0:13:00-0:15:00), freeCodeCamp (2:09:31) | Mark seams on boxes, otherwise Smart UV Project. |
| P3 | **Island margin scales with texture size** or the denoiser leaks neighbours into each other. | Wawa lighting (0:45:00-0:46:03), freeCodeCamp (2:11:30-2:12:30) | 4K: SimpleBake suggests 16 px, Wawa had to raise to 24 px after artifacts; freeCodeCamp quotes ~32 px at 4K (about 0.008 margin in Smart UV Project). |
| P4 | **Bake multiple objects into one atlas** (one collection, one texture, one name) for fewer draw calls. | Wawa lighting (0:19:30-0:21:00), freeCodeCamp (4:30:31, draw-call point) | Scale UV islands by visual importance, not by object count (Wawa 0:27:01: painting took most of the 4K texture). |
| P5 | **Ship compressed, embedded textures in WebP, Draco geometry via a post-export tool**, not Blender's own texture sliders. | Wawa lighting (0:49:03: exporter set to WebP), freeCodeCamp (2:32:30-2:37:02), Khronos/Blender talk (0:48:03) | Blender 4.x offers WebP in exporter; Blender export cannot set texture resolution (Khronos talk 0:17:05). |
| P6 | **Occlusion goes in a custom glTF Material Output group node** (R channel; metal/rough use G/B), because Blender has no AO input. | Wawa PBR (0:21:31-0:23:03), Khronos talk (0:22:02-0:23:01) | SimpleBake has "create glTF settings" to wire it automatically (Wawa 0:23:03). |
| P7 | **Lightmaps cannot be wired through the exporter**; `lightMap` must be assigned in code. | Valentin lightmap (0:02:01) | Bake 32-bit float image, save Radiance HDR (not PNG), colour space Non-Color. |
| P8 | **Apply modifiers/scale, realize instances before export.** | Deayan (0:04:31-0:06:01, 0:12:31), Khronos talk (0:06:30) | Geometry-Nodes instances do not export until a Realize Instances node is added. Khronos: modifiers and shape keys cannot be exported together (0:07:01). |

## Per-video cards

### Wawa Sensei - "From Blender to Three.js: The Complete Baking Guide (AO, PBR, High to Low)" - `fBH8SYA1aTI`, 36:00, 2025-09-19
- Blender procedural gold material (BlenderKit) exports as white: "three.js doesn't handle all the custom nodes from Blender" (0:02:00-0:03:00). Fix is a PBR bake via SimpleBake (paid add-on, ~$20 per his other video).
- PBR bake: stay in object mode, bake roughness/normal/metalness, 2K each (one texture per channel, so four 2K maps), samples ~2 ("reading data, lighting has no effect", unlike Cycles) (0:05:00-0:06:32). Check roughness/metalness maps for detail; if flat, drop the map and use a constant to save texture memory (0:08:00-0:08:40).
- High-to-low: duplicate mesh, subdivide one (5 levels = ~500k verts, "way too much" for web, 0:09:30), auto-generate a cage, extrusion about 0.06 (0:11:33), bake to target. Rebake cage after changing subdivision (0:14:30-0:15:01). Result: ~2,000 verts looking like 500,000 (0:14:02, 0:15:32).
- AO: no UVs means Smart UV Project + pack with pixel margin (0:19:31); wire into glTF Settings group, then in R3F set `aoMap` and keep colour dynamic so you can recolour at runtime (0:24:30-0:25:30).
- **Material-type decision (0:29:00-0:34:30)**: SimpleBake "background" output imports as `MeshBasicMaterial` (unaffected by lights, cannot receive shadows); "Principled BSDF" output = `MeshStandardMaterial` that double-lights a baked scene; "emission" output = `MeshStandardMaterial` with emissive map that keeps the baked light correct **and** can receive real-time shadows. Hands-on result: emission is the best compromise.
- **Decision rule (0:34:30-0:35:31)**: Cycles bake when lights and objects are static; PBR bake for anything that moves or is relit; "often a combination": baked environment + PBR-textured dynamic character.

### Wawa Sensei - "How to Bake Lighting with Blender for Three.js" - `w2XvGYxQiOk`, 51:21, 2025-09-05
- Opening problem statement (0:00:00): Cycles render looks great, GLB in three.js "underwhelming; lights and shadows help a bit but nowhere near". Real-time = shortcuts; baking is the fix (0:04:02-0:05:00).
- Starter setup: ambient light intensity 1 + `Environment preset="sunset"` + directional light with `shadow-normalBias` to kill acne (0:03:02-0:04:02).
- Manual bake steps (0:05:32-0:09:00): new image on material, Cycles, Bake "Combined", wire to base colour, roughness 1. Pain point: rebaking requires undoing all of it, hence SimpleBake preset (0:09:00-0:11:30).
- Samples: 1,024 "a good starting point" (0:08:01); he drops to 5 for demo (0:19:30). Multi-object single texture at 4096 (0:20:01-0:20:30).
- Export: WebP images, quality raised, Draco on (0:49:03).

### freeCodeCamp - "3D Web Development with Blender and Three.js - Create a Cozy Cafe Portfolio" (Chad/Andrew Woan) - `ozWrlHQGuvI`, 5:24:27, 2026-04-22
Only grepped (353k-char transcript); decision-relevant sections:
- 2:06:01: EXR textures are huge, convert to PNG for web.
- 2:08:30: baking is "a very common method on creative websites"; also for optimisation.
- 2:13:30: **only bake things you will never change** (bread/caviar baked, but objects needing runtime variation not).
- 2:32:30-2:37:02: export glTF "material quality 100 because we use an online compressor"; compression in a gltf-transform based web tool with Draco, max texture 1024, WebP. **File size went up (2.6 MB to 2.95 MB) but VRAM dropped from 136.8 MB to 49.1 MB**: judge by memory, not disk (2:36:00-2:37:02).
- 3:07:32-3:08:01: manual DRACOLoader wiring, copy `node_modules/three/examples/jsm/libs/draco` into `public/draco`.
- 4:13:31: exporter sometimes names meshes by mesh data name not object name; fixed with a Blender Python script (symptom: raycast-by-name breaks).
- 4:30:31: raycaster-on-many-meshes issue; solution is to bake into a single texture or use the group (draw calls).

### Deayan Studios - "Master Exporting in Blender - Fix GLB/glTF Exports" - `i82_Rx1OUe0`, 15:52, 2025-11-26
- glTF = separate files (mesh/textures/dependencies), GLB = single binary; "mostly nowadays you go with GLB" (0:02:00-0:03:00).
- Geometry Nodes: exporter sees only original mesh; add **Realize Instances** before Group Output, then apply modifier (0:03:31-0:06:01). Named attributes (per-instance colour) break after realizing (0:06:30).
- Supported materials: Principled BSDF only; subsurface/specular not supported; emission exports but differs; procedural textures rejected (0:07:01-0:08:32).
- Bake with Cycles (not Eevee): UV unwrap, create image texture node, bake Diffuse or Combined, check lighting first because shadows are baked in (0:08:32-0:12:02).
- Optimisation checklist: apply scale (0:12:31), Decimate planar for redundant faces (0:13:00), Triangulate for strict formats (0:13:30), keep textures as small as the closest view allows (0:14:00).

### Valentin's coding book - "Lightmap Baking in Blender for Three.js" - `DpBhfd-LNVk`, 8:03, 2025-01-20 (captions need `--lang en`)
- New image **32-bit float, 1K** (HDR, not PNG; PNG gives "washed-out colours" and breaks exposure/intensity, 0:01:00, 0:05:34-0:06:01). Merge meshes into one object first and add the lightmap image node on every object before joining (0:02:31-0:03:32). Bake type Diffuse, Direct + Indirect, 24 samples (0:03:32-0:04:03). Save as Radiance HDR, Non-Color.
- Lightmap node not recognised by glTF exporter; connect in code (0:02:01).
- Resolution rule: lightmap can be lower res than albedo; shadows soft anyway (0:07:02).

### Valentin's coding book - "Blender to Three.js Workflow - Your Go-To Cheat Sheet" - `j0j2Y84CyuA`, 2:30, 2025-02-02
- Default Principled BSDF exports to `MeshStandardMaterial`; touching transmission/coat promotes to `MeshPhysicalMaterial` automatically (0:01:00-0:01:30). Pack metal/rough/AO into one texture channels (0:01:30). Tiling via UV Mapping node + repeat (0:02:00). Warns Blender glTF docs lag (`blend_mode` replaced in 4.2, 0:00:30). Cheat sheet linked in description (not harvested).

### Blender - "The Complete glTF Asset Creation Pipeline" (Khronos/exporter maintainer talk) - `KTPdNUGwIGc`, 53:43, 2023-10-27 (older; exporter limits mostly still true, verify against current docs)
- glTF "is not an authoring format, it is the last-mile file format for efficient display" (0:01:30).
- Limits stated: shape keys vs applied modifiers cannot be combined (0:07:01); exporter reads a colour factor times a texture as multiply (0:11:32); no export-time texture resolution control (0:17:05); subsurface not in spec then (0:19:00); clearcoat tint not in spec; sheen supported (0:20:30); visibility cannot be animated (0:43:34); only TRS + shape keys animate, with texture-transform / factor animation via an extension "soon" (0:44:00); volume extension (thickness) not yet exported by Blender (0:45:32).

### Needle - "Create Realistic Glass Materials for Web" - `WXzDNkJltyQ`, 9:23, 2025-10-10 (Unity authoring but glTF material model is the same)
- Glass = transmission + volume together (0:03:02). **Thickness 0 = thin-walled, no refraction; need thickness > 0 for refraction** (0:03:33). IOR 1 = "shiny air", up to ~2.3 for diamond (0:05:30-0:06:00). Metalness and transmission fight each other (0:06:32). Attenuation colour + distance tints by travel depth (0:07:31). Thickness map for complex shapes (0:05:02). Dispersion, clearcoat and rough refraction combine (0:00:00-0:01:31).
- Engine-side signal: Needle ships glass/clearcoat/sheen as first-class glTF extensions on top of three.js; their Blender path is "Needle Engine for Blender" (2023-24 tutorial `TXEHR4Cq7iU`, not re-read).

### Gamefromscratch - "Babylon 9 Game Engine - Best Update Yet!" - `mYLIUZzaDhk`, 9:56, 2026-03-31
- Opinion (0:00:00): for web 3D he would pick **Babylon or PlayCanvas**, Babylon "because of its solid support, growing feature set, and open source from the beginning".
- 9.0 features named: clustered lighting, textured area lights (0:00:30-0:01:01), Node Particle Editor (0:01:30), Inspector 2.0 rebuilt in React and extensible (0:02:30, 0:07:00), Frame Graph render-pipeline editor (0:03:01), animation retargeting (0:04:01), Gaussian splats incl. SPZ + editable splats (0:05:00), large-world rendering, geospatial camera, 3D Tiles (Cesium) (0:07:32-0:08:02), OpenPBR, dynamic IBL shadows, SDF text, outline renderer (0:08:31).
- "Editor added in 8; that was a big advantage PlayCanvas had over Babylon" (0:05:31).

### Gamefromscratch - "BabylonJS Game Engine FINALLY Gets a World/Level Editor" - `f3_g1QEvRxA`, 14:05, 2025-09-10
- Babylon Editor v5 (Electron app, Win/macOS, separate repo, Apache-2.0) scaffolds Next.js / SolidJS / vanilla; scripts attach to entities; KTX compressed-texture support (0:02:31). Reviewer: "early", "quite a few things don't work", "a lot buggy" (0:04:01), no Linux build (0:02:01). Needs `babylonjs-editor-tools` installed (0:05:31).

### Bruno Simon - "WebGPU & TSL in Three.js - The new course" - `8HeNnp9sdm4`, 7:36, 2026-09-01
- three.js "now officially supports WebGPU" (0:00:00). **TSL compiles to WGSL (WebGPU) or GLSL (WebGL fallback)**, so one node-based shader source covers both (0:01:01-0:01:31). Because not every visitor supports WebGPU, shipping WebGPU-only is rejected (0:00:31). Relevance: directly reduces the historical "Babylon has WebGPU, three.js doesn't" argument.

### Engine-choice listicles (low value)
- GigaBits `p-PWN-rGbKo` (5:15, 2025-11-29): three.js = most flexible + biggest community, Babylon = structured engine, "often performs better on physics-heavy or game-like scenes", own editor, but "less popular, smaller ecosystem"; Spline = designers. Claims are assertions (no benchmark shown). [P, low]
- AGWS `EivL-WsQQ_s` (8:19, 2024-05-12): Babylon better TypeScript and "better debugging tools"; three.js more community. Only measured fact: a heavy three.js site used ~2.5 GB RAM in his browser, ~20 MB array buffers on an optimised one; IKEA shows 2D image first, 3D model on demand (0:06:30-0:07:01). Product-configurator pattern, not engine comparison.
- Tom Delalande `ifKnOtWOW0w` (4:10, 2026-05-06): browser games "download all assets on every visit, which is why they tend to be low poly" (0:03:31); runs on GPU regardless of engine. Humour video; skip.

## Stated limits (verbatim-grounded)

- Blender's glTF exporter: procedural nodes, subsurface, specular, most Blender-only features do not export (Deayan 0:07:01; Wawa 0:03:00; Khronos 0:19:00).
- Lightmaps and AO must be wired by hand (code for lightMap; glTF Settings group for AO).
- Eevee cannot bake; Cycles required (Deayan 0:08:32; freeCodeCamp 1:49:00).
- Drivers/shape-key corrective shapes and modifier+shape-key export are exporter limits (Khronos 0:07:01, 0:40:32).
- Compression can increase file size while reducing VRAM (freeCodeCamp 2:36:00).
- Babylon Editor v5 is early/buggy as of Sep 2025 (Gamefromscratch 0:04:01).

## Decision rules to carry into the skill

1. **Material that is Blender-procedural: bake to PBR maps (colour/roughness/metalness/normal), not rebuild by hand.** Drop any map that is a constant and set a value instead (Wawa fBH8 0:08:00).
2. **Static lights and static props: Cycles bake. Moving parts or lights: PBR bake. Mix them** (Wawa fBH8 0:34:30-0:35:31).
3. **Bake output type chooses runtime material:** background gives `MeshBasic` (no shadows), emission gives `MeshStandard` with emissive and shadow reception, Principled gives double-lighting (Wawa fBH8 0:29:00-0:34:30). Default pick: emission.
4. **Lightmap = 32-bit float, Radiance HDR, Non-Color, 1K is often enough; assign `lightMap` in code** (Valentin).
5. **UV margin scales with atlas size** (about 16-32 px at 4K, increase if denoiser leaks) (Wawa/freeCodeCamp).
6. **Pack many objects into one atlas** to cut draw calls; only bake things that will not change (freeCodeCamp 2:13:30, 4:30:31).
7. **Post-process with gltf-transform-class tools: WebP/KTX2, Draco; judge by VRAM** (freeCodeCamp 2:36:00-2:37:02).
8. **Engine choice:** for creative-experience sites the surviving YouTube-visible practitioner ecosystem (baking guides, R3F, Needle, Bruno's WebGPU/TSL) is three.js; Babylon's case is its integrated toolbox (Inspector 2.0, NME, Node Particle Editor, Frame Graph, Havok, Editor v5, splats, 3D Tiles) and TypeScript structure. PlayCanvas is the other engine independent reviewers name (Gamefromscratch 0:00:00). **No video offered measured performance data**; do not cite these for benchmarks.

## Reproduction

`ytrelay search "<q>" --features all --limit 12` then `ytrelay info`, `ytrelay transcript`. Rate limit (HTTP 429) appeared after ~20 transcript fetches in one session; no yt-dlp fallback was used.
