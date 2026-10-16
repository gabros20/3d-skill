# Blender Export

Purpose: Export a web-ready, uncompressed GLB (or USDZ) from Blender without silent losses, then hand off.

Read when:
- Exporting from Blender for three.js, R3F or AR; "materials lost on export", "flat in three.js", "model is just the base mesh".

Skip when:
- A GLB exists and needs compression, validation or budgets (→ [asset-pipeline](asset-pipeline.md)).

Inputs:
- The `.blend`, budgets ([shared-performance](shared-performance.md)), `inspect_scene.py` report.

Produces:
- `.3d/versions/vNNN/<name>.glb` (uncompressed) plus a result JSON line.

## Steps

1. Inspect: `<skill>/assets/blender/inspect_scene.py -- --json .3d/evidence/scene.json`. Fix FAIL items; resolve warnings or accept them with a reason.
2. Pre-export: model in metres at unit scale 1.0 (the exporter ignores unit scale: 1 BU = 1 m); apply rotation and scale, remove doubles, fix normals, unique ASCII names, no negative scale, at most 4 skin influences, origin at the base for props.
3. Materials: bake or simplify anything outside the Image Texture → Principled chain ([blender-lookdev-render](blender-lookdev-render.md)); or name the material and patch it at runtime.
4. Run from the project root (paths resolve against cwd), on an export copy, headless, never saving the `.blend` afterwards:
   `Blender -b scene.blend --factory-startup --python-exit-code 1 --python <skill>/assets/blender/export_web.py -- --out .3d/versions/v001/hero.glb [--apply auto] [--root HeroRoot] [--images webp]`
5. Read the JSON line: bytes, meshes, materials, images, animations, `extensionsUsed`, `applied`, `skipped`, `dropped_kwargs`.
6. Hand off: `<skill>/scripts/glb-report` for budgets, then compression in [asset-pipeline](asset-pipeline.md). Load the result in the real app before calling it done.

## Axes

Blender is Z-up, front toward -Y; glTF, three.js and `shots.v1` are Y-up. Model "up" along Blender +Z and "front" facing Blender -Y; `export_yup=True` converts, so a chip lying flat in Blender lies flat in three.js. Never pre-rotate the model to compensate.

## Settings that matter

Params drift between Blender versions (meshopt and gltfpack options are present on 5.2). `export_web.py` introspects `bpy.ops.export_scene.gltf.get_rna_type().properties` and passes only supported kwargs, reporting the rest in `dropped_kwargs`. Do the same in any custom script.

| Setting | Rule |
|---|---|
| `export_format` | `GLB` |
| `export_yup` | True (glTF is Y-up) |
| `export_apply` | False; the script applies per modifier instead (below) |
| `use_selection` | True with one root hierarchy (`--root`); never the whole scene by habit |
| `export_cameras`, `export_lights` | False; the runtime owns lights and camera |
| `export_image_format` | `AUTO` (PNG/JPEG as authored) or `WEBP` (no fallback; smaller download, same VRAM) |
| compression | Draco and meshopt off here; compress once downstream (D5), never both |
| `export_extras` | True so custom properties reach `userData` |
| `export_gpu_instances` | True for linked duplicates under one Empty; confirm instances appear in `gltf-transform inspect` |
| `export_vertex_color` | enum on 5.x (not the old `export_colors` bool) |
| `export_import_convert_lighting_mode` | only matters if lights are exported |

## Modifiers: decide per modifier

- `export_apply=True` silently drops shape keys on the whole export. Geometry Nodes, Boolean, Bevel, Mirror, Solidify and Subsurf must be applied on the copy, or their result is lost (`export_gn_mesh` is not a substitute; a measured GN asset exported 2 triangles instead of 2,688).
- `--apply auto` applies those shape-defining modifiers, keeps Array (it balloons size; use linked duplicates plus instances) and Armature, and skips meshes with shape keys (reported in `skipped`).
- `--apply all` also applies Array and the rest; `--apply none` applies nothing.

## What breaks

| Source | Result |
|---|---|
| Procedural textures, Color Ramp, Mix factors | Lost; roughness falls to the socket default |
| Normal Map fed through a Bump node | WebP export can write a texture with no source and GLTFLoader rejects the file |
| Displacement, bump from noise | Not exported; bake a normal map |
| Drivers | Not exported; keyframed actions are |
| Collection instances | Expand to node trees; draw calls multiply |
| Names | Blender writes them unchanged; GLTFLoader sanitises on load (spaces → `_`, `[].:/` removed, so `Sphere.003` is `Sphere003` in three). Use ASCII names without spaces or dots as the code contract |
| Animation | An action with no armature or object user is skipped; choose `export_animation_mode` deliberately |
| Meshopt or Draco GLB | Lossy and quantised, not for re-editing; Blender 5.2 can import meshopt, earlier versions may not. Keep the raw GLB as the master ([asset-pipeline](asset-pipeline.md)) |
| Blender | writes PNG, JPEG, WebP only: KTX2 happens downstream |

## USDZ (iOS Quick Look)

1. Prefer converting from the exported GLB per [asset-pipeline](asset-pipeline.md) and the AR notes in [splats-xr](splats-xr.md); Blender's `bpy.ops.wm.usd_export` is the alternative.
2. USD export param names changed in 5.0 (`export_textures` → `export_textures_mode`; `visible_objects_only` removed): introspect the operator.
3. Keep PBR basic (base colour, normal, ORM), textures ≤ 2048, no morph targets, ≤ 5 MB. Verify on a real iOS device.

## Traps

- Spaces and dots in object names change after GLTFLoader sanitising and break lookups by name.
- Exporting the whole scene by habit ships helpers, lights and hidden junk.
- A GLB that opens in Blender is not proof it loads in three.js.
