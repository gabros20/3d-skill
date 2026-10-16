# Blender animation

Purpose: Key, loop, constrain, bake and verify Blender motion so that it survives glTF export or renders as designed.

Read when:
- Objects, cameras, shape keys or armatures need keyframes, loops or clips
- A constraint, driver or F-curve modifier is in the motion and the result must export
- A camera move comes from `shots.v1` and needs a Blender-side twin

Skip when:
- Building the rig or skinning → [blender-rigging](blender-rigging.md)
- Writing the export call or checking its output → [blender-export](blender-export.md)
- Data-API conventions, gates, JSON contract → [blender-scripting](blender-scripting.md)
- Renamed APIs → [blender-version-traps](blender-version-traps.md)

Inputs:
- Fps, frame range per clip, the clip names the web code will play, loop or one-shot per clip

Produces:
- One named action per clip, constraints and modifiers baked into keys, and a numeric check of the pose at chosen frames

## Contents

- Keyframes · Timing procedure · Loops · F-curve modifiers do not export · Constraints, drivers, baking · Shape keys · NLA and clips · Camera moves · Verification · Mocap retarget without add-ons · Grease Pencil · VSE · Traps

## Keyframes (5.x slotted actions)

1. Prefer `ob.keyframe_insert("location", frame=f)`. It creates action, slot, layer and strip itself. `action.fcurves` no longer exists.
2. Reach curves with `bpy_extras.anim_utils.action_get_channelbag_for_slot(act, ob.animation_data.action_slot).fcurves`. Building an action by hand is in [blender-scripting](blender-scripting.md).
3. Assigning `ad.action` without `ad.action_slot` leaves the object static. `slot.identifier` looks like `OBBox`; slots have no `.name`.
4. Set fps first: `scene.render.fps`. Clip length in seconds is `frames / fps`.
5. Per key: `k.interpolation` (`CONSTANT`, `LINEAR`, `BEZIER`), `k.easing` (`EASE_IN_OUT` etc.), `k.handle_left_type` / `handle_right_type`.

## Timing procedure

1. Block key poses with `CONSTANT` and keep that stage long. Add breakdowns while stepped.
2. Copy each pose to the end of its hold (pillars), then convert the body curves to Bezier. A whole-curve Bezier conversion drifts across holds.
3. Handle types are timing choices: `AUTO_CLAMPED` for holds, `AUTO` only for settles and overshoot, `VECTOR` for contacts and take-offs, `FREE` for burst spacing.
4. Product and camera moves: ease in and out, 0.4 to 1.2 s per beat. Linear only for turntables.
5. A contact inside continuous motion (a landing) is not a hold; do not pillar it.

## Loops

1. First key value must equal last key value, and the last key sits on frame `start + length`. Loops that repeat the end frame stutter.
2. Linear rotation loop: `LINEAR` keys plus `fc.extrapolation = 'LINEAR'` continues the spin; a `CYCLES` modifier repeats the same segment instead.
3. `act.use_frame_range` with `frame_start` / `frame_end` pins the clip range; `act.use_cyclic` marks it.
4. Seam test: `fc.evaluate(first)` against `fc.evaluate(last)` for every channel; the difference must be below 1e-4.

## F-curve modifiers do not export

`CYCLES`, `NOISE`, `SMOOTH` and the others do not reach glTF. Measured: an action with a `CYCLES` modifier exports only its keyed 2.03 s, with or without `export_force_sampling`. To keep the look, evaluate and rewrite keys:

```python
vals = [(f, fc.evaluate(f)) for f in range(a, b + 1)]
fc.modifiers.remove(fc.modifiers[0])
fc.keyframe_points.clear()
for f, v in vals: fc.keyframe_points.insert(f, v, options={'FAST'})
fc.update()
```

Cleanup after dense keys: `bpy.ops.graph.decimate` and `graph.butterworth_smooth` exist (they need a Graph Editor context, so the evaluate-and-rewrite loop is the headless route).

## Constraints, drivers, baking

1. Constraints for motion: Track To or Damped Track (camera aim), Follow Path, Child Of (hand-offs), Copy Transforms. glTF exports none of them.
2. Bake with the data API, not the operator:

