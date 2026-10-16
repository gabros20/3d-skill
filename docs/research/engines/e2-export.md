# E2 - Blender to web: export strategies for quality and realism

Lane E2, 2026-10-16. Blender 5.2.2 LTS (installed, introspected), three r186.1 (npm), @babylonjs/core 9.31.0 / @babylonjs/loaders 9.31.0 (npm, modified 2026-10-15). Grades: [V] official doc/source read today, [B] measured here, [P] practitioner/maintainer post, [U] unverified or vendor claim. Adds to, does not repeat: `skills/3d/references/blender-export.md` (settings, modifiers, USDZ basics), `asset-pipeline.md` (gltf-transform/gltfpack), `docs/research/realism/l5-written-gems.md` (bake recipes, env maps, tone-map divergence).

## 0. Findings that change the skill

1. **Blender 5.2's exporter has gltfpack built in.** `export_use_gltfpack`, `export_gltfpack_tc` (KTX2), `_si` (simplify), `_vp/_vt/_vn/_vc` (quantisation bits), `_kn` (keep named nodes), `_noq` exist [B: `get_rna_type().properties`, 2026-10-16]. The skill's "compress once downstream" rule stands; this is a convenience path, not a reason to skip the master GLB. Whether the gltfpack binary is bundled or must be on PATH: [U], test before relying.
2. **`KHR_materials_diffuse_transmission` is not exported by Blender and not loaded by three r186**, but Babylon 9.x has a loader for it [V: Blender `exp/material/extensions/` has anisotropy, clearcoat, dispersion, emission, ior, iridescence, sheen, specular, transmission, variants, volume only; r186 `GLTFLoader.js` header; Babylon `loaders/src/glTF/2.0/Extensions/KHR_materials_diffuse_transmission.ts`]. Thin translucency (leaves, paper, wax) must be faked: thin-walled transmission, alpha, or a baked translucency map.
3. **The Blender manual's extension list omits iridescence export, but the code has it** (`iridescence.py`) and the rst documents the sockets [V]. Trust the repo over the summary page.
4. **The official Babylon.js Blender exporter (`.babylon`) is effectively frozen.** BlenderExporter last commit 2023-09-04 (v3.3.2, zip named for Blender 3.3); the docs page still says "v6 is for Blender 2.8 (currently in beta)" and was last touched 2026-07-31 only editorially; the old `Babylon.js/Exporters` repo Blender folder now just says "has moved" (2019) [V: gh api]. Babylon's own docs route Blender users to glTF ("Blender to BJS, using glTF") [V]. Treat glTF as the only Blender to Babylon path.
5. **`KHR_gaussian_splatting` is ratified by Khronos** [V: spec README "Complete, Ratified"], Babylon has a loader file for it, three r186 lists it only as a "separately registered plugin" [V]. Splats can ride in GLB, but runtime support is uneven.

## 1. Matrix: Blender feature, glTF, three r186, Babylon 9.31

"Exports" = Blender 5.2 exporter per rst + repo [V]. Engine columns = loader source/header [V] unless noted. Y = native loader support, P = needs a plugin/example add-on, N = none.

