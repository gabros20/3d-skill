# B3 - Texturing for Blender: AI generation, procedural, UV/bake, agentic pipeline

Researched 2026-10-16. Grades: [V] official/source/introspected, [B] measured, [P] practitioner, [U] unverified.
Introspection and tests: headless Blender 5.2.2 LTS (macOS, Cycles CPU), scratch only. GitHub facts via `gh api` 2026-10-16.

## 0. Bottom line

1. For web/GLB work the highest-value, lowest-risk route is: **generate or fetch a tileable albedo, derive maps, build one Principled material, verify tiling in a Cycles render, bake only when the material is procedural or multi-layer.**
2. **Fetch before generating.** Poly Haven and ambientCG are CC0 and already ship albedo+normal+roughness+AO+height, correctly tiled, de-lit and at known scale [V]. AI generation is for looks no library has.
3. Whole-mesh AI texturing is GPU-heavy (StableGen needs ComfyUI + NVIDIA 8-16 GB; Hunyuan3D-Paint 21 GB) or a paid API (Meshy/Tripo). None is a laptop-local default on this Mac. Treat them as optional, user-provisioned lanes.
4. Licence traps: **CHORD is research-only; Hunyuan3D excludes EU/UK/South Korea and has a 1M-MAU clause; nvdiffrast/nvdiffrec are non-commercial.** Detail in section 1.6.
5. `Material.use_nodes` emits a DeprecationWarning "expected to be removed in Blender 6.0" in 5.2.2 [B]. New scripts should not rely on it silently; guard it (see 2.5).

## 1. AI texture generation

### 1.1 The user's `generate-image` skill as a texture source

Read `~/.claude/skills/generate-image/SKILL.md` + `references/prose-recipes.md` (2026-10-16) [V].

| Fact | Consequence for textures |
|---|---|
| Backend: Codex CLI built-in `gpt-image-2` via `scripts/gen-image.sh <spec|-> <out.png> [-i refs] [-m model]`; prompt must start `$imagegen` | Works headless; output is a PNG you must then post-process |
| Format map: "textures, backgrounds" -> **prose**, stacked descriptors; template ends with `[seamless? for tileable textures], [aspect ratio]` | Use prose, not JSON, for albedo. Use JSON only for a multi-cell *sheet* (e.g. 4 variants labelled in a grid) |
| Edits: `-i ref.png` + instruction | Use for variants and for "remove baked shadows" de-lighting passes (quality varies [U]) |
| No documented size/tile guarantee; only `aspect ratio` in prompt | **Do not trust "seamless".** Always run the seam test (1.2) and repair. |
| Agentic (Codex/Grok CLI), slower than a direct API | Fine for 1-4 textures; for batches use the OpenAI/xAI REST endpoints the skill mentions |

Texture prompt shape that fits the skill's own recipe [P, untested here - not run to avoid spending plan usage]:

```
$imagegen Top-down orthographic photograph of <material>, flat even diffuse lighting,
no shadows, no highlights, no perspective, no vignette, no borders, no text,
uniform detail across the whole frame, seamless tileable texture, <colour + wear + scale cue
e.g. "pebble size about 3 cm">, square 1:1, 2048x2048. Save as albedo_raw.png in cwd.
```
Negative-type clauses go in the same sentence (the skill notes `negative_prompt` is mainly for photoreal; here the "no shadows/no highlights" clauses do the de-lighting job). Ask for **flat, shadowless, top-down**; that is the single biggest quality lever because baked lighting is the main defect (1.5).

Other generators the skill lists (Flux, SDXL, Midjourney, Imagen) are interchangeable: only the prompt wrapper changes (`references/model-notes.md`). ElevenLabs `creative_generate_image` is also available in this environment as a non-Codex route [V, tool list].

### 1.2 Making an image tile