```python
from bpy_extras import anim_utils as au
bo = au.BakeOptions(only_selected=False, do_pose=False, do_object=True, do_visual_keying=True,
    do_constraint_clear=True, do_parents_clear=False, do_clean=True,
    do_location=True, do_rotation=True, do_scale=False, do_bbone=False, do_custom_props=False)
acts = au.bake_action_objects([(ob, None)], frames=range(a, b + 1), bake_options=bo)
```

   Verified: constraints left 0, one new action. Rename it and set a fake user. `bpy.ops.nla.bake(visual_keying=True, clear_constraints=True, bake_types={'OBJECT'})` also works but needs a `temp_override` with object, selection and active object.
3. Bake over the exact clip range, then compare the baked pose with the constrained pose at three frames before deleting anything.
4. Drivers: `ob.driver_add("scale", 0).driver`, type `SCRIPTED`, variables with `targets[0].id` and `data_path`. Simple expressions run without auto-run Python. After `frame_set`, call `view_layer.update()`. Drivers do not export; bake or key the result.
5. Armature motion: bake pose bones with `do_pose=True` and the armature object.

## Shape keys

1. `key_block.keyframe_insert("value", frame=f)`. The action lives on `mesh.shape_keys.animation_data` (a datablock of its own, slot like `KEKey`), not on the object.
2. Export with `export_apply` off, or morph targets vanish. Cloth or soft-body motion → bake to shape keys, then key `value`.

## NLA and clips

1. One action per clip, `use_fake_user = True`, named as the web code expects.
2. Stack with `ad.nla_tracks.new()` then `track.strips.new(name, start, action)`; set `strip.action_slot` explicitly, then clear `ad.action`.
3. glTF clip source is `export_animation_mode`: `NLA_TRACKS` names clips by track (verified: `Spin`, `Slide`), `ACTIONS` by action (verified: both, sorted by name). Pick one on purpose and confirm names with `scripts/glb-report`.
4. Clips share a node timeline in the browser; keep one fps across all of them.

## Camera moves

1. A `shots.v1` shot with `to` and `duration_s` is rendered by `assets/blender/render_shots.py --moves`. Its ease names are `linear`, `in` (t squared), `out`, and default `inOut` (smoothstep). Mirror them in Blender with `LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT` keys.
2. Aim with a target empty and Track To, key the empty and the camera, bake only if the camera itself exports as animation.
3. Seamless turntable: `render_shots.py --turntable N`; frame N+1 equals frame 1. Light and camera orbit, the asset stays still ([blender-lookdev-render](blender-lookdev-render.md)).
4. Scroll-scrubbed footage → [scroll-video](scroll-video.md).

## Verification

1. Pose at frames, headless: `sc.frame_set(f)` then `ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation` (verified: x = 2.0 at the midpoint of a 0 to 4 ease).
2. Print the pose at start, middle and end of each clip as one JSON line; assert against the intended values.
3. Cheap visual check: Workbench render, `scene.render.engine = 'BLENDER_WORKBENCH'`, small resolution, `animation=True`, and an absolute `render.filepath` (a `//` path fails in an unsaved file).
4. After export, count animations and read clip durations with `scripts/glb-report`.

## Mocap retarget without add-ons

1. Match rest pose first (T against A matters most). `COPY_ROTATION` per bone, `COPY_LOCATION` on hips scaled by the leg-length ratio.
2. Bake as above, delete constraints, clean with decimate ratio 0.3 to 0.5. BVH is often in cm: `global_scale=0.01`.

## Grease Pencil

1. v3 data: `bpy.data.grease_pencils.new`, `gp.layers.new`, `layer.frames.new(f)`. Layers default to `use_lights = True`; set False for flat colour.
2. Line Art: `gpo.modifiers.new(name, 'LINEART')`.
3. Key every visible layer at the start frame. A GP object in a render warns until Combined and Depth passes are on.

## VSE

1. `scene.sequence_editor_create()` first, then `se.strips.new_movie / new_image / new_sound / new_effect / new_scene`.
2. Crossfades need alternating channels with overlapping frames. Avoid `bpy.ops.sequencer.*` headless.
3. Long edits: render an image sequence and join with ffmpeg; the default container is not mp4.

## Traps

- `ad.action = act` alone animates nothing; set the slot.
- Constraint, driver and modifier motion previews fine and exports static.
- Actions without a user and without fake user are not saved.
- Unsaved files break `//` render paths.
- Rewriting keys after baking: `fc.update()` or the handles stay stale.