| Blender feature | How to author it | glTF output | three r186 | Babylon 9.31 | Notes |
|---|---|---|---|---|---|
| Base colour, metal/rough, normal (tangent, +Y), emissive | Principled with Image Texture; roughness G, metal B | core PBR | Y | Y | Metal in B, rough in G, AO in R (ORM) |
| Baked AO | Image into `glTF Material Output` node group "Occlusion" input (Shader Editor Add-ons pref on) | `occlusionTexture` | Y (aoMap) | Y (ambient) | R channel; can share ORM image |
| Second UV (lightmap) | UV Map node on that texture | `texCoord: 1` | Y: `texture.channel = texCoord` [V line 3451] | Y (uv2) | Lightmap hijacks the AO slot or is set in code, see section 3 |
| Emission strength > 1 | Emission Strength | `KHR_materials_emissive_strength` | Y | Y | Auto when any emissive component > 1 [V] |
| Transmission | Transmission Weight (not alpha) | `KHR_materials_transmission` | Y | Y | Roughness blurs it; keep alpha Opaque [V] |
| Volume / thickness | Volume Absorption on Output, plus thickness into `glTF Material Output` (G channel) | `KHR_materials_volume` | Y | Y | Needs transmission > 0; colour = attenuation, density = 1/distance |
| IOR | Principled IOR | `KHR_materials_ior` | Y | Y | Written only with transmission, volume or specular; 1.5 omitted |
| Dispersion | `glTF Material Output` dispersion | `KHR_materials_dispersion` | Y | Y | Requires volume |
| Clearcoat | Coat weight/roughness (R/G) | `KHR_materials_clearcoat` | Y | Y | Babylon also has draft `KHR_materials_coat` |
| Sheen | Principled sheen (roughness texture in A) | `KHR_materials_sheen` | Y (plugin registered; header list omits it) | Y | Sheen BSDF node is Cycles-only and not what exports |
| Specular level/tint | Specular IOR Level / Tint | `KHR_materials_specular` | Y | Y | `export_original_specular` exists |
| Anisotropy | Anisotropic sockets + matching tangent UV | `KHR_materials_anisotropy` | Y | Y | Tangent UV map must match normal map's |
| Iridescence (thin film) | Thin Film sockets + `glTF Material Output` max thickness | `KHR_materials_iridescence` | Y | Y | Documented in rst; not in the summary list |
| Diffuse transmission / SSS | none | not exported | N | Y (loader only) | See finding 2 |
| Unlit | Mix with Camera Ray, no Principled | `KHR_materials_unlit` | Y | Y | |
| Texture mapping | Mapping node (Point type) | `KHR_texture_transform` | Y | Y | Z-rotation only, uniform scale only [V] |
| Material variants | glTF Variants panel (enable UI in prefs) | `KHR_materials_variants` | P (three-gltf-extensions, last push 2022-12) | Y | Configurator core. Three side is stale: test |
| Animation of material/light/camera props | Pointer export (experimental) | `KHR_animation_pointer` | P (needle-tools/three-animation-pointer, pushed 2026-10-06) | Y | Needs baked/sampled animation; floats/ints/bools only for custom props |
| Mesh quantisation | Meshopt/gltfpack options | `KHR_mesh_quantization` | Y | Y | Import-only in Blender's own list; produced via meshopt/gltfpack |
| Meshopt | `export_meshopt_compression_enable` | `EXT_`/`KHR_meshopt_compression` (pick via `export_meshopt_extension`) | Y both | `EXT_` Y | Babylon docs: meshopt decoder injection "not yet supported" [V]. Prefer `EXT_` for compatibility [U] |
| Draco | `export_draco_*` | `KHR_draco_mesh_compression` | Y | Y | Export-only in Blender |
| GPU instancing | `export_gpu_instances` | `EXT_mesh_gpu_instancing` | Y | Y | Children of one Empty, meshes without children, no per-instance material [V] |
| Punctual lights | `export_lights`; Lighting Mode Standard / Unitless / Raw (deprecated) | `KHR_lights_punctual` (cd, lx) | Y, intensity passed through unchanged [V line 752] | Y | Area lights and World not exported [V] |
| WebP / KTX2 textures | WebP exporter option; KTX2 via gltfpack option or gltf-transform | `EXT_texture_webp` / `KHR_texture_basisu` | Y both (+ AVIF) | WebP Y, basisu Y | |
| Gaussian splats | not from Blender | `KHR_gaussian_splatting` | P | Y (loader) | Ratified [V]; produced elsewhere |
| Hair/fur | Hair curves | not exported | N | N | Alpha cards |

### What does not survive, and the standard workaround