| Technique | How | Verdict |
|---|---|---|
| **Check first** | Seam ratio = mean abs diff between opposite edges / mean abs neighbour-pixel diff. ~1.0 means the edge looks like any interior line. | [B] Tested: smooth non-tiling field scored 14.9; after cross-fade 1.12. |
| **Cross-fade with half-offset copy** (no AI) | `out = a*W + roll(a, (h/2,w/2))*(1-W)`, `W` = separable sin^2 window (0 at edges, 1 at centre). | [B] Works for noisy/organic materials (stone, soil, fabric). Ghosts large features (planks, bricks, logos). 5 lines numpy. |
| **Offset + inpaint** | Roll image by half in both axes, mask the cross-shaped seam, inpaint (gpt-image edit with `-i`, or SD/Flux inpaint), roll back. | [P] Best general quality; needs a mask tool. Re-run seam test after. |
| **Circular-padding diffusion** | Diffusion whose conv layers use circular padding (ComfyUI "seamless tile" custom nodes; Dream Textures "Seamless" option). | [P] Tiles by construction but needs a local SD/Flux stack. Dream Textures README documents the Seamless option [V github.com/carson-katri/dream-textures, 2026-10-16]. |
| **Tiled-diffusion / MultiDiffusion with wrap** | Same idea at inference time. | [U] not verified for current model generations. |
| **Direct visual check in Blender** | Plane 1x1 m, Mapping Scale 3x3 (Repeat extension), render top-down; look for grid lines and repeated "landmark" features. | [V] Image Texture node `extension` enum: REPEAT/EXTEND/CLIP/MIRROR; `projection`: FLAT/BOX/SPHERE/TUBE [B introspected]. |

Repetition (not just seams) is the second trap: even a perfectly tiling image shows a visible lattice when a distinctive blemish repeats. Mitigations: break up with a low-frequency noise mask driving a second, differently-scaled copy of the texture (the "texture bombing"/two-scale mix), or use `BOX` projection with blend. See 2.3.

### 1.3 Deriving PBR maps from an albedo

| Tool | Status 2026-10-16 | Licence | Notes |
|---|---|---|---|
| **DeepBump** (Blender add-on; colour -> normal, normal -> height, normal -> curvature, 256-px model + upscale) | Last push + release `v8` 2025-03-17; open issues #48, #52, #56 report onnxruntime crashes on Blender 4.3/4.5/5.x (Windows) [V github.com/HugoTini/DeepBump, `gh api`] | GPL-3.0 (weights shipped, training code not) | Has a `cli.py` (documented in `cli.md`) usable outside Blender. Treat as unreliable inside Blender 5.x; try the CLI first. Not tested here. |
| **Materialize** (standalone Unity app: height/normal/metal/smooth/AO from one image) | Repo pushed 2024-06-24, no GitHub releases [V gh api] | GPL-3.0 | GUI-only, not scriptable. Human lane. |
| **NormalMap-Online** | Web tool, browser only [U status] | n/a | Human lane; not agent-usable. |
| **Pure numpy height -> normal** | [B] Tested: `n = normalize(-dx*s, -dy*s, 1)*0.5+0.5` with `np.roll` for wrap (keeps tiling). Output mean RGB (0.50, 0.50, 0.86) at s=2 on noise. | none | Needs a height map. A luminance-as-height shortcut works for rough stone/bark, fails for printed patterns. |
| **Ubisoft CHORD** (SIGGRAPH Asia 2025, albedo/normal/height/roughness/metalness estimation for *generated* tiles; ComfyUI node `ubisoft/ComfyUI-Chord`, pushed 2026-06-23) | arXiv 2509.09952 [V github.com/ubisoft/ubisoft-laforge-chord] | **Ubisoft ML License, Research-Only - Copyleft: "Commercial use is strictly prohibited"** [V LICENSE text read] | Weights need Hugging Face login + acceptance. **Do not use for client/commercial output.** |
| **StableGen PBR decomposition** (Marigold intrinsic) | In StableGen v0.3.x feature list [V] | Marigold licence not listed on page [U] | Only inside StableGen (see 1.4). |
| **Roughness/AO/metal heuristics** | Roughness = inverted/contrast-stretched luminance ranged ~0.4-0.9; metallic = 0 unless the material is bare metal; AO from Cycles bake. | - | [P] Cheap and usually better than a bad ML guess. **Metallic must be a mask of 0/1, not a gradient**, for non-metals. |

