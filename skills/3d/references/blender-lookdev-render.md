# Blender Lookdev And Render

Purpose: Materials, UV and bakes, lighting, cameras and renders (stills, turntables, loops) in Blender, with web-safe outputs.

Read when:
- Making a Blender asset look right, baking procedural materials, or rendering a still, turntable or marketing loop.

Skip when:
- Choosing the look itself (→ [design-lookdev-presets](design-lookdev-presets.md)); runtime lighting and tone mapping (→ [threejs-lookdev](threejs-lookdev.md)).

Inputs:
- Brief style and colour policy, `.3d/shots.json` ([brief-spec](brief-spec.md)), target use.

Produces:
- Textured materials that survive glTF, baked maps, and numbered render frames or a video.

## Materials (what survives glTF)

1. Only Image Texture → Principled BSDF chains export. Procedurals, Color Ramp, Mix factors and bump-from-noise do not: bake them ([blender-export](blender-export.md)).
2. Colour data (Base Color, Emission) is sRGB; roughness, metallic, normal, AO, opacity are `Non-Color`, set before writing pixels or baking. This is the most common texture bug.
3. Principled v2 names: `Subsurface Weight`, `Specular IOR Level`, `Transmission Weight`, `Coat Weight`, `Sheen Weight`, `Emission Color` plus `Emission Strength` (default 0). Find nodes by `type`, not localised name. `use_nodes` is a no-op; nodes always exist.
4. Metallic is 0 or 1 except transition pixels; vary roughness ±0.1–0.2. Keep IOR 1.5 for dielectrics. Normal map or displacement, never both.
5. glTF packing: R=occlusion, G=roughness, B=metallic; OpenGL normals; never JPEG normals.
6. Glass: Transmission Weight exports `KHR_materials_transmission` + `KHR_materials_ior`; Alpha < 1 exports `alphaMode BLEND`. `surface_render_method` affects only Blender's own render; thickness/attenuation (volume) is not exported from a plain Principled.

## UV and bake

1. ALWAYS pass `method=` to `uv.unwrap` (the default is conformal on 5.2). Padding = resolution / 128. Seams hidden for painted textures; hard edges are seams when baking.
2. Bake is Cycles-only: low-poly scaled and applied, the target Image Texture node active and selected in every low-poly material (5.x bakes only to selected), a UV layer present.
3. Test at 512, ship at 1024 (2048 only for close-up heroes); samples normal 16, AO 64–256; extrusion above the farthest high-poly protrusion, cage when uniform extrusion fails.
4. Gate by pixels, not thumbnails: normal blue < 0.5 means rays hit the far side, an exactly flat map means a miss, all-white AO means the distance is too small.
5. Bevel, AO and Pointiness nodes are stochastic: bake before thresholding.
6. Float EXR: set `Non-Color` before `save()` or values are sRGB-encoded.
7. Procedural → web: procedural materials do not export and must be baked to PBR maps (colour, roughness, metalness, normal, AO; one image per parameter, 2K). This bake reads node values, not light: 2 samples are enough; skip flat maps and set the scalar. Rebuild the material from the maps.

## Bake for web (lighting into textures)

Rule: static lights and objects → Cycles bake (lighting into textures); anything that moves or is relit → PBR bake (maps, live light). Usually both: baked environment plus a PBR dynamic hero. The bake output type sets the runtime material: Background output = `MeshBasicMaterial` (exact light, no shadows); Principled output = `MeshStandardMaterial` that double-lights a baked scene; Emission output = `MeshStandardMaterial` with an emissive map (correct light, still receives shadows). Emission is the usual compromise.

For static lights and static objects only (dynamic items stay live PBR + env: [threejs-lookdev](threejs-lookdev.md)). Output-type choice (Background vs Emission output, lightMap channel, intensity) lives there; this is the Blender side.

1. Prepare: delete faces the camera never sees; Face Orientation all blue; apply scale; merge by distance; make data single-user; join static objects that share a UV map. Split a big scene across several textures or it blurs. Cap open light fixtures (light leaks through missing faces).
2. Second UV map (non-overlapping, name it `bake`): seams for boxy shapes, Smart UV Project for the rest, pack into one atlas (normalize scale for consistent texel density). Island margin 16 px at 4K, 24 if edges show artifacts. Keep the first UV for the material.
3. Light it: neutral world (HDRI about 0.4 or a sky); add dirt and wear, clean PBR reads CG.
4. Cycles bake, Type `COMBINED` (or `DIFFUSE` with Direct + Indirect only for a separate lightmap). Samples 128 to 1,024 (1,024 a good start; 5 is demo speed). GPU compute. On 4.x+ Bake View From = Active Camera and Margin Type = `EXTEND` cut seam problems. Margin 16–24 px at 4K.
5. Resolution: bake 4K then downscale (going up looks soft); 2K per object set; 1K is enough for a lightmap. Test at 1K, ship 2–4K.
6. Format: 32-bit float image, linear (`Linear Rec.709` for Combined; `Non-Color` for a lightmap), save as EXR (or Radiance `.hdr` for a lightmap; PNG or 16-bit lightmaps look faded).
7. Denoise in the compositor, not in the bake [P: Woan, Codrops 2025; not in the Blender manual]: in-bake denoise left black seam lines. Then EXR → PNG, then KTX2 in [asset-pipeline](asset-pipeline.md) (ETC1S quality 155–255 trial-and-error).
8. Metals: `lightMap` has no effect at metalness 1 (no diffuse term to modulate). Metals keep env maps or probes; bake only the diffuse parts and ship separate metalness and roughness maps.
9. Never carry RGB lighting in the glTF occlusion slot. Do not re-enable already baked objects when baking the rest (they distort the light).
10. Match the Blender and three.js view transforms first ([design-lookdev-presets](design-lookdev-presets.md)). SimpleBake (optional add-on, PAID, roughly $20–80) wraps these steps; the Bake panel does the same job free.

