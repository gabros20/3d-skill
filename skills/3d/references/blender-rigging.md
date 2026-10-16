# Blender Rigging

Purpose: Build a rig that deforms cleanly and exports to the web: armature, Rigify, IK/FK, weights, shape keys, verification.

Read when:
- A mesh needs a skeleton, skinning, weights, Rigify, IK/FK or shape keys, or a skinned GLB deforms wrongly.

Skip when:
- Keying, clips, NLA, bake-to-keys (→ [blender-animation](blender-animation.md)); exporting the result (→ [blender-export](blender-export.md)); bpy patterns and gates (→ [blender-scripting](blender-scripting.md)); renamed API (→ [blender-version-traps](blender-version-traps.md)).

Inputs:
- The mesh (or its `.blend`), target (web GLB, render, both), character or mechanism.

Produces:
- An armature that passes `assets/blender/rig_check.py`, with a pose-test render as evidence.

## Rig only what moves

A rigid mechanism or a product part needs no skin: parent the object to a bone (or keyframe the object). Skin only meshes that bend. Web budgets: [shared-performance](shared-performance.md).

## Readiness gate (before any bone)

1. Scale and rotation applied on the mesh, shape keys included; unit scale 1.0; ~1.8 m for an adult.
2. Feet at Z=0, centred on X, facing -Y, symmetric. Humanoids in an A-pose (arms 30-45 deg down) deform shoulders better than a T-pose.
3. Loose parts, doubles and inner faces removed (→ [blender-modeling](blender-modeling.md)). Do voxel remesh and topology work first: they destroy vertex groups.
4. Armature object scale 1, rotation 0.

## Bones

- Create in Edit mode via `armature.edit_bones.new(name)`; set `head`, `tail`, `parent`, `use_connect`. Keep the returned edit bone; the reference dies on leaving Edit mode.
- Joints sit at the centre of the volume they rotate, not on the surface. Give elbows and knees a 1-3 deg pre-bend toward their natural direction, else the IK plane is undefined.
- Roll: set after placement with `bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')` on selected bones (works headless). Mirrored bones need mirrored roll; `.L`/`.R` suffixes drive mirror tools.
- Clear `use_connect` before re-parenting a connected bone, or its head jumps.
- Every bone that should deform has `use_deform=True`; controls and helpers `False`.

## Rigify

1. Enable: `addon_utils.enable('rigify', default_set=True)`, then assert `addon_utils.check('rigify')[1]`. Without `default_set=True` it fails with `KeyError` and returns None; a failed enable never raises.
2. `bpy.ops.object.armature_human_metarig_add()` (exists only after step 1); fit joints to the mesh (the add only places a template).
3. Metarig is the source of truth: fix problems in the metarig or Rigify parameters and regenerate. Never hand-edit the generated rig.
4. Generate headless: object mode, `view_layer.objects.active = meta; meta.select_set(True)` (deselect others), then `bpy.ops.pose.rigify_generate()`. `temp_override` fails with `AssertionError: ... active_object == self.obj` (verified: 706 bones, 160 deforming, object `rig`).
5. On failure read the first Rigify error line ("bone position is disjoint", eye corners expected) and fix the metarig.
6. Rules: arm = exactly 3 bones; leg 4 + heel; spine 3+; `super_copy` = one bone.
7. The generated `rig_ui.py` needs Auto Run in a GUI session; untested headless.

## IK/FK and constraints

- IK: `pb.constraints.new('IK')`, set `target`, `subtarget`, `chain_count`. A pole or target parented inside its own chain jitters.
- IK/FK blend is exactly 0 or 1; values like 0.86 give unreadable deformation.
- Twist: segmented deform bones with Copy Rotation 1.0 / 0.66 / 0.33 / 0.1 per segment. Preserve Volume, Corrective Smooth and B-Bone effects do not reach glTF.

## Weights

