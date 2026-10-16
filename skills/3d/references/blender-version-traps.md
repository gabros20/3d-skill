# Blender Version Traps

Purpose: List the Blender 5.x API changes an LLM's memory gets wrong, as old → new.

Read when:
- Writing or debugging any `bpy` script, or a script copied from older docs or an MCP prompt.

Skip when:
- The error is an export or look problem rather than an API error (→ [blender-export](blender-export.md), [blender-lookdev-render](blender-lookdev-render.md)).

Inputs:
- The failing call, `bpy.app.version_string`.

Produces:
- A corrected call; a runtime introspection instead of a guess.

## Meta-rule

Ask Blender, do not remember. `dir(obj)`, `type(obj).bl_rna.properties.keys()`, `bpy.ops.x.y.get_rna_type().properties.keys()`. Static enums list via `bl_rna.properties['prop'].enum_items`; dynamic enums (render engine, view transform, denoiser, add-on enums) do not (headless 5.2.2 returns `['BLENDER_EEVEE']`, `['NONE']`, `[]`). For those, assign a bad value in try/except and read the allowed list from the `TypeError` text (the Cycles denoiser list is also hardware-dependent), e.g. `enum "zzz" not found in ('Standard', 'ACES 1.3', 'ACES 2.0', 'Khronos PBR Neutral', 'AgX', …)`. `hasattr(bpy.types.Mesh, "prop")` is False for RNA properties. Assign engine and enum values inside try/except so a bad guess fails loudly. Current reference: Blender 5.2 LTS (Python 3.13 since 5.1).

## Old → new (5.x)

| # | Old | New |
|---|---|---|
| 1 | `render.engine = 'BLENDER_EEVEE_NEXT'`; `use_gtao`, `gtao_quality`, `gtao_distance` | `'BLENDER_EEVEE'`; `view_layer.eevee.ambient_occlusion_distance` |
| 2 | Pass names `Z`, `DiffCol`, `IndexMA` | `Depth`, `Diffuse Color`, `Material Index` |
| 3 | `scene.use_nodes`, `scene.node_tree`; File Output `file_slots`, `layer_slots`, `base_path` | `scene.compositing_node_group`; `directory`, `file_name`, `file_output_items`; Color output `RGBA` → `Color`; no Composite node |
| 4 | `obj['x']` or `scene['cycles']` for `bpy.props` properties; `del obj[k]` | attribute access; `obj.property_unset(k)`; prop `get`/`set` → `get_transform`/`set_transform` |
| 5 | `action.fcurves`, `.groups`, `.id_root`; `INSERTKEY_XYZ_TO_RGB` | slotted actions: layers → strips → `channelbags` → `fcurves` (`bpy_extras.anim_utils`), set `action_slot` |
| 6 | Boolean solver `'FAST'` | `'FLOAT'`; `'EXACT'` default; `'MANIFOLD'` available |
| 7 | `file_format='FFMPEG'` alone | set `image_settings.media_type` (`'IMAGE'`/`'VIDEO'`) first |
| 8 | `ImageTexture` `use_mipmap`, `filter_type`; `bgl`; `Image.bindcode` | removed; `gpu` module, `gpu.texture.from_image`; `gpu.init()` in background (5.2) |
| 9 | USD: `import_subdiv`, `attr_import_mode`, `export_textures`, `visible_objects_only` | `import_subdivision`, `property_import_mode`, `export_textures_mode`; removed (also in `wm.alembic_export`) |
| 10 | `GPencil*` annotation types; `grease_pencils_v3` | `Annotation*`; `bpy.data.grease_pencils` is the new Grease Pencil |
| 11 | `Bone.select*` (gone); `Bone.hide` for pose state | `PoseBone.hide`, `PoseBone.select` for pose state; edit bones for edit mode |
| 12 | UV `vertex_selection`, `edge_selection`, `BMLoopUV.select*` | removed (selection shared across UV maps) |
| 13 | mathutils with double buffers | float32 buffers; recheck numpy interop |
| 14 | VSE `frame_final_duration` etc.; brush `use_airbrush`; `sculpt.sample_color` | `duration`; `brush.stroke_method`; removed |
| 15 | `mod["Socket_2"]`, `mod["Socket_2_attribute_name"]` (Geometry Nodes) | `mod.properties.inputs.<identifier>.value` / `.attribute_name`; outputs `.properties.outputs.<id>.attribute_name`; Compare/Random Value socket identifiers changed; sculpt automasking in `mesh_automasking_settings.*` |
| 16 | `active_asset_library` plain index | index is offset by the "All Libraries" and "Essentials" entries |