Recommended derivation order for an agent: library PBR set if one exists (CC0) -> else generated albedo + numpy height (luminance) -> normal (numpy) -> roughness heuristic -> AO from a Cycles bake only if the material is applied on real geometry. Normal strength is the tuning knob; verify in a render.

### 1.4 Whole-mesh / projection texturing

| Route | Status (2026-10-16) | Licence | Requirements | Agent fit |
|---|---|---|---|---|
| **StableGen** (Blender add-on; ComfyUI backend; SDXL / FLUX.1-dev / Qwen Image Edit texturing; TRELLIS.2 image/text -> textured mesh; multi-camera projection -> "Bake Textures" to UV; PBR via Marigold; export GLB) | v0.3.1 released 2026-06-12, repo pushed 2026-10-16, 952 stars [V gh api + README] | GPL-3.0; TRELLIS.2 MIT; nvdiffrast/nvdiffrec **NVIDIA non-commercial** (only TRELLIS.2 "Native" texture mode); FLUX.1-dev has its own licence | Blender **4.2-4.5 (OSL) or 5.1+ (GPU raycast)**; "Blender 5.0 is not supported"; ComfyUI server; NVIDIA CUDA, 8 GB (SDXL) / 16 GB+ (FLUX, Qwen); macOS Apple Silicon listed; 10-50 GB disk | README documents UI workflow, Folder Batching and Scene Queue **inside Blender's UI**; no documented Python API or headless mode [V]. So: human-in-the-loop lane, not an agent script. 5.2 LTS compatibility not stated (README says 5.1+) [U] |
| **Dream Textures** (SD in Blender: text->image, Seamless, depth-to-image "Project Dream Texture", upscaling) | Latest tagged release `0.4.1` 2024-08-26; commits continue (2026-09-17, 2026-09-15 fixing a baked-UV bug) [V gh api] | GPL-3.0 | >4 GB VRAM recommended; Blender-version matrix not stated on README [U] | Old SD-era models; prefer ComfyUI+modern checkpoints. Low priority. |
| **ComfyUI-Blender** (alexisrolland; add-on turns a ComfyUI API-format workflow into a Blender panel and runs it on a ComfyUI server) | pushed 2026-08-21, 211 stars, GPL-3.0; supports Blender 5.0 from add-on v4.0.0 [V README] | GPL-3.0 | ComfyUI latest (node schema v3), `--listen` for remote | Good bridge: any ComfyUI texture workflow (seamless diffusion, CHORD-like, upscalers) becomes callable. Whether outputs land as Blender images is not stated on README [U]. |
| **AIGODLIKE ComfyUI-BlenderAI-node** | pushed 2025-11-28, 1562 stars, GPL-3.0 [V gh api] | GPL-3.0 | ComfyUI node editor embedded in Blender | Not updated in the last ~11 months; verify against 5.x before recommending [U]. |
| **Hunyuan3D-2.1 Paint** (PBR multiview texturing, 2B) | repo pushed 2025-10-17 [V] | Tencent Hunyuan 3D 2.1 Community License: **"does not apply in the EU, UK and South Korea"**, >1M MAU needs a separate licence, outputs may not be used to improve other AI models [V LICENSE read] | 21 GB VRAM texture, 29 GB both [V README]; custom rasterizer compile | Not a Mac laptop lane; geographic exclusion matters for EU clients. |
| **Meshy Retexture API** | `POST /openapi/v1/retexture`; input `model_url` (glb/gltf/obj/fbx/stl, <=400 MB) or `input_task_id`; style = `text_style_prompt` (<=800 chars), `image_style_url`, or `multiview_image_urls`; options `ai_model` (meshy-6-lite/meshy-6/meshy-7), `enable_pbr`, `enable_original_uv`, `texture_resolution` 2k/4k/8k, `remove_lighting`; outputs glb/fbx/obj/usdz + `texture_urls` base_color/metallic/normal/roughness [V docs.meshy.ai/en/api/retexture, 2026-10-16] | Credits (example task consumed 10); licence/commercial terms not on that page [U] | API key, paid | **Best agent-scriptable whole-mesh route.** `enable_original_uv` keeps your UVs, which you want. `remove_lighting` addresses baked-light. |
| **Tripo texture task** | `POST /v3/models/texture` on an existing task id, `pbr` (default true), `texture_quality` standard/detailed, optional `texture_prompt` [V developers.tripo3d.com/en/docs/models-texture, via search 2026-10-16; field names differ across wrappers, trust official page] | Credits; terms not read [U] | API key | Accepts a prior Tripo task id, so it retextures Tripo-generated geometry more easily than your own mesh [U]. |
| **TEXTure / Text2Tex / Paint3D** | TEXTurePaper repo MIT, last push 2023-12-08 [V]; Text2Tex/Paint3D repos not located by `gh api` guesses [U] | varies | research code, GPU | Research references, not production routes. |

