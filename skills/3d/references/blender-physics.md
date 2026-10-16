# Blender Physics

Purpose: Set up, bake, verify and deliver simulations (rigid body, cloth, soft body, fluid, particles, hair, simulation nodes) from headless Blender to the web.

Read when:
- Anything must fall, drape, splash, burn, flutter or grow hair; "bake the simulation"; "cloth/liquid for the web"; sim differs between runs or after a frame jump.

Skip when:
- Scatter, instancing, hair styling or custom node logic without time (→ [blender-geometry-nodes](blender-geometry-nodes.md)); keyframed or rigged motion (→ [blender-animation](blender-animation.md)).

Inputs:
- Simulation contract below; `.blend` with real-scale meshes.

Produces:
- Approved cache on disk, then keys, shape keys or pre-rendered frames; verification JSON.

## Contents

- Contract · Solver choice · Settings · Caching headless · Determinism · Delivery to web · Verify · Traps

## Contract

Write before touching a setting: type, solver, fps, scale, onset/peak/settle frames, forces, colliders, cache dir, deliverable. ALWAYS model at real size (metres; mass = volume x density) and set `scene.render.fps` first; defaults are `scene.gravity` -9.81 and 24 fps. Change one causal group per rebake. Never overwrite an approved cache. Headless rules: [blender-scripting](blender-scripting.md).

## Solver choice

| Need | Use |
|---|---|
| Falling, stacking, collisions | Rigid body (Bullet) |
| Clothing, flags | Classic `CLOTH` modifier + `COLLISION` on colliders |
| New node cloth or hair | Assets `Cloth Dynamics (Experimental)` / `Hair Dynamics` (nodes on the `XPBD Solver`); experimental, interfaces may change, pin the Blender version |
| Liquid, smoke, fire | Mantaflow (`FLUID` modifier) |
| Custom rules (flocking, growth) | Simulation zone: `GeometryNodeSimulationInput` / `GeometryNodeSimulationOutput` ([blender-geometry-nodes](blender-geometry-nodes.md)) |
| Jelly | Soft body `SOFT_BODY`; rarely worth it, prefer cloth or shape keys |
| Sparks, dust, rain | Legacy particle system (`EMITTER`), or GN instancing when no force field is needed |

## Settings that matter

- Rigid body: `bpy.ops.rigidbody.object_add()`; floor `type='PASSIVE'`. Defaults: `substeps_per_frame` 10, `solver_iterations` 10, mass 1 kg, `CONVEX_HULL`. Dynamic bodies `CONVEX_HULL`; `MESH` only for passive concave. Densities kg/m3: wood 500-700, plastic 950, concrete 2400, steel 7850. Margin about 1 mm for small props. Never start interpenetrated. Tunnelling: raise `substeps_per_frame` or thicken the collider (`convex_sweep_test` exists; effect untested).
- Cloth: even quad grid, no n-gons, 2-5 cm edges for garments; pin with a vertex group (`vertex_group_mass`, weight 1); colliders `COLLISION` modifier, thickness 1-5 mm; `quality` default 5 (raise for stiff fabric). Self-collision is `collision_settings.use_self_collision`, off by default.
- Cloth Dynamics asset (nodes): inputs include Pin Group, Stretchiness, Bendiness, Substeps (5), Constraint Steps, Mass, Collision Radius, Gravity (-9.81 z), Effectors Collection. Experimental: collisions via the `Collider` asset; check self-collision and wind on your version before promising either.
- Mantaflow: `bpy.ops.object.quick_liquid()` / `quick_smoke()` create flow + domain (`resolution_max` starts at 32). Preview 64, final 128-256 (community figures, not Blender defaults). Default `cache_type` is `REPLAY`: set `'ALL'` for a headless bake and set `cache_directory` yourself (default is a temp dir). Default format `OPENVDB` data, `BOBJECT` mesh. No community tuning values (viscosity, flip ratio) are recorded here: change from defaults only with a measured reason.
- Legacy particles: `ParticleSettings` `type` `EMITTER` or `HAIR`, `count` (default 1000), `frame_start`/`frame_end`/`lifetime`. Hair styling is the Curves system (`bpy.ops.object.curves_empty_hair_add()` adds a `CURVES` object with a `Hair Dynamics` modifier); `bpy.ops.curves.convert_from_particle_system` / `convert_to_particle_system` bridge the two.