1. Bind: select mesh, then armature active, `bpy.ops.object.parent_set(type='ARMATURE_AUTO')`. Non-deform bones get no groups (verified).
2. ALWAYS measure afterwards: it returns `FINISHED` even when heat fails. Verified: a loose island far from any bone left 8 unweighted vertices with `FINISHED`; a simple closed cylinder weighted fully at scales 1, 0.01, 0.001. Suspects not reproduced here (untested): non-manifold meshes, inner faces, duplicates, bones outside the volume, tiny scale.
3. Fallbacks, in order: fix the mesh and re-bind; weight a voxel-remeshed proxy and transfer with `bpy.ops.object.data_transfer` (`data_type='VGROUP_WEIGHTS'`, `vert_mapping='NEAREST'`, `use_object_transform`; enums verified, transfer result untested); envelope (`ARMATURE_ENVELOPE`) as a rough base; paint by hand.
4. Rigid parts (eyes, teeth, armour, product pieces) get weight 1.0 on one bone, never painted. Clothes: apply a Data Transfer from the body, then clean.
5. Clean for the web, in this order: `vertex_group_limit_total(limit=4)`, `vertex_group_normalize_all(lock_active=False)`, `vertex_group_clean(group_select_mode='ALL', limit=0.01)`; run on the mesh as active object.
6. Paint rules: strength 0.1-0.2 with Auto Normalize; 2-3 bones per seam; blend over 1-2 edge loops (firm beats rubbery); strip opposite-side weights at armpits and crotch; mirror with `object.vertex_group_mirror`.
7. Modifier order: Armature after Mirror and before Subdivision; Corrective Smooth after Armature.
8. `VertexGroup.remove` with an out-of-range index crashed 5.2.1: look up by name.

## Shape keys and correctives

- `obj.shape_key_add(name='Basis')` first, then keys. A new key's `value` is 1.0 (verified); set 0 before keying.
- Corrective: pose, `bpy.ops.object.modifier_apply_as_shapekey(modifier=...)` or sculpt the key, then drive `key.value` from the bone: driver variable `TRANSFORMS`, `transform_type='ROT_X'`, `transform_space='LOCAL_SPACE'`, expression remapped to 0..1 (verified `is_valid`).
- Morph targets export to glTF (verified); keyframing them is [blender-animation](blender-animation.md).

## Verify

`blender -b rig.blend --python-exit-code 1 --python assets/blender/rig_check.py -- [--armature NAME] [--max-influences 4] [--max-bones 256] [--tol 0.01] [--json PATH]`

Exit 1 (FAIL) on unweighted vertices, influences over the limit or a deforming mesh with no Armature modifier; WARN on more than `--max-bones` bones; also reports non-normalised sums, empty groups, groups without a deform bone, deform bone count, unapplied scale and modifier order. Then pose the rig at range-of-motion extremes (arms overhead, knees and elbows fully bent, neck turn), render with a [blender-channels](blender-channels.md) evidence render and look: numbers passed once while the render showed broken arms. Collapse below 85% or bulge above 125% of rest limb width is a defect (heuristic).

## Web export

1. Export deform bones only: glTF `export_def_bones=True` (verified: joints were only the `DEF-` bones), FBX `use_armature_deform_only`. Rigify's 706 bones are never shipped.
2. Control rig → game skeleton: a `root` bone plus the DEF hierarchy, constrained to the controls, then bake the animation to it (→ [blender-animation](blender-animation.md)).
3. `export_influence_nb=4` matches the 4-influence rule; glTF skins carry JOINTS_0/WEIGHTS_0 only (4). Bone-count budget and skinning cost: [shared-performance](shared-performance.md). Export settings and checks: [blender-export](blender-export.md); GLB audit after: [asset-pipeline](asset-pipeline.md).
4. No bone scale animation for engines; use quaternion rotation.

## Traps

- `parent_set` success is not skinning success: measure.
- Mesh parented with unapplied scale gets a double transform.
- Skinned mesh looks fine posed but explodes in three.js: check scale on armature and mesh.
- Editing the generated Rigify rig is lost on regeneration.