### 1.5 Projection painting from a generated image (manual route, scriptable)

1. Generate the image **from the intended camera** (render the clay mesh with `render_shots.py`, feed as depth/reference via `-i`, ask the image model to restyle).
2. Project: `bpy.ops.uv.project_from_view` has params `orthographic`, `camera_bounds`, `correct_aspect`, `clip_to_bounds`, `scale_to_bounds` [B introspected] but needs a 3D-viewport context (not available `-b` without override) [U not run]. Headless alternative: **shader-space projection** - Texture Coordinate `Camera` output -> Image Texture, then bake DIFFUSE/EMIT to the UV image (2.4).
3. Occlusion: projection paints through geometry. Only single-view-visible surfaces are correct; use several cameras with blend weights (what StableGen automates) or keep to near-planar shots.
4. Bake to UV, then inpaint holes at UV level.

### 1.6 Licence quick table (commercial use of generated textures)

| Item | Commercial? |
|---|---|
| gpt-image-2 / Codex outputs | Governed by OpenAI/ChatGPT terms [U not read] |
| Poly Haven, ambientCG | **CC0, commercial OK, no attribution required** [V polyhaven.com/license; docs.ambientcg.com/license]. Poly Haven ToS forbids scraping; API under separate terms |
| DeepBump / Materialize / StableGen / Dream Textures code | GPL-3.0 (applies to the add-on code, not to images you make) [V] |
| StableGen + TRELLIS.2 Native mode | nvdiffrast/nvdiffrec non-commercial [V] |
| CHORD | **Research only** [V] |
| Hunyuan3D 2.1 | Territory-limited, MAU clause [V] |
| FLUX.1-dev | Own licence [V StableGen README says so; terms not read] - check before client work |

### 1.7 Quality traps (all lanes)