## Caching headless

1. Step from `frame_start` in order: `for f in range(a, b+1): scene.frame_set(f)`. State advances only for frames actually evaluated (measured: sampling frames 1, 10, 30 left a node cloth near its start pose while every-frame stepping fell correctly).
2. Bakes: classic caches `bpy.ops.ptcache.bake_all(bake=True)` (worked with no override: rigid world and cloth both ended `is_baked` True); single `ptcache.bake` under `temp_override(point_cache=mod.point_cache)`; free with `ptcache.free_bake_all()`. Fluid: `bpy.ops.fluid.bake_all()` under `temp_override(active_object=domain, object=domain, selected_objects=[domain])` after `cache_type='ALL'` and `cache_frame_start/end`; read `domain_settings` flags afterwards. Simulation nodes: `bpy.ops.object.simulation_nodes_cache_bake(selected=False)` under `temp_override(object=obj, active_object=obj)`; baked, an arbitrary frame jump is then correct.
3. Any change to the object, a collider or a setting invalidates the cache. Rebake the smallest interval, then save; keep fluid and node-bake folders beside the `.blend`.

## Determinism

Same file + same blender + same frame order gave identical rigid-body positions across two processes (md5 over 120 frames). Reproduce a state by stepping from the start, or bake and read the cache; never by jumping.

## Delivery to web

| Sim | Route | Notes |
|---|---|---|
| Rigid | Step frames, sample `matrix_world`, then `rigidbody.object_remove`, `keyframe_insert("location")` and rotation per frame | glTF exports it as translation + rotation channels (measured). `rigidbody.bake_to_keyframes` FAILS headless (context poll error): do not use it |
| Cloth, soft body | Evaluate each frame (`evaluated_get(depsgraph).to_mesh()`, `vertices.foreach_get("co")`), write shape keys `shape_key_add(from_mix=False)`, key `value` one-hot per frame | glTF `weights` channel works; 961 verts x 20 frames = 1.3 MB; cap about 60 frames. Single end pose: `object.modifier_apply_as_shapekey(keep_modifier=True, modifier="Cloth")` |
| Long or dense cloth | Vertex animation texture: write positions to a float image, sample in a custom vertex shader ([shader-glsl](shader-glsl.md)) | OpenVAT-style add-on: licence and 5.x support untested; own the script |
| Liquid, smoke, fire | Pre-render frames: [scroll-video](scroll-video.md) | Mantaflow caches never reach glTF |
| Hair | Build mesh cards by hand (untested conversion), or render | Curves are not strand geometry in glTF; an empty hair `CURVES` object exported as an empty node (populated curves untested) |
| Any | Alembic/USD (`wm.alembic_export`, `wm.usd_export`) exist for DCC hand-off only | Not web-loadable |

Export settings and clip naming: [blender-export](blender-export.md).

## Verify

1. Reopen the saved file in a fresh `blender -b` process; step to the same frames.
2. Report facts separately: modifier present, forces/colliders set, cache range, `is_baked`, then behaviour: `z` or vertex extents at onset/peak/settle frames within the contract. Evidence rule: [blender-channels](blender-channels.md).
3. After conversion, re-read the exported GLB animation channels and compare 3 sampled frames to the sim.

## Traps

- Frame jumps give a stalled or reset sim, not the real pose.
- Cloth evaluated mesh coordinates are local; apply `matrix_world` before comparing world heights.
- Fluid with default `REPLAY` or temp cache dir leaves nothing to ship.
- Unapplied object scale or tiny (cm-scale) meshes make every solver look floaty.
- Do not key a body that still has a rigid body: remove the rigid body after sampling or the sim overrides keys.
