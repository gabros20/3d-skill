# Blender Modeling

Purpose: Model, repair or procedurally build an asset in Blender with a verified agent loop.

Read when:
- Building or fixing geometry in Blender (blockout, hard-surface, sculpt, retopo, decimation, repairing an import).

Skip when:
- Only materials, UVs or bakes (→ [blender-lookdev-render](blender-lookdev-render.md)), or export (→ [blender-export](blender-export.md)).
- The subject is a common stock asset (→ [asset-acquire](asset-acquire.md)).

Inputs:
- Brief with real dimensions and budgets (tris, texture px), references, the channel from [blender-channels](blender-channels.md).

Produces:
- A `.blend` that passes the numeric gate and matches references in a render.

## Contents

Loop · Repair · Rules · Hard-surface · Stack order · Sculpt · Retopology · Decimate · Cleaning · Fidelity gates · Traps

## Loop

1. Brief in numbers: purpose, target use, tri and texture budgets ([shared-performance](shared-performance.md)), real size (1 unit = 1 m).
2. Read state first with `<skill>/assets/blender/inspect_scene.py` (or `bpy.data` in an MCP call). Unit counts, scale, modifiers, materials.
3. One change per call or script step. Plan big to small: block-out → primary forms → secondary forms → detail.
4. Verify: frame the subject, then capture (two opposite angles, plus front/side/top for proportion). An unframed viewport shows a prop as a few pixels.
5. Gate numbers and image: tri count, scale applied, proportions within 5% of the reference (2% for the final pass), silhouette match before form, form before detail, topology before texture.
6. Fix before advancing. NEVER report done without looking at a render.
7. Mark unseen surfaces `inferred`; unknown evidence stays UNKNOWN ([intake-references](intake-references.md)). Two repeats of the same failed fix means change approach.

## Repair before modelling

Prefer repairing an imported or generated model over modelling a common asset from scratch ([asset-acquire](asset-acquire.md)): fix scale and origin, normals, doubles, n-gons and UVs, then decimate or retopo to budget. Model from scratch only for the hero, custom or branded shape.

## Rules

- Axes: Blender is Z-up; glTF, three.js and `shots.v1` are Y-up. Model up along +Z, front facing -Y; the exporter converts ([blender-export](blender-export.md)). A chip lying flat in Blender lies flat in three.js.

- Apply rotation and scale before bevel, solidify, array, bake and export.
- Use the data API and `bmesh` over operators (hundreds of `bpy.ops.mesh.primitive_*` calls are orders of magnitude slower than `bpy.data.objects.new`).
- Tag datablocks you create; reruns must not create `.001` twins.
- `obj.data` ignores modifiers: use `ob.evaluated_get(depsgraph).to_mesh()` and `to_mesh_clear()`. `matrix_world` is stale until `view_layer.update()`. Edit Mode holds its own mesh copy.
- Smoothing: `mesh.use_auto_smooth` is gone; use Smooth by Angle ([blender-version-traps](blender-version-traps.md)).

## Hard-surface order

Cut first, bevel after, normals last.
1. Booleans on the clean base. Solver `EXACT`; cutters must be closed (open cutters break Exact and silently skip in Manifold). `FAST` was renamed `FLOAT`; `MANIFOLD` is the fast solver but needs manifold inputs. Messy cutters: `use_self`, `use_hole_tolerant`. Coplanar faces: offset the cutter ~0.1 mm. Keep cutters in a `_cutters` collection, display Wire, `hide_render`.
2. Bevel above the booleans: Harden Normals on, about 3 mm on body parts and 1 mm on small parts, 3 segments for renders, 1–2 for web.
3. Weighted Normal at the bottom of the stack; Mirror late.
4. If Harden Normals or Weighted Normal change nothing, the faces are not flat; check in a shiny matcap.
5. N-gons and booleans for planar machined parts; a quad cage with subdivision for continuous curvature.

## Modifier stack order

Top to bottom: Mirror → Array → Solidify → Boolean (cuts) → Bevel → Subdivision → Weighted Normal → Triangulate (export copy only).
- Armature after Mirror, before Subdivision; Corrective Smooth after Armature.
- Shrinkwrap (`wrap_method` `NEAREST_SURFACEPOINT` / `PROJECT`) before Subdivision on a retopo cage.
- Data Transfer for custom normals goes last.
- Apply scale first. Read tri counts from the evaluated mesh, never `obj.data`.