| Trap | Symptom | Fix |
|---|---|---|
| **Baked lighting in albedo** | Gradients/shadows rotate wrongly under scene light, tile shows a "lamp" | Prompt flat/shadowless; high-pass filter (blur radius ~ 1/4 image, subtract, add mean); `remove_lighting` (Meshy); StableDelight/Marigold-style de-lighting in StableGen [V listed] |
| **Seams / lattice** | Visible grid | 1.2 |
| **Scale / texel density** | Pebbles the size of boulders | State physical scale in the prompt; set Mapping `Scale` so 1 tile = known metres (e.g. 1 tile = 1 m -> UV scale 1/1 on a 1 m plane); keep one density per scene (see 3.3) |
| **Colour space** | Washed-out/dark or wrong normals | Albedo/emission = **sRGB**; roughness, metallic, AO, height, **normal = Non-Color** [B: `images.new` defaults to sRGB; set `img.colorspace_settings.name='Non-Color'` for data]. Baked normal/roughness images created with `images.new` must be set to Non-Color explicitly. |
| **Normal map convention** | Bumps look inverted | glTF/three.js and Blender = OpenGL (+Y up); DirectX maps (green flipped) from Unreal/Substance exports need the green channel inverted [P] |
| **Low resolution upscaled** | Mushy detail | Upscale with a real upscaler (Real-ESRGAN etc., [U] not tested) *before* deriving normals |
| **8-bit height** | Terracing in normals | Derive normals from the float image, or 16-bit |
| **Metallic gradients** | Dirty halos | Binary masks |
| **Procedural look-alike** | AI "wood" that isn't plank-structured | Prefer procedural (section 2) for engineered/regular materials |

## 2. Procedural texturing in Blender

### 2.1 Nodes that exist in 5.2.2 [B introspected `bpy.types`]

Texture nodes: Brick, Checker, Environment, Gabor, Gradient, IES, Image, Magic, Noise, Sky, Voronoi, Wave, White Noise. Utility: Bevel (inputs Radius, Normal), Ambient Occlusion, Geometry (outputs include **Pointiness**, Parametric, Random Per Island), Bump, Displacement, Vector Displacement, Normal Map, Mapping, Texture Coordinate. Noise node inputs: Vector, W, Scale, Detail, Roughness, Lacunarity, Offset, Gain, Distortion; `noise_type` enum: MULTIFRACTAL, RIDGED_MULTIFRACTAL, HYBRID_MULTIFRACTAL, FBM, HETERO_TERRAIN. Note: **Musgrave is gone** (merged into Noise since 4.1) and **Gabor exists**. Principled BSDF inputs begin Base Color, Metallic, Roughness, IOR, Alpha, Thin Wall, Normal, Weight, Diffuse Roughness, Subsurface Weight/Radius/Scale ... [B].

### 2.2 Recipes (node graph, name = what to link)

| Material feature | Recipe |
|---|---|
| **Base variation** | Noise (Scale 3-8, Detail 8-12, Roughness 0.6) -> Color Ramp (2-3 stops) -> Mix over two colours. A second Noise at ~25x scale at low strength adds grain. |
| **Cellular (stone, scales, cracks)** | Voronoi (`F1`/`Smooth F1` for cells, `Distance to Edge` for cracks) -> Color Ramp (sharp stops) -> Bump height. Randomised Color output feeds per-cell colour variation. |
| **Wood/marble banding** | Wave (Bands/Rings, Distortion 2-6, Detail 2) with a Noise added to Vector input. |
| **Edge wear** | `Bevel` node (Radius 0.02-0.05) -> Vector Math **Dot/Subtract vs. the true Normal** -> Color Ramp -> mask. Works in **Cycles only** [P]. Alternative: Geometry `Pointiness` (needs dense mesh; Cycles only) or AO node `Inside` for cavities. |
| **Dirt/grime** | AO node (`Inside` off, Distance 0.2-0.5) multiplied by a large-scale Noise -> Color Ramp -> Mix(dark brown, base). Concentrated in crevices: invert AO. |
| **Anti-tiling for any image** | Two Image Texture nodes at different Mapping scale/rotation, mixed by a low-frequency Noise mask. |
| **Triplanar / box mapping** | Image Texture `projection='BOX'` with `projection_blend` 0.2 on Object coordinates (no UVs needed) [V: BOX enum present]. |
| **Texture coordinates** | `Object` for non-deforming props (stable under UV edits); `Generated` for bounding-box 0-1; `UV` for anything that will be baked or exported; `Camera`/`Window` only for screen-space or projection tricks. |

All of these mostly use shader nodes that **glTF cannot export** (the exporter only understands image-textured Principled inputs). Anything procedural must be baked before export (2.4, `blender-export.md`).

