# Blender Scripting

Purpose: Write bpy as an agent: patterns that work on Blender 5.x, gates that prove a change landed, headless limits, batch and file hygiene.

Read when:
- Writing, debugging or reviewing any bpy snippet or script, over MCP or headless.
- A bpy call returned FINISHED but nothing changed, or a script exits 0 after failing.

Skip when:
- Choosing or setting up the channel (→ [blender-channels](blender-channels.md)); an old name fails (→ [blender-version-traps](blender-version-traps.md)).

Inputs:
- The task, `bpy.app.version_string`, the channel.

Produces:
- A short idempotent script that prints one JSON line, plus a verified result.

## Contents

- Contract · Data API first · Evaluated data · Patterns that changed in 5.x · Verify · Headless limits · Ask Blender · Assets and linking · Batch · File hygiene · Extensions · Performance

## Contract

1. Get-or-create by name (`bpy.data.objects.get(n) or bpy.data.objects.new(n, me)`); keep what `new()` returns, never look up by an assumed name (`.001` suffixes). Mark what you create (name prefix or custom property `owner="3d"`); never delete or edit what you did not create. A rerun must not make twins.
2. Headless: `--python-exit-code 1` (without it a raising script exits 0), args after `--`, print one JSON line starting `{` or write a JSON file, never parse the log. MCP `execute_blender_code`: return by assigning a dict to `result`.
3. One save per stage as a numbered copy: `bpy.ops.wm.save_as_mainfile(filepath=p, copy=True, compress=True, relative_remap=True)`. A second save to the same path leaves `.blend1`. Never save over the user's master during an experiment.

## Data API first

`bpy.data.*.new`, `collection.objects.link` and `bmesh` need no context, selection or mode. Use operators only where there is no data route: unwrap and pack, bake, render, export, `object.convert`, `object.modifier_apply`, Rigify generate. For those:
- `with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):` and only the keys the operator's poll reads. Never the old dict argument. Check `op.poll()` first.
- Rigify is the exception: `temp_override` breaks it (`active_object == obj` assertion); set `view_layer.objects.active` and `select_set` instead ([blender-rigging](blender-rigging.md)).
- Edit Mode keeps its own mesh copy: `bmesh.from_edit_mesh`, or leave Edit Mode before reading `obj.data`.

## Evaluated data

- Counts, bounds and tris come from the evaluated mesh: `ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); …; ev.to_mesh_clear()`. `ob.data` ignores modifiers.
- `bpy.context.view_layer.update()` before reading `matrix_world` or driven values. RENDER and VIEWPORT modifier visibility differ: count what will render.

## Patterns that changed in 5.x

```python
# Geometry Nodes input: resolve the identifier, never hard-code Socket_N
ident = next(i.identifier for i in ng.interface.items_tree if i.name == "Scale")
getattr(mod.properties.inputs, ident).value = 2.5

# Layered action from scratch; without action_slot nothing animates
act = bpy.data.actions.new("A"); slot = act.slots.new("OBJECT", ob.name)
cb = act.layers.new("L").strips.new(type='KEYFRAME').channelbag(slot, ensure=True)
fc = cb.fcurves.new("rotation_euler", index=2)
fc.keyframe_points.insert(1, 0.0); fc.keyframe_points.insert(30, 3.14)
ob.animation_data_create(); ob.animation_data.action = act; ob.animation_data.action_slot = slot

# After changing a GN input, tag before reading the evaluated result (else it is stale)
ob.update_tag(); bpy.context.view_layer.update()

# Compositor tree (needs a Group Output, there is no Composite node)
sc.compositing_node_group = bpy.data.node_groups.new("Comp", "CompositorNodeTree")

# Cycles on Apple GPU: refresh before reading devices (list is empty first)
cp = bpy.context.preferences.addons["cycles"].preferences
cp.compute_device_type = "METAL"; cp.refresh_devices()
for d in cp.devices: d.use = d.type != "CPU"
sc.cycles.device = "GPU"
```

`ob.keyframe_insert(...)` still works and creates action, slot, layer and strip itself. Verified on 5.2.2.

## Verify

1. Re-measure from the evaluated depsgraph, never trust `{'FINISHED'}` (unwrap, `parent_set` auto-weights, bake and Rigify generate all return FINISHED on failure).
2. Look at a render of the result; a passing metric never waives a visible defect ([blender-lookdev-render](blender-lookdev-render.md)).
3. Reopen the saved file in a fresh process before saying "done".
4. After any MCP mutation, inspect state before retrying: there is no undo.

## Headless limits

| Fails or differs | Do instead |
|---|---|
| `bpy.app.timers` never fire | do the work synchronously |
| `bpy.ops.ed.undo()` fails its poll | reload the numbered copy |
| sculpt, paint and comb strokes need a viewport (sculpt ops can crash `-b`) | voxel remesh, multires, GN; hand brushwork to the user over MCP |
| `render.opengl` and viewport screenshots | render with Workbench |
| `sequencer.*`, `anim.keyframe_insert` and other UI ops | data API (`strips.new_*`, `keyframe_insert` on the ID) |
| EEVEE needs a GL context | Workbench for CI silhouettes, Cycles for truth |
| First Metal Cycles render compiles kernels (144 s measured once) | budget it or pre-warm; raise client timeouts |

## Ask Blender

Introspect before using a remembered name ([blender-version-traps](blender-version-traps.md) holds the recipes). With the official MCP, `search_api_docs`, `get_python_api_docs` and `search_manual_docs` return RST bundled for the installed version. An add-on enable never raises on failure: `addon_utils.enable(name, default_set=True, persistent=False)` under `--factory-startup` (nothing is saved), then assert `addon_utils.check(name)[1]`. With `default_set=False` Rigify prints a traceback and stays disabled.

## Assets and linking

- `bpy.data.libraries.load(path, link=…)` cannot read the open file. Append for deliverables, link for shared studio libraries; edit a linked rig through `id.override_hierarchy_create`.
- Reusable materials and GN tools: `id.asset_mark()`, then `asset_data.tags.new(...)`, `author`, `license`, `description`, `catalog_id`; `asset_generate_preview()` runs headless. The Essentials library ships with Blender.

## Batch

- Shard frames across processes with `-s/-e`; several machines writing one folder: `render.use_overwrite=False` and `use_placeholder=True`. One process per GPU; with N CPU processes give each `-t`.
- `render.use_persistent_data=True` for animation. Record `bpy.app.version_string` and `bpy.app.build_hash` with every batch result.

## File hygiene

- `transform_apply(isolate_users=True)` for shared data; `bpy.data.orphans_purge(do_recursive=True)` returns the count; `batch_remove(ids)` for mass deletes.
- `file.find_missing_files(directory=…)`, `file.make_paths_relative`, `file.pack_all` run headless.
- Put cutters and helpers in collections (`_cutters`, `_helpers`, `export`) with `hide_render`; give actions you keep a fake user (0-user datablocks are not saved).

## Extensions

Default to a script, not an add-on. If the user needs a UI tool: a manifest, relative imports, wheels in `./wheels/`, no network at register, no datablock references in globals; `blender --command extension validate` / `build`.

## Performance

`vertices.foreach_get("co", arr)` with numpy beat a Python loop 13x on a 10k-vertex mesh (one measurement); no `bpy.ops` in loops (the data API is far faster); one `view_layer.update()` per batch.

## Traps

- `hasattr(bpy.types.Mesh, "prop")` is False for RNA properties; use `bl_rna.properties`.
- `scene.view_layer` does not exist: use `bpy.context.view_layer`.
- Do not call `bpy.ops.wm.read_factory_settings` in a user session.
