# Blender UV And Bake

Purpose: Unwrap, pack and bake in Blender so maps land where intended, at a stated texel density, and prove it in pixels.

Read when:
- Unwrapping, packing UVs, baking procedurals to maps, hi-to-lo normals, or baking lighting for a web scene.

Skip when:
- Sourcing or generating textures (→ [blender-texturing](blender-texturing.md)); node recipes and colour rules (→ [blender-shading](blender-shading.md)); runtime use of baked maps (→ [threejs-lookdev](threejs-lookdev.md)).

Inputs:
- Meshes with transforms applied, target map set, texture budget ([shared-performance](shared-performance.md)).

Produces:
- Unwrapped UVs, baked images (PNG or EXR) that passed the pixel gates, and a material rebuilt from them.

Read with [blender-scripting](blender-scripting.md) and [blender-version-traps](blender-version-traps.md). All ops here need Edit Mode or a bake context and return `FINISHED` on failure: re-measure ([blender-scripting](blender-scripting.md) Verify).

## Contents

- UV · Texel density · Bake setup · Procedural to maps · High to low · Lighting bake for web · Pixel gates · Scripts · Traps

## UV

1. Apply scale, merge doubles, remove back faces first; most bake bugs start there.
2. ALWAYS pass `method=` to `uv.unwrap` (the default is `CONFORMAL`; also `ANGLE_BASED`, `MINIMUM_STRETCH`). Hard-surface: `uv.smart_project(angle_limit=1.15, island_margin=0.02)`. Organic: mark seams, `ANGLE_BASED`. Hard edges above ~60° are seams when baking.
3. Order: unwrap → `uv.average_islands_scale` → `uv.pack_islands(rotate=True, rotate_method='CARDINAL', margin_method='FRACTION', margin=…, shape_method='AABB')`.
4. Gap in pixels = resolution / 128 (8, 16, 32 px at 1K, 2K, 4K); FRACTION margin = gap / (2 × resolution). Community formula, untested here. Bake margin 8–16 px with `margin_type='EXTEND'` stops mip bleed.
5. `shape_method='CONCAVE'` packs tighter but is slow (0.4 s on a 500-face mesh here; community reports 2–25 s on real assets): AABB while iterating, CONCAVE for the final.
6. Coverage ≥ 70 % is a good target; the packer often lands 55–62 % on organic shapes (community).
7. UDIM is not web: glTF and three.js read one 0–1 space. Split into materials instead.
8. Mirrored or stacked UVs: move the duplicate exactly +1 in U during the bake, and back after.

## Texel density

Canonical home. `px/m = resolution × sqrt(total_uv_area / total_face_area_m2)` over the object's faces (measured on an unwrapped Suzanne, 2048 px: 524 px/m).

| Asset | px/m (community) |
|---|---|
| Hero, close-up | 1024–2048 |
| Mid-ground prop, third-person | 512 |
| Mobile, background | 256 |

Keep one density per scene: spread across objects ≤ 1.3×; 10–20 % off is invisible.

## Bake setup

1. Cycles only (`scene.render.engine = 'CYCLES'`). Low-poly: scale applied, a UV layer, no overlapping islands, padding ≥ 8 px.
2. In every material of the bake target add an Image Texture node, set its image, make it the active node AND select it. Measured: not selected, or no image node, returns `CANCELLED` ("No active and selected image texture node found").
3. Data images are `Non-Color`, colour images `sRGB` ([blender-shading](blender-shading.md)); create them before baking. Baked images are not saved: `img.save_render(path, scene=sc)` honours `scene.render.image_settings` (PNG, 16-bit if wanted).
4. `view_from` lives on `scene.render.bake` (`ABOVE_SURFACE` or `ACTIVE_CAMERA`), not on the operator. Operator params: `type, pass_filter, margin, margin_type, use_selected_to_active, max_ray_distance, cage_extrusion, use_cage, cage_object, normal_space, uv_layer, use_clear`.  Bake `type` values include `COMBINED, AO, NORMAL, ROUGHNESS, EMIT, DIFFUSE`; there is no metallic.
5. Test at 512, ship 1024 (2048 close-up heroes). Samples: normal 16, AO 64–256.

## Procedural to maps

