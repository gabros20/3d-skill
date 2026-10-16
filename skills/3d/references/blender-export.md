# Blender Export

Purpose: Export a web-ready, uncompressed GLB (or USDZ) from Blender without silent losses, then hand off.

Read when:
- Exporting from Blender for three.js, R3F, Babylon or AR; "materials lost on export", "flat in three.js", "model is just the base mesh", lights too bright.

Skip when:
- A GLB exists and needs compression, validation or budgets (→ [asset-pipeline](asset-pipeline.md)).

Inputs:
- The `.blend`, target goal (table below), budgets ([shared-performance](shared-performance.md)), `inspect_scene.py` report.

Produces:
- `.3d/versions/vNNN/<name>.glb` (uncompressed) plus a result JSON line.

## Contents

- Strategy by goal · Pre-export checklist · Run · Axes · Settings · Modifiers and instancing · Material Output group · What breaks · USDZ

## Strategy by goal

| Goal | Route |
|---|---|
| Max-realism static | Prefer pre-rendered stills or frames (Cycles). If the user may orbit a little: Cycles Combined bake per static group to 2–4 atlases ([blender-uv-bake](blender-uv-bake.md)); glass and metal stay live PBR with env |
| Interactive hero | One root, live PBR (clearcoat, sheen, transmission as needed), ORM packed, one AO bake, shape keys for morphs (no `export_apply`), a baked contact blob; compress downstream |
| Configurator | Parts as separate nodes with stable ASCII names, shared material per finish, `KHR_materials_variants` (Babylon native; three needs a plugin or swap by name), AO baked per part; lightmaps do not survive reconfiguration; never join/flatten/palette |
| Animated story | Clips as NLA tracks or actions named per beat; bake sims to shape keys or vertex textures, or pre-render the beat and layer live; verify clip names in code |
| AR | GLB ≤ 5 MB, basic PBR, metres; USDZ drops animation, supply it separately; see USDZ |

Babylon: glTF is the only Blender route; the official `.babylon` exporter is frozen (last commit 2023, built for Blender 3.3).

## Pre-export checklist

1. `inspect_scene.py`: fix FAIL, resolve or justify warnings.
2. Metres at unit scale 1.0 (the exporter ignores unit scale); rotation and scale applied; doubles removed; normals fixed; ASCII names without spaces or dots; no negative scale; ≤ 4 skin influences; prop origin at base.
3. Every material is Principled fed by Image Texture / RGB / UV only; Color Ramp, noise, bump, Sheen BSDF and Hair BSDF baked or replaced ([blender-shading](blender-shading.md), [blender-uv-bake](blender-uv-bake.md)).
4. Volume, thin film, dispersion: add the Material Output group (below).
5. GN and booleans handled per the modifier rules; Array replaced by linked duplicates under one Empty.
6. Animation: actions per clip, constraints and drivers baked ([blender-animation](blender-animation.md)), names final; skinned meshes: DEF-only skeleton ([blender-rigging](blender-rigging.md)).
7. Decide lights and cameras (default exported), light units (COMPAT), and backface culling per material.
8. Export the master, read the JSON line, diff `extensionsUsed` against what you intended.
9. `gltf-transform validate`, open it in the target engine, run the pixel-parity gate ([shared-verification](shared-verification.md)); compress once from the master.

## Run

Run from the project root, on an export copy, headless, never saving the `.blend` afterwards:

`Blender -b scene.blend --factory-startup --python-exit-code 1 --python <skill>/assets/blender/export_web.py -- --out .3d/versions/v001/hero.glb [--root HeroRoot] [--apply auto|none|all] [--images webp] [--lighting compat|spec|raw] [--gn-instances] [--cull-backfaces] [--no-lights] [--no-cameras]`

The JSON line (the one starting `{`) reports bytes, counts (meshes, materials, images, animations, cameras, lights, `double_sided`, `node_names`), `extensionsUsed`, `applied`, `skipped`, `warnings`, `dropped_kwargs`.

## Axes

Blender is Z-up, front toward -Y; glTF, three.js and `shots.v1` are Y-up. Model "up" along Blender +Z and "front" facing Blender -Y; `export_yup=True` converts, so a chip lying flat in Blender lies flat in three.js. Never pre-rotate the model to compensate.

## Settings

Params drift between versions. `export_web.py` introspects `bpy.ops.export_scene.gltf.get_rna_type().properties`, passes only supported kwargs and reports the rest in `dropped_kwargs`; do the same in custom scripts.