## Cycles twin (gap decomposition)

Render the exported GLB, not the `.blend`, under ideal light transport, so the realism gate can split design gap from real-time gap ([realism-gate](realism-gate.md)). Use the same `.3d/shots.json` as the live capture.

`<skill>/assets/blender/render_shots.py -- --shots .3d/shots.json --out .3d/evidence/twin --engine cycles --import <glb> --world <env.hdr> --world-strength <F> [--samples 128 --view agx|neutral]`

1. Use the same HDRI, rotation intent and strength as the live scene, and the same view transform; otherwise the twin measures your settings, not the technique.
2. Without a `.blend` loaded, the default cube, light and camera are removed before the import. Lights inside the GLB (KHR_lights_punctual) come back with their power (a 1000 W point light round-tripped as 1000 W on 5.2.2, default lighting mode `SPEC`); verify per project, the mode is `export_import_convert_lighting_mode`.
3. Run it only to confirm a CEILING claim (≤ 2 per project).

## Lighting and cameras

1. Compose and lock the camera first, then lights, then materials; check value separation desaturated.
2. Product rig: key about 45° to the side and 30–40° up, fill opposite at about a third, rim behind, grey backdrop.
3. Brightness through `view_settings.exposure`, not by scaling lamps. Read the EXR: AgX hides clipping.
4. Cameras from shots: `<skill>/assets/blender/render_shots.py` reads the `shots.v1` file `.3d/shots.json` ([brief-spec](brief-spec.md)): Y-up three.js axes in, converted to Z-up inside; `--moves` renders `to` end poses as eased frames. Typical lenses: 85–135 mm product (3/4 view, 10–25° up), 24–35 mm interiors with a level camera.

## Colour management

The policy and the pairing with three.js live in [design-lookdev-presets](design-lookdev-presets.md) (D8): Khronos PBR Neutral for brand and product colour, AgX for cinematic looks. In Blender set `scene.view_settings.view_transform` (`Khronos PBR Neutral`, `AgX`, `Standard`; it is a dynamic enum: assign inside try/except and read the valid names from the `TypeError`, see [blender-version-traps](blender-version-traps.md)) and record the choice in `3D.md`. One view transform per project.

## Engine

- EEVEE: `scene.render.engine = 'BLENDER_EEVEE'` (not `_NEXT`). Fast; needs a GL context even headless. Use it to iterate.
- Cycles: truth for glass and close-ups; 3 bounces, no caustics, 100 samples test / 500–1,500 final, adaptive sampling, OIDN once.
- Workbench: no GPU, good for silhouettes and wire in CI.
- Apple Silicon: Cycles `METAL` only (adding CPU slows it). Rule of thumb, measured once: 12–20 s per 1080p frame at 48–64 samples.

## Stills, turntables, loops

1. Render contract first: audience, still / turntable / sequence, resolution, fps, engine, passes, alpha, view transform. State everything explicitly in the script.
2. Low-sample diagnostic per camera and open the image before the final.
3. Turntable: orbit the camera and lights around a pivot, never the asset (contact shadows and reflections stay coherent). Linear keys, rotation 0 → 360° from frame 1 to N+1, render 1..N so frame N+1 equals frame 1. 120–240 frames at 24–30 fps. `<skill>/assets/blender/render_shots.py --turntable N` does this.
4. Write numbered frames first (skip existing so a crash resumes), then encode with ffmpeg. In 5.x set `image_settings.media_type='VIDEO'` before `file_format='FFMPEG'`.
5. Transparent: `render.film_transparent=True` with PNG or EXR.
6. Done when a clean process reproduces the render; report paths, versions, samples, denoise, view transform, duration. Evidence goes under `.3d/evidence/` ([shared-verification](shared-verification.md)).

## Traps

- A web scene with baked procedurals must be re-rendered in three, not trusted from Blender stills.