| Lost | Evidence | Workaround |
|---|---|---|
| Procedural nodes, Color Ramp, Mix, noise bump/displacement | Exporter reads only recognised arrangements [V]; donmccurdy "vast majority of Blender's nodes... cannot be exported" [P, discourse 40116, 2022-07-08] | Bake to PNG textures wired to Principled; bake normal from displacement |
| Geometry Nodes | Apply modifiers on a copy [P 40116]; `export_gn_mesh` marked experimental [V rst:1021]; skill's own measurement: 2 tris vs 2,688 [B, blender-export.md] | Apply, or realize instances before export |
| Simulation / GN animation | manthrax: "no easy/obvious way"; poster's workaround: bake sim nodes, Alembic, import, MDD, import, GLB shape keys [P, discourse 84737, 2025-07-02] | Bake to vertex-animation textures or shape keys; or pre-render |
| Particles, line trails | mjurczyk: Blender-specific, rebuild in three.js by hand; instances in the GLB bloat JSON, textures dominate size [P, discourse 72780, 2024-10-14] | Re-create as Points/instanced meshes in code; ship the emitter params as `extras` |
| Hair curves, Principled Hair | Not in exporter feature list [V] | Alpha cards (baked from the strands), or shell fur in a shader |
| World / HDRI, area lights | "not supported by glTF, and will be ignored" [V] | Ship the HDRI separately (EXR/HDR/KTX2 cube), match rotation and exposure in code |
| Volumes beyond Absorption (smoke, fog) | Only Volume Absorption maps [V] | Bake to sprites/slices or pre-render; Igloo shipped VDB via a custom exporter [P, l5] |
| Drivers, constraints | Only keyed/sampled output; `export_bake_animation` forces sampling [B] | Bake animation (section 4) |

## 2. Babylon-specific Blender paths

| Path | State | Verdict |
|---|---|---|
| glTF/GLB via Khronos exporter, loaded by `@babylonjs/loaders` | Babylon docs page "Blender to BJS, using glTF" [V]; Babylon's art-prep docs describe the same exporter options [V] | Default and only recommended path |
| Official `.babylon` exporter (BlenderExporter) | Last commit 2023-09-04; zip is for Blender 3.3; docs say beta/2.8 [V] | Legacy. Do not start a 2026 project on it. Reasons to touch: existing `.babylon` scenes |
| Community "Blender + Babylon level authoring" (components, colliders, Havok, prefabs, LUTs, `.glb` + `.scene.json` manifest) | Forum showcase, started 2026-07-07, maintainers sebavan and Deltakosh replied positively [P, forum 63754]. Not an official tool | Pattern worth copying: GLB for geometry/materials, a JSON manifest for behaviours. Do not depend on it |
| Babylon Sandbox / Inspector | Docs: "quick check using the sandbox" [V] | Use as the second-engine verifier: drop the GLB, switch material overrides in Inspector, compare to three |
| Node Material Editor | A Babylon-native material graph (JSON snippet). Not an import target from Blender. Maintainer PatrickRyan recommends a small NodeMaterial for simple unlit-alpha rather than a heavy PBRMaterial [P, forum 63619, 2026-06-10] | Use NME only for things glTF cannot say (custom shaders), assigned by mesh name in code |
| Lightmaps | Official guided lesson: second UV via Lightmap Pack, bake Diffuse (no colour) in Cycles, export GLB, then "apply the lightmap to every mesh" in code [V, Babylon docs `guidedLearning/lightmaps`] | Lightmap is a code-side assignment in Babylon too |
| Handedness | Loader parents glTF under `__root__` rotated 180 deg on Y, Z scale -1 [V]; docs say do not add another axis flip | Never pre-rotate in Blender to compensate |

## 3. Other Blender to web routes