### 2.3 Libraries and tools (Substance-free)

| Resource | Notes |
|---|---|
| **Poly Haven** | CC0, textures include diffuse, nor_gl, rough, ao, disp, arm packs; API api.polyhaven.com under separate terms; no scraping [V]. |
| **ambientCG** | CC0; API v1/v2/v3 (`/assets`, `/categories`, `/collections`, `/rss` in v3) [V docs.ambientcg.com/license]. |
| **Material Maker** | MIT, v1.7 released 2026-07-14, pushed 2026-10-16, 5996 stars [V gh api]. Node-based procedural PBR authoring that exports PNGs / game-engine formats; headless/CLI export mode exists [U not verified in this lane]. Best Substance substitute for tileable, parametric materials. |
| **Blender's own** | Procedural graph + bake = the Substance-free workflow; Geometry Nodes can drive attributes feeding materials (lane B1). |

### 2.4 Baking procedural/complex materials to images (for web)

Verified end-to-end headless [B] on a cube with a noise-driven Principled material:

```python
import bpy
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 8
# 1. UVs (smart_project needs edit mode)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
# 2. target image + ACTIVE Image Texture node in the material (required; bake writes to the active image node)
img = bpy.data.images.new("bake_albedo", 2048, 2048)           # sRGB default
n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img
mat.node_tree.nodes.active = n
# 3. bake
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=16,
                    margin_type='EXTEND', use_clear=True)         # albedo: 0.1 s for 512^2
# data maps: create a NEW image, set Non-Color, re-point the node, then
img_r = bpy.data.images.new("bake_rough", 2048, 2048); img_r.colorspace_settings.name = 'Non-Color'
n.image = img_r
bpy.ops.object.bake(type='ROUGHNESS', margin=16, use_clear=True)
img.save_render("albedo.png", scene=sc)   # honours scene.render.image_settings (set PNG / RGB / 8)
```
Notes: `bake` types introspected: COMBINED, AO, SHADOW, POSITION, NORMAL, UV, ROUGHNESS, EMIT, ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION. `pass_filter` set: NONE, EMIT, DIRECT, INDIRECT, COLOR, DIFFUSE, GLOSSY, TRANSMISSION. **There is no METALLIC bake type**: bake metallic by routing it to an Emission shader and baking `EMIT` [P, standard trick, not run]. Albedo = `DIFFUSE` with `pass_filter={'COLOR'}` only. Use `save_render` (not `img.save()`) when you want colour-managed 8-bit PNG [P].

## 3. UV, painting and baking essentials

### 3.1 Operators verified by introspection (5.2.2) [B]

| Operator | Parameters (defaults) |
|---|---|
| `uv.smart_project` | `angle_limit` 1.152 rad (66 deg), `margin_method` SCALED/ADD/FRACTION, `rotate_method` AXIS_ALIGNED(_X/_Y), `island_margin` 0.0, `area_weight` 0.0, `correct_aspect` True, `scale_to_bounds` False |
| `uv.unwrap` | `method` ANGLE_BASED/CONFORMAL/MINIMUM_STRETCH, `fill_holes`, `margin` 0.001, `margin_method`, `use_subsurf_data`, `iterations` 10, `use_weights`/`weight_group` |
| `uv.pack_islands` | `udim_source` CLOSEST_UDIM/ACTIVE_UDIM/ORIGINAL_AABB/CUSTOM_REGION, `rotate` True, `rotate_method` ANY/CARDINAL/AXIS_ALIGNED..., `scale` True, `merge_overlap`, `margin` 0.001, `margin_method`, `pin`/`pin_method`, **`shape_method` CONCAVE/CONVEX/AABB** |
| `uv.average_islands_scale` | `scale_uv`, `shear` - run before pack for uniform texel density |
| `uv.seams_from_islands` | `mark_seams`, `mark_sharp` |
| `uv.lightmap_pack` | `PREF_PACK_IN_ONE`, `PREF_MARGIN_DIV` 0.1, `PREF_BOX_DIV` 12 |