## Sculpt (agent role)

Agents do not brush. Sculpt-mode operators reportedly crash headless (`-b`); this is unverified and was not run here, so never enter Sculpt Mode in a script. Brushwork goes to the user over an MCP session ([blender-channels](blender-channels.md)). Agent-side jobs:
- Voxel remesh: set `mesh.remesh_voxel_size`, then `object.voxel_remesh()` (no properties). Voxel size by head height H: block-out H/40, primary forms H/65–110, secondary H/130–235, detail ~H/330. Shape before 100k faces.
- It destroys UVs, vertex groups and multires: run it before UV and rigging.
- `object.multires_subdivide(modifier=, mode=)`; multires and topology edits do not mix. Bake from the highest level onto a level-0 low mesh ([blender-uv-bake](blender-uv-bake.md)). Bake behaviour untested.
- `mesh.symmetrize(direction=, threshold=)`. Asymmetry goes on a shape key.
- Procedural sculpt: Geometry Nodes SDF-grid booleans and fillets ([blender-geometry-nodes](blender-geometry-nodes.md)).

## Retopology

Pick the method per part:
- Static props, scans, bake-only meshes: automatic. `object.quadriflow_remesh(target_faces=, use_preserve_sharp=, use_mesh_symmetry=)` (verified: target 200 gave 227 faces) or voxel remesh.
- Deforming heroes: hand-built loops or Shrinkwrap onto the high mesh. 3 loops at each bending joint, poles only where nothing moves, loops close on themselves, triangles only in hidden non-deforming spots.
- Judge the subdivided surface: a snapped cage shrinks once subdivided.
- Budgets: [shared-performance](shared-performance.md).
- Quad Remesher (paid add-on): propose, never install ([asset-acquire](asset-acquire.md)).

## Decimate for web

1. Bake normals from the original first; keep it as `X_high` ([blender-uv-bake](blender-uv-bake.md)).
2. `COLLAPSE` with `ratio` for organic meshes; `delimit` takes `NORMAL`, `MATERIAL`, `SEAM`, `SHARP`, `UV` to protect seams and UV borders.
3. `DISSOLVE` with `angle_limit` (about 1–5°) for hard-surface; `UNSUBDIV` for grid-like meshes.
4. Measure the evaluated mesh; the ratio is not the final count.
5. Check silhouette at the shot distance.

## Cleaning a generated or scanned mesh

The common agent path ([asset-acquire](asset-acquire.md) links here).
1. Inspect with `<skill>/assets/blender/inspect_scene.py`.
2. Merge by distance: operator `mesh.remove_doubles(threshold=0.0001)`, in Edit Mode with all selected (the menu label is Merge by Distance). Verified: 16 → 8 verts on a doubled cube.
3. Normals: `mesh.normals_make_consistent(inside=False)`.
4. Non-manifold: `mesh.select_non_manifold`, then `mesh.fill_holes` or `mesh.delete_loose`. Still broken, or intersecting shells: voxel remesh, which gives a watertight result but drops UVs.
5. Retopo or decimate to budget (above), then UV.
6. Bake albedo and normal from the original ([blender-texturing](blender-texturing.md), [blender-uv-bake](blender-uv-bake.md)).
7. Origin at the base, `object.transform_apply(isolate_users=True)`, real size in metres, up along +Z.
8. Gate: tris within budget, bake not flat, render versus the original at the shot camera.

## Geometry Nodes

Moved to [blender-geometry-nodes](blender-geometry-nodes.md).

## Reference-fidelity gates

1. Camera-lock a view that matches the reference, then compare silhouette overlap (aim ≥ 0.85 at block-out, ≥ 0.90 at forms) before detailing.
2. Check proportions numerically from the bounding box (`inspect_scene.py`), not by eye.
3. Cap fix loops at three, then show the best candidate and the delta.
4. NEVER weaken the rubric after a failed candidate.

## Traps

- Unit scale is ignored by the exporter: 1 Blender unit exports as 1 m. A scene modelled in mm units arrives 1000x too large; model in metres at scale 1.0.
- Never lose user work: copy the `.blend` before batch edits.