| Setting | Script default and why |
|---|---|
| `export_format`, `export_yup` | `GLB`, True |
| `export_apply` | False; modifiers are applied per modifier instead |
| `use_selection` | only with `--root`; never the whole scene by habit |
| `export_lights`, `export_cameras` | True (the operator default is False: set them or get neither). Lights are written as `KHR_lights_punctual`, marked required: strip them for minimal viewers |
| `export_import_convert_lighting_mode` | `COMPAT` (W/4π). Measured on a 1000 W point light: `SPEC` (operator default) writes 54,351 cd and `RAW` 1000, both blown out in three and Babylon (frame error vs Cycles 49 and 42 /255); `COMPAT` writes 79.58 (error 17, floor luminance within 3%). Neither engine rescales for exposure |
| `export_image_format` | `AUTO` or `WEBP` (no fallback; smaller download, same VRAM) |
| compression | off here (D5); compress downstream, never both Draco and meshopt |
| `export_extras`, `export_gpu_instances`, `export_gn_mesh` | True |
| `export_vertex_color` | enum on 5.x (not `export_colors`) |

- Backface culling: every material exports `doubleSided: true` unless Backface Culling is on in Blender. That costs fill rate; set it per material on closed meshes (`--cull-backfaces` does all of them).
- Shadows are not in glTF: none appear in three or Babylon unless the runtime sets them ([threejs-lookdev](threejs-lookdev.md)); this is the largest visual gap on floors.
- `KHR_materials_diffuse_transmission` is not exported (thin translucency: fake with alpha, thin transmission or a baked map).
- Blender 5.2 has gltfpack options (`export_use_gltfpack`, `export_gltfpack_*`) but does not bundle the binary and does not read PATH: it needs the add-on preference "Path to gltfpack" (`io_scene_gltf2` preferences `gltfpack_path_ui`); empty gives `PermissionError`. Use it only as a convenience; keep the master and compress per [asset-pipeline](asset-pipeline.md).

## Modifiers and instancing

- `export_apply=True` drops shape keys on the whole export. Apply Geometry Nodes, Boolean, Bevel, Mirror, Solidify and Subsurf on the copy or their result is lost (an unapplied GN asset exported its base cube: 12 triangles instead of 768).
- `--apply auto` applies those shape-defining modifiers, keeps Array and Armature, skips meshes with shape keys and linked duplicates (reported in `skipped`). `--apply all` also applies Array; `none` applies nothing.
- GN instances: `--gn-instances` keeps GN unapplied and exports `EXT_mesh_gpu_instancing` (needs `export_gn_mesh` and `export_gpu_instances`; without them the GN-only object is dropped entirely). It hides the instance source objects.
- The instance source object (the cube an Object Info node points at) exports as its own node: `hide_render`, `hide_viewport` and `hide_set` do not exclude it unless `use_visible=True`. A measured scene showed one "long block" in three and Babylon: the leftover source cube sat in a gap of the instance row and fused three cubes. Test-scene cause, not an exporter bug; the script warns about it, and `--gn-instances` removes it.
- Animation key times stay at frame/fps (`export_anim_slide_to_zero` False): the first key is not at 0, harmless.

## Material Output group

Volume (thickness, attenuation), dispersion and iridescence export only through a node group whose name starts `glTF Material Output`, with inputs named exactly `Thickness`, `Dispersion`, `Iridescence Factor`, `Iridescence Thickness Minimum` and `Occlusion` (R channel). Rules measured on 5.2.2:
- Without the group, Volume Absorption and Thin Film export nothing.
- Volume needs Thickness ≠ 0; dispersion needs volume; attenuation distance = 1/density, attenuation colour from the absorption colour.
- Transmission alone gives `KHR_materials_transmission` + `ior`.
`export_web.py` warns when a material has a volume or thin-film setup and no such group.

## What breaks

| Source | Result |
|---|---|
| Procedural textures, Color Ramp, Mix factors | Lost; roughness falls to the socket default |
| Normal Map fed through a Bump node | WebP export can write a texture with no source and GLTFLoader rejects the file |
| Displacement, bump from noise | Not exported; bake a normal map |
| Drivers | Not exported; keyframed actions are |
| Collection instances | Expand to node trees; draw calls multiply |
| Names | Written unchanged; GLTFLoader sanitises on load (spaces → `_`, `[].:/` removed, so `Sphere.003` is `Sphere003` in three) |
| Animation | An action with no armature or object user is skipped; choose `export_animation_mode` deliberately |
| Meshopt or Draco GLB | Lossy, quantised, not for re-editing; Blender 5.2 can import meshopt. Keep the raw GLB master |
| Texture formats | Blender writes PNG, JPEG, WebP only: KTX2 happens downstream |

## USDZ (iOS Quick Look)

1. Prefer converting from the exported GLB per [asset-pipeline](asset-pipeline.md) and the AR notes in [splats-xr](splats-xr.md); Blender's `bpy.ops.wm.usd_export` is the alternative.
2. USD export param names changed in 5.0 (`export_textures` → `export_textures_mode`; `visible_objects_only` removed): introspect the operator.
3. Keep PBR basic (base colour, normal, ORM), textures ≤ 2048, no morph targets, ≤ 5 MB. Verify on a real iOS device.

## Traps

- A GLB that opens in Blender is not proof it loads in three.js.
- Exporting the whole scene by habit ships helpers, lights and hidden junk.
- Spaces and dots in names change after GLTFLoader sanitising and break lookups.