All need the object in Edit Mode with faces selected (the way the smart_project test ran). `bpy.ops.object.bake` params: `type, pass_filter, filepath, width, height, margin(16), margin_type(ADJACENT_FACES/EXTEND), use_selected_to_active, max_ray_distance, cage_extrusion, cage_object, normal_space(OBJECT/TANGENT), normal_r/g/b, target(IMAGE_TEXTURES/VERTEX_COLORS), save_mode, use_clear, use_cage, use_split_materials, use_automatic_name, uv_layer`.

### 3.2 Which unwrap

| Situation | Choice |
|---|---|
| Hard-surface props, quick | `smart_project(angle_limit=66deg, island_margin=0.02)` then `pack_islands(margin=0.005)` |
| Organic/character | Mark seams manually (or `uv.seams_from_islands` after a smart pass) then `uv.unwrap(method='ANGLE_BASED')`; check stretch visually |
| Tileable material on a plane/box | **No UVs needed** - Object coords + BOX projection |
| Lightmap | `lightmap_pack` - not for web unless baking AO |

Packing: since Blender 4.x the packer has concave shape support (`shape_method`), `merge_overlap` for mirrored halves, and pin options [B introspected]. Run `average_islands_scale` first when texel density must be uniform.

### 3.3 Texel density targets for web [P unless noted]

| Asset | Texture size | Notes |
|---|---|---|
| Hero product / close-up | 2048 or 4096 (GPU mem 4096^2 RGBA ~ 64 MB uncompressed; use KTX2 in export) | Check with `budget` in `blender-export.md` |
| Mid-ground prop | 1024-2048 | |
| Background / tile | 512-1024 | Tileables should be power-of-two |
Target consistent px/cm across assets in one scene (e.g. 512-1024 px/m for hero props); the rule is *consistency*, not a number.

### 3.4 UDIMs

Blender supports UDIM tiles for authoring (`uv.pack_islands udim_source` options reflect it), but **glTF/web has no UDIM**: three.js loads one UV 0-1 space. For web, stay in 0-1; split large assets into several materials instead [P]. UDIM is for film/DCC interchange only.

### 3.5 Texture paint via Python

Python can create, fill, save and bake images but interactive `texture_paint` strokes need a viewport. For agents: `bpy.data.images.new(name, w, h, alpha, float_buffer)`; write pixels via `img.pixels.foreach_set(np_array.ravel())` (flat float RGBA, 0-1, rows bottom-to-top); then `img.update()`. Tested pixel read via `img.pixels[:]` [B]. Pack with `img.pack()` or save with `save_render`.

### 3.6 Selected-to-active baking (high -> low poly)

[B] Verified headless on a displaced 64x32 sphere (hi) -> 16x8 sphere (lo), tangent-space normal bake:
```python
hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo   # lo MUST be active
# lo has a material whose ACTIVE node is an Image Texture node holding a Non-Color image
bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT',
    use_selected_to_active=True, cage_extrusion=0.15, max_ray_distance=0.3,
    margin=8, margin_type='EXTEND', use_clear=True)
```
Result mean RGB (0.500, 0.500, 0.985): the flat-blue normal baseline, i.e. rays hit and returned valid tangent normals. Rules: the low-poly needs UVs; extrusion/ray distance must cover the max hi-lo gap or you get holes/cage artefacts; use `use_cage` + `cage_object` for tight control; `margin` 8-16 px with `EXTEND` avoids edge bleeding on mip-mapped GLB textures.

## 4. Recommended agentic pipeline

```
brief -> [G1 library check] -> generate/fetch albedo -> [G2 tile] -> derive maps -> [G3 data]
 -> build Principled -> [G4 render check] -> bake if needed -> [G5 export check] -> GLB
```

