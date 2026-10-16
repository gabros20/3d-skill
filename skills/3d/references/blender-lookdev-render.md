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
6. Glass: `surface_render_method` `DITHERED` or `BLENDED`; exports as KHR transmission/ior/volume.

## UV and bake

1. ALWAYS pass `method=` to `uv.unwrap` (the default changed to conformal in a measured 5.2 run). Padding = resolution / 128. Seams hidden for painted textures; hard edges are seams when baking.
2. Bake is Cycles-only: low-poly scaled and applied, the target Image Texture node active and selected in every low-poly material (5.x bakes only to selected), a UV layer present.
3. Test at 512, ship at 1024 (2048 only for close-up heroes); samples normal 16, AO 64–256; extrusion above the farthest high-poly protrusion, cage when uniform extrusion fails.
4. Gate by pixels, not thumbnails: normal blue < 0.5 means rays hit the far side, an exactly flat map means a miss, all-white AO means the distance is too small.
5. Bevel, AO and Pointiness nodes are stochastic: bake before thresholding.
6. Float EXR: set `Non-Color` before `save()` or values are sRGB-encoded.
7. Procedural → web: bake via Emission, 30+ samples, then rebuild the material from the maps.
8. Baked lighting is a separate UV layer and atlas, never packed in the glTF occlusion slot.

## Lighting and cameras

1. Compose and lock the camera first, then lights, then materials. Value separation first; check desaturated.
2. Size and distance are the controls: key at least head-sized relative to the subject; every light motivated; rim on the key side. Product rig: key about 45° to the side and 30–40° up, fill opposite at about a third, rim behind, grey backdrop.
3. Brightness through `view_settings.exposure`, not by scaling lamps. Read the EXR: AgX hides clipping.
4. Cameras from shots: `assets/blender/render_shots.py` reads the `shots.v1` file `.3d/shots.json` ([brief-spec](brief-spec.md)): Y-up three.js axes in, converted to Z-up inside; `--moves` renders `to` end poses as eased frames. Typical lenses: 85–135 mm product (3/4 view, 10–25° up), 24–35 mm interiors with a level camera.

## Colour management

The policy and the pairing with three.js live in [design-lookdev-presets](design-lookdev-presets.md) (D8): Khronos PBR Neutral for brand and product colour, AgX for cinematic looks. In Blender set `scene.view_settings.view_transform` (`Khronos PBR Neutral`, `AgX`, `Standard`; names come from the OCIO config, check the enum) and record the choice in `3D.md`. One view transform per project.

## Engine

- EEVEE: `scene.render.engine = 'BLENDER_EEVEE'` (not `_NEXT`). Fast; needs a GL context even headless. Use it to iterate.
- Cycles: truth for glass and close-ups; 3 bounces, no caustics, 100 samples test / 500–1,500 final, adaptive sampling, OIDN once. Keep EEVEE within about 30% of Cycles on the subject.
- Workbench: no GPU, good for silhouettes and wire in CI.
- Apple Silicon: Cycles `METAL` only; about 12–20 s per 1080p frame at 48–64 samples.

## Stills, turntables, loops

1. Render contract first: audience, still / turntable / sequence, resolution, fps, engine, passes, alpha, view transform. State everything explicitly in the script.
2. Low-sample diagnostic per camera and open the image before the final.
3. Turntable: orbit the camera and lights around a pivot, never the asset (contact shadows and reflections stay coherent). Linear keys, rotation 0 → 360° from frame 1 to N+1, render 1..N so frame N+1 equals frame 1. 120–240 frames at 24–30 fps. `assets/blender/render_shots.py --turntable N` does this.
4. Write numbered frames first (skip existing so a crash resumes), then encode with ffmpeg. In 5.x set `image_settings.media_type='VIDEO'` before `file_format='FFMPEG'`.
5. Transparent: `render.film_transparent=True` with PNG or EXR.
6. Done when a clean process reproduces the render; report paths, versions, samples, denoise, view transform, duration. Evidence goes under `.3d/evidence/` ([shared-verification](shared-verification.md)).

## Traps

- Compositor tree is `scene.compositing_node_group` in 5.x ([blender-version-traps](blender-version-traps.md)).
- A web scene with baked procedurals must be re-rendered in three, not trusted from Blender stills.