Procedural materials do not export, so bake each parameter to its own image and rebuild the material from the maps. This reads node values, not light: 2–8 samples are enough, and flat maps become a scalar instead of an image.
- Albedo: `type='DIFFUSE'`, `pass_filter={'COLOR'}`. Roughness: `type='ROUGHNESS'`. Normal: `type='NORMAL'`, `normal_space='TANGENT'`.
- Metallic has no bake type: route the value to an Emission shader and bake `type='EMIT'`. Measured: Metallic 0.8 baked as 0.8 grey.
- One new image per map; switch the node's image between bakes; restore the surface link afterwards.

## High to low

1. Select high, then low, and make LOW the active object; `use_selected_to_active=True`. Low has the Non-Color image node ready.
2. `cage_extrusion` above the farthest the high pokes out; `max_ray_distance` larger. Measured on a sphere displaced 0.08: extrusion 0.15 / ray 0.3 gave a rich normal map; ray 0.001 returned `FINISHED` with a flat-looking map (std halved).
3. One global extrusion fails on thin parts close together (ears on a head): use `use_cage` with `cage_object`, or bake per pair. Explode touching parts.
4. Multires on the low gives an almost flat normal: set render level 0. Triangulate as the engine will; bake normals before decimating.

## Lighting bake for web

Static lights and objects → Cycles bake; anything moving or relit → PBR maps and live light. The output type sets the runtime material: Background output = `MeshBasicMaterial` (exact light, no shadows); Principled = `MeshStandardMaterial` that double-lights; Emission = `MeshStandardMaterial` with an emissive map (the usual compromise). Runtime wiring: [threejs-lookdev](threejs-lookdev.md).

1. Prepare: delete faces the camera never sees, Face Orientation all blue, apply scale, merge doubles, single-user data, join static objects sharing a UV map. Split a big scene across several textures.
2. A second UV map named `bake`, non-overlapping, one atlas, consistent density, margin 16 px at 4K (24 if edges show). Keep the first UV for the material.
3. Light with a neutral world (HDRI about 0.4, or a sky); add dirt and wear.
4. `COMBINED` (or `DIFFUSE` with Direct + Indirect only, for a separate lightmap). Samples 128–1,024. `scene.render.bake.view_from = 'ACTIVE_CAMERA'` and `EXTEND` cut seam trouble.
5. Bake 4K then downscale; 1K is enough for a lightmap.
6. Save as 32-bit float EXR with the image set `Non-Color` first. Measured, 0.5 in: `Non-Color` came back 0.5; an sRGB-tagged image saved with `save_render` came back 0.214; `Linear Rec.709` saved with `save()` came back 0.735. Radiance `.hdr` also works for lightmaps; PNG or 16-bit looks faded.
7. Denoise in the compositor, not in the bake: in-bake denoise left black seam lines (practitioner, not in the Blender manual). Then EXR → PNG → KTX2 ([asset-pipeline](asset-pipeline.md)).
8. Metals: `lightMap` has no effect at metalness 1; bake only diffuse parts and ship separate metalness and roughness. Never carry RGB lighting in the glTF occlusion slot. Do not re-enable already baked objects while baking the rest.
9. Match view transforms with three first ([design-lookdev-presets](design-lookdev-presets.md)). SimpleBake (PAID add-on) wraps these steps: propose, never install unasked.

## Pixel gates

Read pixels, not thumbnails.
- Normal mean blue < 0.5: rays hit the far side. Good normals sit near (0.5, 0.5, ~0.99).
- Near-flat or exactly flat map: rays missed (distance too small, wrong active object).
- All-white AO: distance too small. Black holes or NaN: bad UVs or cage.
- Inverted pixels that do not move with extrusion: geometry problem.

## Scripts

Contract: [blender-scripting](blender-scripting.md); flags: each `--help`.
- `uv_check.py [--objects A,B] [--res 2048] [--target PX_PER_M] [--lightmap] [--json PATH]`: overlap, bounds, density spread (FAIL above 1.3x), coverage, margin. Exit 1 on FAIL; modifiers ignored.
- `bake_maps.py --object LOW --maps albedo,roughness,metallic,normal,ao,emit,combined --res N --out-dir DIR [--high HI --extrusion F --ray F --cage NAME] [--rebuild COPY.blend]`: the setup above plus the pixel gates; exit 1 on a flat, NaN or CANCELLED map (`--allow-flat` for a legitimate constant). Never saves your `.blend`; `--rebuild` writes a copy wired to the maps (not ao, combined) for `export_web.py`.

## Traps

- 5.0+ shares UV selection across maps; `BMLoopUV.select` code fails (community).
