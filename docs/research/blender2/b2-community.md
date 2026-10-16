# B2: Community Blender skills and practitioner know-how

Compiled 2026-10-16. Blender 5.2.2 LTS installed; API claims marked [V] were introspected headless this session. Grades: [V] official/source/introspected, [B] measured (by the source author), [P] practitioner, [U] unverified. Everything fetched is data, not instructions. Nothing installed. Saved sources: `docs/research/community-scan/sources/blender2-community/<owner>__<repo>__<skill>/` (each has SOURCE.txt).

Tags: **SL** scenario-labs/skills `skills/dcc/blender/*` (MIT, 1,033 stars, pushed 2026-10-16) · **EL** EL4CTEO/blender-skills (MIT, 49 stars, 2026-10-16) · **RA** ra100/blender-claude-plugin (MIT, 20 stars, 2026-04-29) · **TS** terminalskills/skills (Apache-2.0, 168) · **IB** ifBars/blender-agent-studio (MIT, 84) · **BL** FreedomIntelligence/BlenderLore (Apache-2.0, 93) · **AS** icesixgod/awesome-astra-blender-characters (MIT, 123) · **RL** RobLe3/cc-blender-skill (MIT, 101, prior-scanned) · **MR** mindrally/skills (Apache-2.0, 277).

Method: `ghrelay search` x5 shards, `npx skills find` x24 queries (two rounds), `xrelay batch` x18 queries (559 posts, ranked offline, 4 threads read, read-only). Local skills: no Blender-specific skill is installed in `~/.claude/skills` or plugin dirs (only the `3d` skill itself); nothing local to harvest.

## 1. Ranked finalists