| Step | Procedure | Gate (fail = stop and fix) |
|---|---|---|
| 0. Brief | Material, physical scale (m per tile), target size, hero vs background, commercial? | Commercial flag decides allowed tools (1.6) |
| 1. Source | Query Poly Haven/ambientCG first. If no match, `generate-image` prose prompt (1.1) at 2048^2. | **G1:** CC0 set exists? use it, skip AI |
| 2. Tile | Seam ratio (1.2). If > ~1.3, cross-fade or offset-inpaint, re-measure. | **G2:** ratio <= ~1.3 and 3x3 preview shows no lattice |
| 3. De-light | Reject images with strong gradient (low-frequency luminance std high); high-pass or regenerate | **G3a:** flat luminance |
| 4. Maps | Height (luminance or library), normal via numpy `roll` (tile-safe), roughness heuristic, metallic 0 | **G3b:** colour spaces set: albedo sRGB; others Non-Color |
| 5. Material | Principled: Base Color <- albedo; Roughness/Metallic <- Non-Color images; Normal <- Normal Map node (`Strength` 0.5-1) <- normal image; Mapping node Scale = 1/physical_size | - |
| 6. Render check | Plane + sphere, Cycles 32-64 samples, camera at design distance; render two views | **G4:** no visible tiling grid, scale matches real-world reference, no inverted normals. Look at the PNG |
| 7. Bake (only if procedural / multiple layers / projection) | Section 2.4 / 3.6 with 16 px margin | **G5a:** bake mean not 0/NaN, no black holes; texel size per 3.3 |
| 8. Export | Use skill's `export_web.py`; glTF reads Principled image links only | **G5b:** re-import GLB in headless Blender, check images present and normal slot Non-Color |

Failure modes seen or predicted: bake without an active image node -> "no active image" error; `images.new` default sRGB on data maps -> washed normals (set Non-Color); selecting hi but leaving lo inactive -> bake fails; AI "seamless" image not tileable -> lattice; metallic from heuristic -> halos; DeepBump import crash on 5.x -> use numpy or CLI; running GPL/non-commercial tools into a commercial deliverable.

Whole-mesh AI branch (optional): brief mentions "texture this existing mesh from a prompt" -> if the user has an API key: Meshy Retexture with `enable_original_uv=true`, `enable_pbr=true`, `remove_lighting=true`, `texture_resolution="2k"`, then pull `texture_urls` and run G4/G5. If the user has an NVIDIA ComfyUI server: StableGen manually (human in loop). Else: stay with section 4 main path.

## 5. Open items [U]

- `generate-image` seamless success rate and max resolution not measured (would spend plan usage).
- StableGen on Blender 5.2 LTS (README states 5.1+; 5.0 unsupported).
- DeepBump CLI functionality on Apple Silicon.
- Material Maker headless export flags.
- Meshy/Tripo commercial terms and exact credit prices.
- Metallic-via-EMIT bake and `uv.project_from_view` headless context were not executed.

## Sources
gh api repos: sakalond/StableGen, carson-katri/dream-textures, HugoTini/DeepBump, BoundingBoxSoftware/Materialize, RodZill4/material-maker, Tencent-Hunyuan/Hunyuan3D-2.1, ubisoft/ubisoft-laforge-chord, ubisoft/ComfyUI-Chord, alexisrolland/ComfyUI-Blender, AIGODLIKE/ComfyUI-BlenderAI-node, TEXTurePaper/TEXTurePaper (all 2026-10-16). Raw LICENSE files of Hunyuan3D-2.1 and CHORD (2026-10-16). https://github.com/sakalond/StableGen; https://github.com/HugoTini/DeepBump; https://github.com/carson-katri/dream-textures; https://docs.meshy.ai/en/api/retexture; https://developers.tripo3d.com/en/docs/models-texture; https://polyhaven.com/license; https://docs.ambientcg.com/license/; ~/.claude/skills/generate-image/SKILL.md and references. Blender claims: headless 5.2.2 LTS introspection and bake runs, 2026-10-16.
