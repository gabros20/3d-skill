# Blender Geometry Nodes

Purpose: Build, drive, verify and hand off procedural Geometry Nodes assets from Python on Blender 5.2.

Read when:
- Scattering, arraying along curves, greebling, hair curves, simulation or repeat zones, or any asset that must stay procedural.
- A GN asset exports as its base mesh, loses UVs or smoothing, or its modifier inputs will not set.

Skip when:
- Plain modifier stacks, booleans, sculpt (→ [blender-modeling](blender-modeling.md)); solver choice for cloth or fluids (→ [blender-physics](blender-physics.md)).
- General bpy safety, gates, JSON contract (→ [blender-scripting](blender-scripting.md)).

Inputs:
- Target object, what must stay editable, budget for the web target ([shared-performance](shared-performance.md)).

Produces:
- A node group with named inputs, a verified evaluated count, and either an applied mesh or kept instances for export.

## Build from Python

1. Tree: `ng = bpy.data.node_groups.new(name, "GeometryNodeTree")`. Sockets: `ng.interface.new_socket(name, in_out='INPUT'|'OUTPUT', socket_type='NodeSocketGeometry'|'NodeSocketFloat'|'NodeSocketInt'|'NodeSocketBool'|'NodeSocketObject')`. Add every dependency (target object, density, `Seed`) as an input; never reference scene objects inside the tree.
2. Nodes: `ng.nodes.new("GeometryNodeInstanceOnPoints")`; links: `ng.links.new(a.outputs[...], b.inputs[...])`. Address sockets by display name (`'Mesh'`, `'Density Max'`, `'Instance'`), never by index, and print `[s.name for s in node.inputs]` for any node you have not used this session.
3. Attach: `md = ob.modifiers.new("GN", "NODES"); md.node_group = ng`.
4. Set inputs by identifier, resolved from the interface: `ids = {i.name: i.identifier for i in ng.interface.items_tree if i.item_type == 'SOCKET' and i.in_out == 'INPUT'}` then `getattr(md.properties.inputs, ids["Density"]).value = 30`. `md["Socket_2"]` and `md.keys()` raise on 5.2; `Socket_N` numbering shifts when sockets are added.
5. After setting an input, call `ob.update_tag()` then `bpy.context.view_layer.update()` before reading the result. Measured: the first evaluation was right, and a later `.value = True` change left the old result until the tag.
6. Menu-type choices moved onto sockets in 5.2: Resample Curve `Mode` is an input (`inputs['Mode'].default_value = 'Count'`), while Curve to Points and Distribute Points keep `node.mode` / `node.distribute_method` properties. Check with `--describe`-style introspection, not memory.
7. Zone pairs: `ri = nodes.new("GeometryNodeRepeatInput"); ro = nodes.new("GeometryNodeRepeatOutput"); ri.pair_with_output(ro)` (same for `GeometryNodeSimulationInput/Output`). State items appear after pairing; link the first by name (`'Geometry'`). Capture Attribute items: `ca.capture_items.new('FLOAT', "Height")`, then use `ca.inputs['Height']` and `ca.outputs['Height']`.

## Rules that decide results

- A field is a deferred question: the consuming node evaluates it on its own domain. Freeze it with Capture Attribute before a node that changes topology (Extrude, Subdivide, Delete).
- Boolean fields cast from float: any value above 0 is true, so a vertex-group selection that is interpolated onto a subdivided mesh bleeds. Threshold with Compare and an epsilon.
- Everything is object-local; world-space directions need Self Object, Object Info (Relative off), Invert Matrix, Transform Direction.
- Simulate only when state depends on the previous frame; otherwise drive from Scene Time, which scrubs. Repeat and For-Each zones are the last resort when a built-in node exists.
- GN output has no UVs or smoothing unless you write them: Store Named Attribute (`FLOAT2`, `CORNER`, name `UVMap`) and Set Shade Smooth or Smooth by Angle. UV storage is untested here; confirm with `uv_layers` on the applied mesh.
- Seed every Random Value from an ID or Index field plus a group `Seed` input, so a variation is a number rather than a rebuild.

## Patterns