| Route | What it automates | Cost | Quality ceiling | Notes |
|---|---|---|---|---|
| **Needle Engine** (three.js based, Blender add-on) | 100+ components in a Needle Object panel; save `.blend` and the browser reloads; HDRI exported automatically; **lightmapping**: mark objects `Lightmapped`, Cycles bake with auto-generated lightmap UVs ("no second UV channel needed"), 1024-4096, 128-512 samples, denoise, exported with the scene; progressive LOD (`gltf-progressive`) on build; Needle Cloud upload [V, Needle docs, repo release 5.1.16 2026-10-15] | Commercial licence for some uses [U: not read] | Bake-grade interiors, product shots | Requires Blender 4.5+ (docs: the 5.1+ glTF exporter is "still stabilizing", use 5.0 or LTS), Node 22/24; set View Transform to Standard, not Filmic. Closed-ish pipeline on top of three; fine for fast configurators/interiors |
| `@needle-tools/gltf-progressive` | Standalone: tiny proxy GLB plus streamed LOD meshes/textures; works with plain three, R3F, model-viewer. Vendor claim: 56 MB to 300 KB initial [V doc, claim U] | Free npm | Large scenes | Adds `NEEDLE_progressive`; third-party plugin on three's loader list |
| **Verge3D** (Soft8Soft) | Blender add-on, Puzzles visual scripting, PBR pipeline, Sneak Peek, one-click CDN publish; version 4.13 on site [V, soft8soft.com]. Pricing page 404; edition names Enterprise/Ultimate only [U] | Paid licence | Mature three-based runtime | Locks interactivity in Puzzles, not code |
| **PlayCanvas** | GLB import; engine glb extensions include transmission, volume (asset-viewer example), ior, clearcoat, sheen, specular, anisotropy, iridescence, dispersion, emissive_strength, unlit, lights_punctual, variants, gpu_instancing, draco [V, engine repo `parsers/glb/extensions`] | Free engine; editor tiers [U] | High; strong splat tooling (SuperSplat, splat-transform) [V] | Choose when the team wants an editor and splat-first pipeline |
| **model-viewer** | `ar-modes` webxr, scene-viewer, quick-look; Quick Look builds USDZ on the fly if no `ios-src`; "animations are not yet supported" in auto USDZ; `ar-usdz-max-texture-size`; tone-mapping neutral (default, was ACES before v4.0), aces, agx, reinhard, cineon, linear [V, modelviewer.dev docs; repo v4.4.0 2026-10-09] | Free | PBR product shots, AR | Best "GLB in, AR out" for a product page |
| **Gaussian splats from Blender renders** | BlenderNeRF add-on (Blender >= 4.0): frame subset, train/test cameras, or camera on sphere; writes `transforms_train/test.json` (Instant-NGP or NeRF format) plus optional `points3d.ply` from mesh vertices; 50-150 images, focal 30-70 mm, fixed focal length, avoid motion blur; last push 2024-12-16 [V README]. Paid alternatives (Splatworks writes poses directly, static frame; Datasplat builds COLMAP from a render sequence + camera) [U vendor pages] | GPU training time | Path-traced look with true view-dependent reflections baked into splats; static only, no relighting | Real use: props, product reflections [P, Oryzo in l5]. Runtime: Spark (three, pushed 2026-10-16; .ply/.spz/.splat/.ksplat/.sog) or PlayCanvas. Ship small: compress to SPZ/SOG |
| **Pre-rendered Cycles sequence / video** | Cycles frames to AV1/H.265/WebM or image sequence, scrubbed by scroll or looped; skill already routes this (brief-approach, scroll-video) [V local] | Zero GPU risk, heavy bytes | Highest (true path tracing) | No interaction. Hybrid: video plate plus live light/cursor interaction (Lusion "Redshift video + real-time point light on cursor" [P, l5]) |
| **Hybrid baked + live** | Static world baked in Cycles (one-to-few 2K-4K lightmaps/atlases), dynamic hero live | Moderate | Strongest realism per byte | Andrew Woan's world: Combined bake 4096, EXR to PNG, KTX2 ETC1S `--quality 255` [P, Codrops 2025-04-08, in l5]. Oxyn on discourse: "bake everything... emissive/unlit materials without real time shadows... all the work is mostly done outside three" [P, discourse 89753, 2026-02-10] |

## 4. Design for the web in Blender (what is not already in `blender-export.md`)

**Budgets and density.** Triangles matter far less than textures for file size [P: mjurczyk, 72780]; spend the budget on texel density and draw calls. Decide one texel-density target per object class (hero 1 texel per ~0.5 mm of silhouette-significant surface at planned closest distance, background 4x coarser) and enforce it with the UV Texel Density checker or by a scripted average [U: practitioner convention, not sourced]. Keep per-material 2048 as default, 4096 only for a full-scene bake [P, Woan].

**UV layers.** UV0 = tiling/trim/atlas colour; UV1 = unique non-overlapping 0-1 for lightmap/AO. Export keeps both; the second only reaches a material if a texture references it (UV Map node, `texCoord:1`) [V]. In three the glTF lightmap lands in the AO slot (`aoMap`, `texture.channel=1`); a true `lightMap` must be set in code by material name [V loader; P: ProgressiveLightMap thread requires `uv1`, discourse 87992, 2025-11-07, manthrax]. Never rename UV maps expecting names to carry over; channel index is the contract.

**Atlases.** Each material is a draw call; Babylon docs merged meshes and used a palette texture to cut them [V].