## Older traps still hit in 5.x

| Old | New |
|---|---|
| `mesh.use_auto_smooth`, `calc_normals()` (gone in 4.1) | `shade_smooth_by_angle`, Smooth by Angle modifier, `mesh.set_sharp_from_angle` |
| Principled `Specular`, `Subsurface`, `Transmission`, `Clearcoat`, `Emission` | `Specular IOR Level`, `Subsurface Weight`, `Transmission Weight`, `Coat Weight`, `Emission Color` (+ `Emission Strength`, default 0) |
| `mat.use_nodes = True` | deprecated no-op |
| `ng.inputs.new(...)` | `ng.interface.new_socket(...)` |
| `bpy.ops.x(override_dict)` | `with bpy.context.temp_override(...)`; check `op.poll()`; prefer `bpy.data` in headless |
| Musgrave, Separate/Combine RGB, Velvet, Point Density nodes | Noise fractal types, Separate/Combine Color, Sheen; removed |
| Sky type `NISHITA` | `SINGLE_SCATTERING`, `MULTIPLE_SCATTERING`, `PREETHAM`, `HOSEK_WILKIE` |
| Brush `sculpt_tool`, `paint.brush_set` | `sculpt_brush_type`, brush assets (`brush.asset_activate`) |
| EEVEE bloom, SSR toggles | Glare compositor node, `use_raytracing`, `use_fast_gi` |
| Colour spaces `Linear`, `Raw` | `Linear Rec.709`, `Non-Color` |
| glTF kwarg `export_colors` | `export_vertex_color` enum; filter every kwarg through `get_rna_type().properties` |

## More traps (verified on 5.2.2)

| Old or assumed | New |
|---|---|
| `scene.sequence_editor.sequences`, `sequences_all`, `sequences.new_movie/new_image/new_sound/new_effect` | `strips`, `strips_all`, `strips.new_clip/new_mask/new_scene/new_image/new_movie/new_sound/new_meta/new_effect`; `scene.sequence_editor_create()` first |
| `world.use_nodes = True` (like `Material.use_nodes`) | deprecated, removal in 6.0; `world.node_tree` exists afterwards |
| `addon_utils.enable("rigify")` with `default_set=False` | prints a traceback, returns `None`, add-on stays off, its operators are absent; use `default_set=True` and assert `addon_utils.check(name)[1]` (never raises on failure) |
| `scene.cycles.denoiser = 'OPTIX'` or `'NLM'` on Apple | enum is `('OPENIMAGEDENOISE')` only on Metal; assigning others raises `TypeError` |
| Resample Curve node `.mode = 'COUNT'` (node property, older docs and scripts) | on 5.2.2 `mode` is a socket: `node.inputs['Mode'].default_value = 'Count'` (value names are title case); other GN nodes (Mesh Line, Curve Circle, Mesh Boolean, Distribute Points) keep node properties: introspect `node.bl_rna.properties` and `node.inputs` |
| `bpy.ops.mesh.merge_by_distance` (menu label) | `bpy.ops.mesh.remove_doubles(threshold=…)` |
| `object.shade_auto_smooth` as "set sharp edges" | it adds a Smooth by Angle modifier; `object.shade_smooth_by_angle(angle=…)` writes the `sharp_edge` attribute and adds no modifier |