| Goal | Chain (5.2 node names) |
|---|---|
| Scatter | `GeometryNodeDistributePointsOnFaces` (`POISSON` with Distance Min, or `RANDOM` with Density Max; density attribute drives Density Factor) then `GeometryNodeInstanceOnPoints`; feed its `Rotation` output and Random Value (rotation, scale) |
| Array on a curve | `GeometryNodeCurveToPoints` (`COUNT`) emits `Points` and `Rotation` (tangent aligned); Instance on Points. Measured: 8 instances on a 2-point Bezier |
| Pipe, rail, cable | `GeometryNodeCurveToMesh` with a `GeometryNodeCurvePrimitiveCircle` profile (resolution 8 gave 16 verts per line) |
| Greebles, panels | Extrude or Inset on a Selection field, offset by Random Value, join to the base |
| Booleans or fillets that Exact cannot do | SDF grid chain: `GeometryNodeMeshToSDFGrid`, `GeometryNodeSDFGridBoolean`, `GeometryNodeSDFGridFillet`, `GeometryNodeGridToMesh` (names exist on 5.2; round trip untested) |
| Hair | Hair curves are GN assets; see Hair |

Closures and bundles exist in 5.x; skip them unless the task is a reusable tool.

## Instances versus realized

- Instances are cheap: keep them until something needs real geometry (booleans, per-instance edits, apply). Measured on a 4 m grid: 480 instances became 3,840 vertices and 2,880 faces when realized.
- Web target, many copies: keep instances and export `EXT_mesh_gpu_instancing`. Flags and the instance-source trap live in [blender-export](blender-export.md) (`--gn-instances`; `export_gn_mesh` and `export_gpu_instances` both required). Measured: the instanced host exported with TRANSLATION, ROTATION and SCALE attributes.
- Web target, few unique pieces, per-instance materials, or non-glTF consumers: Realize Instances, then apply.
- `bpy.ops.object.modifier_apply` on an instances-only result fails with "Evaluated geometry from modifier does not contain a mesh". Add Realize Instances first (measured 64 vertices, 48 faces for 8 cubes).

## Simulation zones

- A frame jump does not equal stepping. Measured: stepping frames 1 to 5 gave z 0.1 to 0.5; a fresh jump from 1 to 5 gave 0.2. Headless, step `scene.frame_set(f)` in order from the start frame, or bake.
- Bake: read `md.bakes[i].bake_id`, select and activate the object, then `bpy.ops.object.geometry_node_bake_single(session_uid=ob.session_uid, modifier_name=md.name, bake_id=bid)`. After the bake a jump to frame 5 returned 0.5. Set `scene.frame_start/end` first; bake before export or any frame jump.
- A Repeat zone with a Join Geometry of its own input doubles the geometry each pass (5 iterations gave 32 points from 1). Count before raising iterations.
- XPBD solver and hair-dynamics assets are experimental in 5.2; choose the solver in [blender-physics](blender-physics.md).

## Hair curves

Hair curves do not export to glTF (untested here; plan for cards or mesh). Method, from community practice: finish topology and non-overlapping UVs and apply scale first (density counts local area); place guides with 2 points while shaping, mask Interpolate, randomise per curve rather than per point, grow on a separate hair cap split along the part, and judge at full density in pose. For the web, convert to mesh cards (about one subdivision per 20 cm) or bake. Comb and sculpt-curves strokes are GUI-only.

## Reusable tools

`ng.is_modifier = True; ng.asset_mark()` makes the group an asset (both measured). Test it on a second object, such as Suzanne, to prove it holds no hidden scene reference.

## Verify

Read counts from the evaluated geometry, never from `ob.data`:

```python
ob.update_tag(); bpy.context.view_layer.update()
gs = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).evaluated_geometry()
mesh = gs.mesh                       # vertices, polygons (empty, not None, when only instances exist)
ip = gs.instances_pointcloud()       # None when realized; len(ip.points) = instance count
```

Hold `gs` in a variable while you read `gs.mesh`; a mesh read through a dropped GeometrySet raises "StructRNA has been removed". `ev.to_mesh()` works for realized results and needs `to_mesh_clear()`.

Gate: instance or vertex count matches the expectation within the Seed variation, bounds match the brief, and the exported GLB re-read by `scripts/glb-report` shows the same triangle count or the instancing extension.

## Traps

- Exporting without applying or instancing writes the host mesh and the asset vanishes ([blender-export](blender-export.md)).
- A leftover instance source object exports as its own node.
- Performance: realizing before you need to, Distribute Points Poisson at high density, and zone loops dominate evaluation time; lower density in the viewport input and keep the final value in a separate input.