**Names and pivots.** Behaviour in names or `extras`, not hierarchy depth; pivots at hinges for anything code rotates; one root Empty per asset.

**Instancing.** For repeated props: linked duplicates (shared mesh data) as children of one Empty, no children on instances, accept shared materials [V rst]. For material-varied repeats, code with `InstancedMesh`/Babylon instances and per-instance colour. Array modifier ballooning: keep linked-duplicate approach. Skill's `instance` pass in gltf-transform is skipped when animation exists [V asset-pipeline].

**LOD.** glTF has no portable LOD extension in these loaders (Babylon has `MSFT_lod` [V file list]; three has none in core). Options: separate GLBs swapped by distance, `NEEDLE_progressive` via gltf-progressive [V], or gltfpack simplify tiers. Name `Asset_LOD0/1/2` and export separately.

**Animation.** Default mode Actions: only the active action or actions stashed on NLA tracks are exported; unassociated actions are silently skipped [V rst]. Practice: one action per clip, push each to its own NLA track, track name = clip name, then check the resulting names in code. Modes: Actions (default), Active Actions merged, NLA Tracks (strip modifiers), Scene [V]. Since Blender 4.4 slotted actions merge tracks by action, not by name [V]. Sampling: rate 1 is exact, larger rates distort keyframes [V Babylon art-prep]; Force Sampling / Bake for constraints and drivers [B]. Optimise duplicate keyframes (`export_optimize_animation_size`) [B]. Only transforms, pose bones, shape-key values animate by default; material/light/camera needs the Animation Pointer option [V]. Shape keys: `export_apply` kills them [V].

**Camera.** Export only to check FOV; `shots.v1` owns the camera. Three uses vertical FOV [U].

**Lights.** Standard mode writes physical cd/lx and three consumes them unconverted [V line 752]; prefer HDRI plus code lights tuned live.

**Colour.** Blender 5 defaults to AgX; Needle says set Standard to match the browser [V]. One tone map, in the engine.

## 5. Strategies by goal

### 5.1 Max-realism static (hero render feel, no interaction)
1. Prefer **pre-render** if the camera is not user-driven (Cycles stills, loop video or scrub frames). Highest ceiling, lowest runtime risk [V local brief-approach].
2. If the user must orbit slightly: **Cycles Combined bake** per static object group to 2-4 atlases (4096 then downscale, Woan), UV1 non-overlapping, unlit/emissive-style display, KTX2 via gltf-transform, tight HDRI for reflective extras [P].
3. For glass/metal hero: keep live PBR with `transmission + volume + ior`, a PMREM env that matches Blender's HDRI and rotation, sheen/clearcoat where real [V matrix + l5].
4. Optional splat for a reflective prop only [P].
Check: render the same camera in Blender and engine; compare with the preview diff, not by eye.

### 5.2 Interactive hero (one object, user rotation/hover)
Exports: single root, PBR with clearcoat/sheen/transmission as needed, ORM packed, one AO bake, shape keys for morph interaction (no `export_apply`), meshopt + KTX2 downstream. Keep live: hero, env, subtle contact shadow (baked blob under it). Verify second engine only if Babylon is in the stack.

### 5.3 Configurator
- Variants through `KHR_materials_variants` (Babylon native; three needs the three-gltf-extensions plugin, last push 2022-12 [V], so test or implement material swap by name in code).
- Parts as separate nodes with stable ASCII names; shared materials per finish; avoid `join`/`flatten`/`palette` in optimisation [V asset-pipeline].
- Bake AO per part, not per scene, so parts can swap. Lightmaps do not survive reconfiguration (discourse 89753: re-bake on a backend or accept fakery) [P].
- Progressive LOD (`gltf-progressive` or Needle) for dozens of options [V claim U].

### 5.4 Animated story (scroll or timeline)
- Camera and character via NLA clips named per beat; export clips in the Actions mode; verify clip names in code.
- Heavy sims: bake to VAT or shape keys, or pre-render the beat and hybrid it with a live layer [P Lusion, Houdini VAT in l5].
- Material/light animation: Animation Pointer export (Blender) + a three plugin or hand-coded tracks [V/P], or drive in code from `extras`.
- Alternative for photoreal scroll: frame sequence; see scroll-video.