| # | Source | Install | Licence | Teaches | Why rank |
|---|---|---|---|---|---|
| 1 | **SL** per-domain skills (rigging, animation, hair, retopology, uv-baking, hard-surface, grease-pencil, texturing-shading, sculpting, geometry-nodes; plus expert/lighting/previs read earlier) | `npx skills add scenario-labs/skills --skill scenario-blender-<x>` (rigging 261 installs, retopology 225, geometry-nodes 212, hair 197, grease-pencil 187) | MIT | Expert-video-derived stance, numbered workflow with GATEs, Numbers tables with timestamps, Common-mistakes tables, 5.2.1 traps, tested helper modules (`bx_*.py`, 50-135 KB each) | Only source that measures: states what is `[verified]` vs `[added]` vs expert-sourced, and records failures (e.g. "numbers passed while render showed broken arms"). Best procedures in every domain it covers |
| 2 | **EL** `blender-*` (14 skills read: character-rigging, facial-shapekeys, animation, sculpting, simulation, retopology-uv, texture-baking, geometry-nodes, pbr-materials, pipeline-automation, addon-development, workflow-recipes, plus earlier core/export/asset-qa/game-opt) | `npx skills add EL4CTEO/blender-skills`; plugin marketplace JSON present; CI tests per skill | MIT | Compact (5-7 KB each), game/engine-handoff bias, headless-safe scripts returning JSON, 5.x API-change notes | Best for the **game/web delivery** path; short enough to inline; every skill has a `tests/test_*.py` |
| 3 | **BL** `blender-pipeline` knowledge/*.md | `git clone`; `skills/blender-pipeline/knowledge/{rendering-and-dynamics,editing,generation,operations-and-knowledge}.md` | Apache-2.0 | Rule/Applies-when/Verify format distilled from tutorial videos; deterministic QA metrics for renders and dynamics | Best **verification-gate** phrasing; fills the "how to accept a render/sim" gap |
| 4 | **IB** `blender-simulation-workflow`, `-animation-workflow`, `-character-workflow`, `-asset-validation` | `ifBars/blender-agent-studio` plugin installer | MIT | Cache-as-build-step discipline, simulation contract, evidence cadence | Strong process; thin on numbers |
| 5 | **TS** `blender-compositing`, `-vse-pipeline`, `-motion-capture`, `-addon-dev`, `-grease-pencil`, `-render-automation` | `npx skills add terminalskills/skills` | Apache-2.0 | 5.x-aware guideline lists (compositor, VSE, mocap retarget, extensions) | Only source for compositing and VSE API traps. Guidelines are accurate on spot-check [V] |
| 6 | **RA** `blender-physics-simulation`, `-animation-rigging`, `-shader-nodes`, `-compositing-nodes`, `-python-scripting` | `ra100/blender-claude-plugin` | MIT | Code cookbooks (rigid/cloth/Mantaflow/soft body/particles; drivers; NLA) | Useful as API snippets; not procedures. 5.1 notes (Smooth FCurve modifier, Apply to Basis) [V] |
| 7 | **AS** astra-character-workflow | `icesixgod/awesome-astra-blender-characters` | MIT | Reference-first character reconstruction: 9-view reference set, evidence-based acceptance, anti-"script ran = done" | Good process for image-to-character; Chinese-language text |
| 8 | **RL** blender-animation/materials/modeling/uv-texturing | `RobLe3/cc-blender-skill` | MIT | Prior scan covered; not re-read beyond fetch | Redundant with SL/EL |
| 9 | **MR** blender-python-addon | `mindrally/skills` | Apache-2.0 | Add-on structure | Superseded by EL addon-development (extension manifest era) |
| Skip | arjun988 (94 thin skills, prior verdict), edemaistre (13 skills with SL's exact names, **no licence**, likely derivative), xliuxjianx (no licence; NPR skills only 4-5 KB), ptrthomas (no licence), capybala18 (279 KB single SKILL.md, building/car anatomy, off-topic here), jablonkai (4 stars) | | | | |

## 2. Per-domain best procedures

Number convention: steps are the source's order; GATE = stop-and-verify.

### 2.1 Rigging (SL rigging, EL character-rigging; AS for characters)
1. **Model check first**: scale applied (shape keys too), feet Z=0, centred X, facing -Y, ~1.8 m adult; T- or A-pose (A-pose 30-45 deg deforms shoulders better) (SL, EL). GATE: `model_check == []`.
2. **Place joints at the centre of the volume they move**, not on the anatomical skeleton; give knees/elbows a **1-3 deg pre-bend** (the chain curvature defines the IK plane); hinge rolls on one local axis (SL, from CGDive/Demeter).
3. **Metarig is the source, generated rig disposable**: every fix goes in metarig bones/Rigify params/post-generate script; regenerate keeps control names (SL). Rigify metarig rules: arm exactly 3 bones, leg 4 + heel, spine 3+, `super_copy` 1 bone. Rigify is **disabled on factory startup** [V: `addon_utils.check('rigify') == (False, False)`]; enable it before use.
4. Generate with the metarig **selected and active** (EL: `temp_override` insufficient); on failure read the first Rigify error line ("bone position is disjoint", "Expected 2 eye corners") and fix the metarig (SL).
5. **Skinning**: `parent_set` returns FINISHED while heat weighting failed; measure unweighted vertices and empty groups, fall back to voxel proxy (H/180, then H/90, H/45) + Data Transfer (SL, EL `bind_mesh.py`). Strip opposite-side weights (armpits/crotch leak). Rigid parts (eyes, teeth, armor) get 1.0 to one bone, never painted. Clothes get applied (not live) Data Transfer from the body.
6. **Weights rules**: <=4 influences for games (<=8 PC), normalised, drop <0.01; 2-3 bones per seam; mix 0.5 at strength 1; brush strength 0.1-0.2 with Auto Normalize (SL, EL). Firm beats rubbery.
7. **Twist**: 4 twist bones per segment, Copy Rotation 1.0/0.66/0.33/0.1 (SL); Preserve Volume, Corrective Smooth and B-bones are Blender-only, so games use segmented DEF bones.
8. **Stress test** in range-of-motion poses and look at renders; thresholds: collapse <0.85, bulge >1.25, leak >0.001 H, strain 0.5-1.6 (SL, [added]). "Numbers passed while a render showed broken arms": always open the render.
9. **Correctives**: sculpt in posed state (`modifier_apply_as_shapekey`), drive 0..1 from bone local rotation (`TRANSFORMS`, `ROT_X`, `LOCAL_SPACE`) (EL, SL). X: @pierrick_picaut advertises corrective bones on Rigify [P, course only].
10. **Game skeleton**: `root` + DEF-only hierarchy, DEF- prefix stripped, constrained to the control rig, then bake (EL). Roblox R15 / Unity Humanoid / UE mannequin name sets in EL.
- Armature modifier order: after Mirror, before Subdivision (SL); Corrective Smooth after Armature (EL).
- Traps: IK/FK switch exactly 0 or 1 (0.86 gives unreadable deformation); IK target parented inside its chain jitters; re-parenting a connected bone moves the head (clear `use_connect` first); `shape_key_add` leaves new keys at value **1.0** in 5.2.x [V: printed 1.0]; `VertexGroup.remove` with out-of-range index crashes 5.2.1 (SL [verified]); Rigify `rig_ui.py` needs Auto Run in a GUI.
- Licence: MIT both.

### 2.2 Animation (SL animation, EL animation, TS mocap, RA)
1. **Stay stepped long ("blocking plus")**: add hand breakdowns while CONSTANT; never convert the whole blocking to Bezier. Key every main control on every key pose, copy each pose to the end of its hold ("pillars"), spline body only; face/fingers stay stepped. Measured: naive Bezier conversion drifted 84% of the next move across a hold; pillars held at 0 (SL [B]).
2. **Exception**: a contact inside continuous motion (landing) is not a hold; pillaring cut speed at impact 0.101 to 0.007 m/frame (SL [B]).
3. Handle types are timing decisions: AUTO_CLAMPED for holds, AUTO only for settles/overshoot, VECTOR for contacts/take-offs, FREE for burst spacing. Heel curve eased during contact slid the foot 5.8 cm per step (SL [B]).
4. Numbers: snap 2-3 frames after a hold; hold 6 frames to read; eye dart 1-2, brow 3-10; ease rule 80% of remaining distance; real gravity at 24 fps = 0.01703 m/frame^2; foot slip <1 mm; IK leg extension <0.99 while bent (SL).
5. **Check arcs in camera pixels**, not normalised coordinates (aspect squeezes x) (SL).
6. **Game rules** (EL): one action per clip with fake user; loops identical first/last frame; the F-curve CYCLES modifier does **not** export (bake); root bone carries translation/yaw; do not animate bone scale for engines; quaternion for game bones.
7. **Bake control rig to export skeleton** with visual keying (captures IK/constraints/drivers), then mute the target's constraints; one muted NLA track per clip so FBX/glTF export all (EL `bake_action.py`). glTF: `export_force_sampling` is the safe default.
8. **Mocap retarget without add-ons**: match rest pose first (T vs A matters most), COPY_ROTATION per bone, COPY_LOCATION on hips scaled by leg-length ratio, self-bake, delete constraints (EL, TS). BVH is often cm: `global_scale=0.01`. Clean with `graph.decimate` (ratio 0.3-0.5), `graph.butterworth_smooth`, or the new **SMOOTH F-curve modifier** [V: `SMOOTH` in modifier enum; RA says Gaussian blend, 5.1].
9. 5.x data model [V]: `action.fcurves` absent; slots/layers present; use `anim_utils.action_ensure_channelbag_for_slot`, or just `keyframe_insert`. One layer per action (`layers.new` raises, SL); layer via NLA ADD/COMBINE. `pose.apply_to_basis` exists [V].
- Headless limits (SL): `anim.keyframe_insert` fails; `pose.breakdown` needs explicit prev/next frame; `render.opengl` refuses, so playblast = Workbench render; `matrix_world` stale until `view_layer.update()`.
- X practitioner: @rewind02 (6.5k engagement, [P]) says Opus-in-Blender rigs/animates when told "keep it realistic, rig it for smooth animation" in the same prompt; render 480p preview before final (1080p 1-2 h); check animation step by step. Weak evidence; consistent with SL's gate-per-stage.

### 2.3 Texturing and UV (SL uv-baking, texturing-shading; EL retopology-uv, texture-baking, pbr-materials)
1. Apply scale first ("fixes the vast majority" of bake problems). Clear non-manifold, doubles, back faces.
2. **Seams follow the texturing method**: 2D paint wants few hidden seams; 3D paint/bake wants more seams, less stretch (SL). Game rule: every hard edge (>~60 deg) must be a UV seam (EL `--seams-from-sharp 60`).
3. **Always pass `method=` to unwrap**: default is CONFORMAL [V: default `CONFORMAL`, enum ANGLE_BASED/CONFORMAL/MINIMUM_STRETCH]; Minimum Stretch gave most even density on Suzanne (spread 1.38), conformal failed by area 5.89 (SL [B]). `uv.unwrap` returns FINISHED even when it failed; check unsolved faces and folding islands.
4. **Straighten then equalise then pack without tilt**: Follow Active Quads, pack with CARDINAL; margin as FRACTION = gap/(2*res); gap = res/128 (8/16/32 px at 1K/2K/4K) (SL). EL gives 2k->8 px, 4k->16 px.
5. **Texel density**: SL (px/cm) FPS 10.24, weapon 20.48, third-person 5.12, top-down 2.56; EL (px/m) 1024-2048 hero, 512 third-person, 256 mobile. Same density per asset (spread <=1.3); 10-20% mismatch invisible. Coverage >=70% (studio 75%). Blender packer on organic characters yields 55-62% (SL [B]).
6. Mirrored/stacked UVs: move duplicates exactly +1 U during the bake, back afterwards (EL, SL).
7. **Bake**: low has UVs, no overlaps, padding >=8 px; hard edges = seams; triangulate as the engine will; high covers low and pokes out slightly; explode touching parts. Extrusion must exceed the farthest the high sticks out; **one global extrusion fails on thin close parts (ears on a head)**; use cage or adaptive/per-pair. Test bake 512, final 2048; samples 16 normal, 128 AO (SL, EL).
8. Judge bakes in pixels: blue <0.5 = rays hit far side; exactly flat = rays missed; all-white AO = distance too small; inverted pixels that don't move with extrusion = geometry problem (SL). Low carrying Multires gives almost flat normal map: render levels 0 for bake.
9. Bake silent failures: target image node must be **active and selected** in every material or bake returns CANCELLED; images not auto-saved (EL, SL).
10. **PBR rules** (EL, SL agree): metallic binary; base colour is albedo (dielectric sRGB ~30-240, metal 180-255); data maps Non-Color; roughness varied +-0.1-0.2 with grunge; normal OR displacement never both (SL, per Cycles lead); micro detail in roughness not bump; OpenGL normals except Unreal/Substance-DX; ORM = R AO, G rough, B metal. Engine packing table in EL (Unity URP: metal R + smoothness A).
11. Procedural to engine: only Image Texture -> BSDF chains export; bake procedurals via Emission, >=30 samples (SL). Bevel/AO/Pointiness are Cycles-only and stochastic (SL [B]); EEVEE shows no Bevel edges.
12. Edge wear/dirt as one reusable node group with per-material strength, all procedural (X @hayashimon1, [P]); print-like signage made by rendering a 2D layout top-down to a texture, then adding fade/yellowing/lamination/peel.
13. Trim sheets / decals: only EL covers (unwrap strips, move islands to trim rows; islands may exceed 0-1 in U for tiling). No community skill found with real decal/trim procedure: **gap**. AI texture generation: see B3 (`b3-texturing.md`); AS gives reference-image provenance rules (save prompt, source, mark generated areas as design completion, never as measurement).
- Traps: 5.0+ UV selection shared across maps (`BMLoopUV.select` code fails, EL); `pack_islands` with CONCAVE can take 2-25 s headless, use AABB while iterating (EL); `material.use_nodes` deprecated; `mat.diffuse_color` is viewport-only.
- X: @amatsukisaku [P] hard-separate mouth-line colours with a seam + separate UV island, otherwise bleed and ugly edges when the mouth moves.

### 2.4 Procedural / Geometry Nodes (SL geometry-nodes, EL geometry-nodes)
1. A **field is a deferred question**, evaluated by the consuming node on that node's domain; `Capture Attribute` freezes a field before topology changes (SL, EL).
2. Domain changes interpolate; Boolean rule is float>0 = true, so a subdivided vertex-group selection bleeds; decide with Compare + epsilon (SL).
3. **Simulation only when history matters**; if state does not depend on the previous frame, drive from Scene Time (scrubs, sub-frames) (SL). Loops (repeat/for-each) are last resort; built-ins use acceleration structures.
4. Everything is object-local: world directions need Self Object > Object Info > Invert Matrix > Transform Direction (SL).
5. Instances are cheap: realise as late as possible, or use glTF instancing (`export_gpu_instances`) (EL). Expose `Seed`; use Random Value with ID/Index field (EL). Store `UVMap` explicitly or it is dropped; add `Set Shade Smooth`/Smooth by Angle or GN output loses smoothing.
6. **Reusable tools**: expose every dependency as a group input, never hard-reference scene objects; test the asset on a second object (Suzanne test); `is_modifier` + `asset_mark()` (SL).
7. 5.2 API: `mod.properties.inputs.<identifier>.value` replaces `mod["Socket_2"]` [V: `properties` attr present]; Random Value/Compare sockets changed (dynamic typed Min/Max/Value) so look up by name and `--describe` (EL). `nt.interface.new_socket` (not `inputs.new`).
8. Sim zones must be stepped frame-by-frame in order headless (works for GN zones and point caches) or baked per modifier (`mod.bakes`, `object.geometry_node_bake_single`) (EL). Jump-to-late-frame equals stepped result only after bake (SL gate).
9. Numbers (SL, Thommes BCON23/26): heat melt 300 K ambient / 2000 K source / heating 0.05 / cooling 0.01 per frame; cloth asset defaults Substeps 5, Constraint Steps 15, Collision Radius 0.01, Tearing Threshold 1.2; drip 0.01/frame, normal mix 0.1 (0.5 "looks like baking bread").
- Nodes exist in 5.2.2 [V]: `GeometryNodeXPBDSolver`, `GeometryNodeForeachGeometryElementInput`. Licence MIT.

### 2.5 Shading node recipes (SL texturing-shading, EL pbr-materials, TS/RA minor, X)
- Masks, not painted colour: build every effect as grayscale mask into Mix/HSV factor; masks need contrast (pull Color Ramp stops); mask frequency vs vertex density: vertex colours for broad soft masks, images for fine detail (SL).
- Skin: roughness 0.68-0.72 (lips ~0.4), pores Voronoi Smooth F1 scales 100/200, SSS scale **0.005-0.04 m in 5.2** (older tutorials' 0.02-0.15 look waxy), SSS high on ears/nose/lids/lips (SL [B]).
- Bump Distance ~0.001 and Strength 0.1-0.2 for fabric; displacement Scale 0.2, Midlevel 0.5, 16-bit source (SL).
- Judge in Standard view, mid-grey background, Base Color black to read roughness, hard backlight and light from below (SL). View transforms: AgX default, Khronos PBR Neutral for asset parity, Standard for UI/pixel match (EL).
- Hair material: Principled Hair BSDF in Cycles; **EEVEE needs explicit colours** (SL hair).
- Stylised/cel: X @Mix3Design pack of six cel setups [P, product post, not read]; Jan van den Hemel toon shader posts [P]; xliuxjianx NPR skills unlicensed and short. **Gap**: no verified NPR procedure.

### 2.6 Physics and simulation (EL simulation, IB simulation, RA, SL GN)
1. **Simulation contract first** (IB): type, solver, timeline, scale, forces, colliders, domain, cache dir, resolution, deliverable; state onset/peak/settle frames. Cache is a build step; never overwrite an approved bake.
2. Real scale and `scene.render.fps` before tuning; **change one causal parameter group at a time, invalidate and rebake the smallest interval** (IB, EL).
3. Solver choice (EL): rigid = Bullet; clothing = classic Cloth + Collision; new node cloth/hair = Cloth Dynamics / Hair Dynamics assets (5.2 XPBD, experimental: no self-collision, no built-in wind, interfaces may change; pin version); liquids/smoke = Mantaflow.
4. Rigid body: mass = volume x density (wood 500-700, concrete 2400, steel 7850, plastic 950 kg/m^3); CONVEX_HULL for dynamic, MESH only for passive concave; substeps 10, iterations 10, margin 1 mm; don't start interpenetrated (EL). `rigidbody.bake_to_keyframes` needs UI, so sample `matrix_world` per frame.
5. Cloth: even quad density, 2-5 cm edges for clothing, no ngons; pin vertex group weight 1; collider thickness 1-5 mm; apply as shape key or bake Alembic/point cache.
6. Mantaflow: preview 64, final 128-256; `cache_type="ALL"` for headless; `fluid.bake_all()` under domain context override; slow, test coarse first.
7. Background-mode traps (EL): point caches fill by stepping frames from `frame_start`; `ptcache.bake_all` needs valid context; changing anything invalidates caches.
8. Validation (IB, BL): reopen saved scene in a fresh process, inspect same frames; separate facts: mechanism enabled, forces/keys, cache range, bake complete, visible post-impulse behaviour. Tunnelling = thin collider/too few substeps/too fast.
9. Cloth/Particles/Soft body API cookbooks: RA physics (17 KB). Hair particles: see 2.7.

### 2.7 Particles and hair (SL hair; X)
1. Prepare: finish topology and **non-overlapping UVs** first (hair binds to UV space), apply scale (density counts local area) (SL).
2. **Guides get 2 points** while placing (3 for short fur, 8 long, human long resampled to 15); space guides evenly and **always mask Interpolate** (SL).
3. Density per m^2 must be huge and radius drops with it: long fur 1,000,000/m^2 at ~0.2 mm; work at 4% viewport amount; coverage sanity density x pi x r^2 ~0.13 (SL).
4. Randomise **per curve, not per point**: 80% of strands no frizz, strays 10% with strong noise; Trim with Replace Length off + Random Offset 5 mm, masked (SL, Thommes).
5. Human hair: grow on a separate **hair cap split along the part**; keep Part by Mesh Islands on (21% of children crossed the part with it off, 0% on); density map part 1.0, base 0.5 (SL [B]).
6. Layer order for long fur: Noise, Curl (radius 2 cm), Frizz with negative Shape, Clump (guide distance 1 cm, 1 mm sub-clump), final Frizz, Trim, Rotate; each layer must earn its place in an A/B render.
7. Judge **at full density and in pose**; animated hair keeps Hair Dynamics last.
8. Game cards: card subdivision 1 per 20 cm; convert to mesh and export glTF; hair cap beneath; UVs in half-tile (SL).
9. Headless limit: `sculpt_curves.brush_stroke` has no exec; Comb/Add/Density strokes are GUI-only (SL). X @nobishiro_pingu [P]: curve hair shows strand shadow noise; transfer normals from a subdivided sphere (3-4 levels) to smooth per-strand shading.

### 2.8 Sculpt, retopology, bake (SL sculpting/retopology, EL sculpting/retopology-uv)
1. **Never enter Sculpt Mode headless**: operators crash `-b` (EL, SL [B]); use object-level ops (voxel remesh, symmetrize, multires, smooth) and GN SDF-grid booleans.
2. Voxel ladder (SL, head height H): blockout H/40, primary H/65-110, secondary H/130-235, detail ~H/330; shape before 100k faces, detail ~500k. EL: 2 m character `remesh=0.02`.
3. Fix mass upstream; planes only restate (SL). Asymmetry/expression on a shape key, basis stays neutral.
4. `voxel_remesh` destroys UVs/vertex groups/multires: do before UV and rigging; multires and topology edits don't mix (EL).
5. **Retopo method per part** (SL): eyes/mouth/brows via ring carving with upper=lower loop counts; limbs via tubes; static props QuadriFlow whole; QuadriFlow gave 0 eye/mouth rings on the test sheep. **Auto-remesh fits static/scan/bake-only; deforming hero meshes need hand loop budgets** (both SL and EL).
6. Edge-flow rules: 3 loops per bending joint, poles (valence 3/5) only where nothing moves, loops close on themselves, triangles only in non-deforming hidden spots. Game character tri budgets (EL): mobile 5-15k, console/PC third-person 30-80k, hero 100k+; SL: head 2-3k tris, body 5-6k.
7. Judge the **subdivided** surface; a snapped cage shrinks inside when subdivided; fit so the subdivided surface matches (SL `fit_subdiv`).
8. Handoff: `X_high` -> `X_low` -> UV -> bake (2.3 steps 7-9). SL measured: aggressive fit scored better numbers but looked lumpier than the human cage; render wins over metric.
- 5.x API: `brush.sculpt_tool` renamed `sculpt_brush_type` [V], automasking moved in 5.2 (EL). Licence MIT.

### 2.9 Hard surface (SL hard-surface; EL hardsurface-modeling not read in depth)
Cut first, bevel after, normals last: Booleans above an angle-limited micro bevel (30 deg, Harden Normals, Miter Outer Arc), Weighted Normal at the bottom. Two bevels: weight-limited design bevel (8-12 segments) before cuts; micro bevel after. Every wall/step/groove wider than 2x micro width [verified]. Solver EXACT (Float left 16 non-manifold edges on a coplanar cutter). If Harden Normals/Weighted Normal change nothing, the face is not flat. Micro bevel width real-size: ~3 mm body, 1 mm small parts, 0.1 mm collars; default 0.5% of largest dimension. Judge in shiny matcap and close up.

### 2.10 Compositing, Grease Pencil, VSE (TS, SL grease-pencil, BL)
**Compositing** (TS, spot-checked [V]): `scene.compositing_node_group` is the tree (None until created); `scene.node_tree` AttributeError in 5.x [V]; `scene.use_nodes` is deprecated [V]. Tree needs a Group Output with a Color first input or the frame saves uncomposited (or black if unlinked). `node.width` is the editor width (4.x `glare.width` code fails silently). Duplicate socket names (Color Balance `Lift`): use identifiers, never indices. Enable render passes on the View Layer before linking. Set `scene.render.compositor_device = 'CPU'` headless [V attribute exists]. Prefer `film_transparent` + Alpha Over to Keying when you control the 3D. Denoise right after Render Layers; multilayer EXR for all passes. Sources: TS (Apache-2.0), RA.
**Grease Pencil** (SL): GP object per physical element parented, layers by graphic logic; interpolate only "sculpted" pairs (same stroke count/order/points); fill is geometry (`fill_id != 0`, even-odd holes), not material; new layers have `use_lights=True` and take ambient from `World.color` (0.05), so unlit flat colour needs `use_lights=False` (verified); Line Art `radius` is the line width (points get radius/2); every visible layer needs a key at/before `frame_start`; ortho camera for multiplane; bake procedural output to editable strokes. Width px = 2 x radius / px_size.
**VSE** (TS): `sequence_editor_create()` first [V method exists]; use `strips.new_movie/new_image/new_sound/new_effect`, avoid `sequencer.*` ops in background; crossfades need alternating channels with overlapping frames; fade audio by keying `strip.volume`; set `ffmpeg.format='MPEG4'` for mp4 (default MKV); render long edits as image sequence then ffmpeg. `left_handle_offset`/`right_handle_offset` trim.
**Render QA** (BL): before semantic review export diagnostics (counts, coverage, luminance, clipping, edge contact); evaluate foreground separately from canvas; use a fixed camera containing the full motion envelope; thresholds apply only to the named contract.

### 2.11 Add-on development (EL addon-development; TS addon-dev; MR)
Copy template (manifest, `__init__`, operators, ui); manifest id lowercase_underscore permanent, tagline <=64 chars no trailing period, SPDX GPL-3.0-or-later for bpy code; `blender --command extension validate|build|install-file`; **relative imports only**, no `bl_info`; no network/file access at import/register, declare `[permissions]`, check `bpy.app.online_access`; ship `.whl` in `./wheels/` (5.1 no longer loads user site-packages); prefix classes `MYTOOL_OT_`, `_PT_`, `_PG_`; unregister in reverse (classes, props, menus, handlers, timers, keymaps, draw handlers); `bgl` removed in 5.0 [V: no module]; never store `bpy.types.ID` refs in globals (crash after undo/load), store names or `session_uid`. Licence MIT/Apache-2.0.

### 2.12 Automation and batch (EL pipeline-automation, SL expert, TS render-automation, BL)
`blender -b [file] --factory-startup --python-exit-code 1 -P script.py -- args` (flag order matters, left to right); return JSON lines, never parse logs (5.0 log format changed); shard `--shard i/N` over N processes; never write into source folder, use `save_as_mainfile(copy=True)`; idempotent scripts with named prefixes; `bpy` wheel (Python 3.13, ~300 MB) for pytest/CI, no GPU; EEVEE needs GPU/EGL even headless; record `bpy.app.version_string` + `build_hash`; GPU in containers needs NVIDIA runtime. Practitioner loop (X): @hayashimon1: reference image first, blockout, then boolean/cloth detail, procedural wear node group, then "closeup critique" rounds; @shion_takk (21 replies, claims ~$455 API cost, 98% Opus 5.5 medium, 50 prompts, 8-hour runs): **requirements definition is most important**, a rule "stop improvising, look up the catalogue spec", route each object to bpy-built vs Tripo-generated by an explicit criterion, audit every object for interpenetration/floating, add small motion to scene, compact context at 50-70% [P, self-reported]. @rewind02: do not model chairs from scratch, pull assets (BlenderKit) and let the model arrange them [P].

## 3. API traps consolidated (cross-source, verified where marked)
| Trap | Source | Verified |
|---|---|---|
| `action.fcurves` gone; use slots/layers/channelbag | EL, SL, TS | [V] absent; slots, layers present |
| `scene.node_tree` gone; `compositing_node_group` | TS | [V] |
| `scene.use_nodes` deprecated, removed in 6.0 | warning at runtime | [V] |
| `mod["Socket_2"]` -> `mod.properties.inputs.<id>.value` | EL, SL | [V] `properties` exists |
| `sculpt_tool` -> `sculpt_brush_type` | EL | [V] |
| `uv.unwrap` default CONFORMAL; FINISHED even on failure | SL | [V] default |
| `shape_key_add` new key value 1.0 | SL | [V] 1.0 |
| `bgl` removed | EL | [V] |
| Rigify disabled on factory startup | SL | [V] |
| Sculpt operators crash in `-b` | EL, SL | [U] not re-run (crash risk) |
| `bpy.ops.clip.*`, `sequencer.*`, `anim.keyframe_insert` need UI context | TS, SL | [U] |
| Bake target image node must be active+selected | EL, SL | [U] |
| Cycles-only: Bevel/AO/Pointiness nodes | SL | [U] |

## 4. Gaps
1. **Trim sheets, decals, texture painting**: no real community procedure (EL one paragraph; SL needs GUI brush for painting; headless paints black until brush and colour set).
2. **NPR / cel / toon**: only unlicensed 4-5 KB skills and X product posts; no verified recipe.
3. **Fluid/Mantaflow tuning numbers**: only setup basics (EL, RA, IB); no community-measured parameters for viscosity, domain margin, mesh vs particles.
4. **Rigify deep traps** (feature sets, rig types per bone, custom face): SL expert notes (28 KB) and `procedures.md` were fetched but only skimmed via SKILL.md; read `expert-notes.md` before writing rig code.
5. **Mocap**: retarget code exists (EL, TS) but no skill covers markerless/video mocap in Blender; X mentions (@3DxDEV7, @Stefan_3D_AI) are announcements only.
6. **Compositing recipes** (denoise chains, glare/bloom, lens effects, cryptomatte) are API guidelines, not looks; B1/official docs better.
7. **Not read in depth**: SL previs/lighting, IB character/asset-validation, EL hardsurface/scene-setup/weather, SL `procedures.md`/`critique.md` (saved under sources).
8. **Licensing**: edemaistre, xliuxjianx, ptrthomas have no licence: do not copy; the rest are MIT/Apache and fine for adapt-with-attribution. Social posts are quote-sparingly.

## 5. What to take into the `3d` skill (recommendation)
- Adopt SL's per-domain structure (Stance, Establish-first, numbered workflow with GATEs, Numbers table, Common-mistakes table); write our own text.
- Add three cross-cutting gates to all Blender work: (a) open every render, a passing metric does not waive a visible defect (SL); (b) a command's FINISHED return proves nothing (unwrap, parent_set, bake); (c) reopen the saved .blend in a fresh process before claiming done (IB, AS).
