# Blender Modeling

Purpose: Model, repair or procedurally build an asset in Blender with a verified agent loop.

Read when:
- Building or fixing geometry in Blender (blockout, hard-surface, Geometry Nodes, repairing an import).

Skip when:
- Only materials, UVs or bakes (→ [blender-lookdev-render](blender-lookdev-render.md)), or export (→ [blender-export](blender-export.md)).
- The subject is a common stock asset (→ [asset-acquire](asset-acquire.md)).

Inputs:
- Brief with real dimensions and budgets (tris, texture px), references, the channel from [blender-channels](blender-channels.md).

Produces:
- A `.blend` that passes the numeric gate and matches references in a render.

## Loop

1. Brief in numbers: purpose, target use, tri and texture budgets ([shared-performance](shared-performance.md)), real size (1 unit = 1 m).
2. Read state first with `<skill>/assets/blender/inspect_scene.py` (or `bpy.data` in an MCP call). Unit counts, scale, modifiers, materials.
3. One change per call or script step. Plan big to small: block-out → primary forms → secondary forms → detail.
4. Verify: frame the subject, then capture (two opposite angles, plus front/side/top for proportion). An unframed viewport shows a prop as a few pixels.
5. Gate numbers and image: tri count, scale applied, proportions within 5% of the reference (2% for the final pass), silhouette match before form, form before detail, topology before texture.
6. Fix before advancing: a block-out defect costs one step, the same defect after texturing costs a stage. NEVER report done without looking at a render.
7. Mark unseen surfaces `inferred`; unknown evidence stays UNKNOWN ([intake-references](intake-references.md)). Two repeats of the same failed fix means change approach.

## Repair before modelling

Prefer repairing an imported or generated model over modelling a common asset from scratch ([asset-acquire](asset-acquire.md)): fix scale and origin, normals, doubles, n-gons and UVs, then decimate or retopo to budget. Model from scratch only for the hero, custom or branded shape.

## Rules

- Axes: Blender is Z-up; glTF, three.js and `shots.v1` are Y-up. Model up along +Z, front facing -Y; the exporter converts ([blender-export](blender-export.md)). A chip lying flat in Blender lies flat in three.js.

- Apply rotation and scale before bevel, solidify, array, bake and export.
- Use the data API and `bmesh` over operators (hundreds of `bpy.ops.mesh.primitive_*` calls are orders of magnitude slower than `bpy.data.objects.new`); keep the object returned by `new()`.
- Never touch data you did not create; tag owned datablocks with a prefix or custom property; rerun must not create `.001` twins.
- `obj.data` ignores modifiers: use `ob.evaluated_get(depsgraph).to_mesh()` and `to_mesh_clear()`. `matrix_world` is stale until `view_layer.update()`. Edit Mode holds its own mesh copy.
- Smoothing: `mesh.use_auto_smooth` is gone; use Smooth by Angle ([blender-version-traps](blender-version-traps.md)).

## Hard-surface order

Cut first, bevel after, normals last.
1. Booleans on the clean base. Solver `EXACT`; cutters must be closed (open cutters break Exact and silently skip in Manifold). `FAST` was renamed `FLOAT`.
2. Bevel above the booleans: Harden Normals on, about 3 mm on body parts and 1 mm on small parts, 3 segments for renders, 1–2 for web.
3. Weighted Normal at the bottom of the stack; Mirror late.
4. If Harden Normals or Weighted Normal change nothing, the faces are not flat. Judge in a shiny matcap, close up on every cut.
5. N-gons and booleans for planar machined parts; a quad cage with subdivision for continuous curvature.

## Geometry Nodes

- Prefer trait selections (position, normal, proximity) over indices; keep instances; simulate only when history matters (else drive from scene time).
- Expose dependencies as group inputs; everything is object-local.
- Web trap: GN output exists only as a modifier result. Exporting without applying writes the base mesh and the procedural asset vanishes ([blender-export](blender-export.md)).
- Set inputs with `mod.properties.inputs.<identifier>.value` on 5.2+, not `mod["Socket_2"]`.

## Reference-fidelity gates

1. Camera-lock a view that matches the reference, then compare silhouette overlap (aim ≥ 0.85 at block-out, ≥ 0.90 at forms) before detailing.
2. Check proportions numerically from the bounding box (`inspect_scene.py`), not by eye.
3. Cap compare-and-fix loops at three, then show the user the best candidate and the delta.
4. NEVER weaken the rubric after a failed candidate.

## Traps

- Unit scale is ignored by the exporter: 1 Blender unit exports as 1 m. A scene modelled in mm units arrives 1000x too large; model in metres at scale 1.0.
- Never lose user work: copy the `.blend` before batch edits.