### 5.5 AR
GLB under ~5 MB, basic PBR (base, normal, ORM), metres, model-viewer `ar-modes="webxr scene-viewer quick-look"`; auto USDZ drops animation so supply `ios-src` for animated assets [V]. Test on a real iOS device.

## 6. Pre-export checklist (additions in bold; unchanged items live in blender-export.md)

1. Run `inspect_scene.py`; resolve FAIL.
2. Units/axes/apply scale/doubles/normals/ASCII names/<=4 influences/origin: unchanged.
3. **Material audit**: every shader is Principled fed by Image Texture/RGB/Mapping/UV Map only; extensions intentionally triggered (transmission needs volume for refraction; dispersion needs volume; IOR only written with those; emission >1 triggers strength ext).
4. **Orphan check**: Color Ramp/noise/bump/AO nodes baked out; Sheen BSDF and Hair BSDF replaced.
5. **UV audit**: UV0 for colour, UV1 non-overlapping lightmap; lightmap image wired to `glTF Material Output` Occlusion with UV1 if it must travel in the GLB.
6. **Modifiers**: GN and booleans applied on a copy; shape keys preserved; Array replaced by linked duplicates under one Empty for instancing.
7. **Animation**: actions stashed per clip, NLA track names final, sampling decided, constraints/drivers baked, pointer export only if needed.
8. **Lights/camera**: excluded unless required; HDRI exported separately; tone map decision recorded (Standard vs AgX).
9. **Export a master** (uncompressed, extras on); read the JSON line; diff `extensionsUsed` against section 1.
10. **Validate** (`gltf-transform validate`), open in the target engine and, for Babylon projects, the Sandbox/Inspector; load the real app; run the pixel-parity gate.
11. **Compress once** from the master (meshopt + KTX2 or Blender's gltfpack path), keep the master.

## 7. Route comparison

| Route | Realism ceiling | Interactivity | Bytes | Engine lock-in | Setup effort | Pick when |
|---|---|---|---|---|---|---|
| Pre-rendered Cycles (video/frames) | Highest | None (scrub only) | High, streams well | None | Low | Camera not driven, mobile risk high |
| Baked GLB (unlit lightmap atlases) | Very high | Camera, light hover | Medium (KTX2 atlases) | None (any glTF engine) | High (UVs, bakes) | Interiors, rooms, sets, hero worlds |
| Live PBR GLB (+ env) | High for single objects | Full | Low | None | Low | Product/hero objects, configurators |
| Hybrid (bake world + live hero + video plate) | Very high | Targeted | Medium | None | Highest | Flagship campaign pages |
| Needle Engine | High (bakes) | Full, component-based | Medium + progressive | Needle components | Low-medium | Fast interior/product experiences, Blender-centric teams |
| Verge3D | High | Full via Puzzles | Medium | Verge3D | Low | Paid, no-code interactivity |
| PlayCanvas | High | Full (editor) | Medium | PlayCanvas | Medium | Editor team, splat-first |
| Gaussian splat of a Blender render | Path-traced look, static | Orbit only | Medium | Splat viewer | Medium-high | Reflective prop, scene fragment |
| model-viewer (+USDZ) | Medium-high | Orbit, AR | Low | None | Lowest | Product page with AR |

## Sources

[V] Khronos glTF-Blender-IO (`docs/blender_docs/scene_gltf2.rst`, `exp/material/extensions/`); three r186 `GLTFLoader.js`; Babylon.js loaders `Extensions/` listing and docs (Blender_to_glTF, Exporters/Blender, dccToGltf, lightmaps); BabylonJS/BlenderExporter; Needle docs (Blender index, lightmapping, gltf-progressive); model-viewer docs; PlayCanvas `parsers/glb/extensions`; Khronos `KHR_gaussian_splatting`; BlenderNeRF and Spark READMEs; Blender 5.2.2 operator introspection. [P] discourse.threejs.org 40116, 72780, 84737, 87992, 89753; forum.babylonjs.com 63754, 63619, 63567, 17003; Codrops Woan 2025-04-08 (via l5). [U] Verge3D pricing, Sketchfab limits, Splatworks/Datasplat, Needle licensing, gltfpack bundling, texel-density numbers.
