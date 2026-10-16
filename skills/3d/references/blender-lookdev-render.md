# Blender Lookdev And Render

Purpose: Light, frame and render in Blender (stills, turntables, loops, transparent product shots) with verified 5.2 settings and compositing.

Read when:
- Setting up lights, world, camera, render settings, passes or compositing, or running a render from the CLI.

Skip when:
- Materials (→ [blender-shading](blender-shading.md)); UV and bakes, including lighting bakes (→ [blender-uv-bake](blender-uv-bake.md)); choosing the look (→ [design-lookdev-presets](design-lookdev-presets.md)); runtime lighting (→ [threejs-lookdev](threejs-lookdev.md)).

Inputs:
- Brief style and colour policy, `.3d/shots.json` ([brief-spec](brief-spec.md)), target use.

Produces:
- Numbered frames, stills or alpha PNGs, and the settings that made them.

## Contents

- Lighting and world · Cameras · Colour · Engines · Passes and compositing · Stills and loops · CLI · Twin · Traps

## Lighting and world

1. Compose and lock the camera, then lights, then materials; check value separation desaturated.
2. Product rig: key ~45° to the side and 30–40° up, fill opposite at about a third, rim behind, grey backdrop.
3. Brightness through `view_settings.exposure`, not lamp scaling. Read the EXR: AgX hides clipping.
4. Lights: `use_temperature` + `temperature` (K) on any light; area light `spread` narrows a softbox; `ob.light_linking.receiver_collection` / `blocker_collection` isolate a hero.
5. World: an HDRI with Mapping Z rotation and Background strength. For a plain camera background over HDRI light, mix a colour in with Light Path `Is Camera Ray`.
6. Transparent product shot: `ob.is_shadow_catcher = True` on the floor, `render.film_transparent = True`, PNG RGBA. Measured: floor alpha 0, the contact shadow comes out black at alpha ~0.9. `view_layer.cycles.use_pass_shadow_catcher` adds a separate `Shadow Catcher` output.

## Cameras

- Focus: `cam.dof.use_dof`, `focus_object` = an Empty, `aperture_fstop` 2.8–5.6 for product work.
- Shake: a Noise F-modifier on the camera channels.
- Shots: `<skill>/assets/blender/render_shots.py` reads `shots.v1` (`.3d/shots.json`): Y-up three.js axes in, Z-up inside; `--moves` renders `to` poses as eased frames. Lens defaults: [brief-spec](brief-spec.md).

## Colour

Policy and three.js pairing: [design-lookdev-presets](design-lookdev-presets.md) (Khronos PBR Neutral for brand and product, AgX for cinematic). Set `scene.view_settings.view_transform` (dynamic enum: assign in try/except and read the valid names from the `TypeError`, [blender-version-traps](blender-version-traps.md)); 5.2.2 offers `Standard, ACES 1.3, ACES 2.0, Khronos PBR Neutral, AgX, Filmic, Filmic Log, False Color, Raw`. One transform per project, recorded in `3D.md`.

## Engines

- EEVEE: `'BLENDER_EEVEE'`. Fast, needs a GL context. Settings: `use_raytracing`, `taa_render_samples`, `use_shadows`, `shadow_resolution_scale`, `use_fast_gi`, `volumetric_samples`. Weak at caustics, SSS through thin parts and Bevel/AO nodes. Iterate here.
- Cycles: truth for glass and close-ups. Defaults: total 12, diffuse 4, glossy 4, transmission 12, transparent 8. `sample_clamp_indirect` (default 10) tames fireflies; keep caustics off unless needed; `use_light_tree` on; adaptive `adaptive_threshold` 0.01 final, 0.05 preview (starting points). Glass and liquid need transmission ≥ 8; foliage and hair raise transparent bounces.
- Denoise: OpenImageDenoise is the only denoiser on Apple (`denoiser = 'OPENIMAGEDENOISE'`); `denoising_input_passes = 'RGB_ALBEDO_NORMAL'`, `denoising_prefilter = 'ACCURATE'` for finals. Test ~100 samples, final 500–1,500.
- Also: `render.use_persistent_data` for animations, `render.use_simplify` + `simplify_subdivision_render` for heavy scenes.
- Workbench: no GPU; silhouettes and wire in CI.
- Apple Silicon: Cycles `METAL` only (CPU added slows it). Measured once: 12–20 s per 1080p frame at 48–64 samples. First-render kernel compile: [blender-scripting](blender-scripting.md).

## Passes and compositing

Enable passes on the view layer before linking: `use_pass_z` (output `Depth`), `use_pass_mist`, `use_pass_normal`, `use_pass_diffuse_color`, `use_pass_ambient_occlusion`, `use_pass_cryptomatte_object|material|asset`. Names: [blender-version-traps](blender-version-traps.md). Multilayer EXR: `image_settings.media_type = 'MULTI_LAYER_IMAGE'`.

```python
ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); sc.compositing_node_group = ng
ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
rl, out = ng.nodes.new("CompositorNodeRLayers"), ng.nodes.new("NodeGroupOutput")
gl = ng.nodes.new("CompositorNodeGlare"); gl.inputs["Type"].default_value = "Fog Glow"
ng.links.new(rl.outputs["Image"], gl.inputs["Image"]); ng.links.new(gl.outputs[0], out.inputs[0])
sc.render.compositor_device = 'CPU'   # default is GPU; CPU for headless
```

Without a Group Output the frame saves uncomposited. Options are sockets in 5.x: Glare `Type` takes `Bloom, Ghosts, Streaks, Fog Glow, Simple Star, Sun Beams, Kernel`; Blur `Size` is a 2-vector.

| Effect | Nodes (all exist in 5.2.2) |
|---|---|
| Bloom, fog glow | `CompositorNodeGlare` |
| Chromatic dispersion | `CompositorNodeLensdist` (`Dispersion`, `Distortion`) |
| Vignette | `CompositorNodeEllipseMask` → `CompositorNodeBlur` → `ShaderNodeMix` (`data_type='RGBA'`, `blend_type='MULTIPLY'`) against the image. Measured: corners 0.40 → 0.07, centre unchanged |
| Cut-out over a colour | `CompositorNodeAlphaOver` (`Background`, `Foreground`) on a `film_transparent` render |
| Denoise a pass chain | `CompositorNodeDenoise` (`Image`, `Albedo`, `Normal`) right after Render Layers |
| Masks | `CompositorNodeCryptomatteV2` (`matte_id`) |

Measured: a Glare tree changed the rendered PNG against the same scene with the tree detached. Mix sockets are picked by identifier ([blender-shading](blender-shading.md) Traps). There is no `CompositorNodeComposite` or `CompositorNodeMixRGB`.

## Stills and loops

1. Render contract first: audience, still / turntable / sequence, resolution, fps, engine, passes, alpha, view transform; state it in the script.
2. Low-sample diagnostic per camera; open the image before the final.
3. Turntable: orbit camera and lights around a pivot, never the asset. Linear keys, 0 → 360° from frame 1 to N+1, render 1..N; 120–240 frames at 24–30 fps. `render_shots.py --turntable N`.
4. Write numbered frames (skip existing so a crash resumes), then encode with ffmpeg; `image_settings.media_type='VIDEO'` before `file_format='FFMPEG'`.
5. Done when a clean process reproduces the render; report paths, versions, samples, denoise, transform, duration, under `.3d/evidence/` ([shared-verification](shared-verification.md)).

## CLI

`blender -b scene.blend --factory-startup -E CYCLES -o //out/f_#### -F PNG -x 1 -s 1 -e 120 -a -- --cycles-device METAL`

Settings flags go BEFORE the action (`-a` or `-f N`, last). Measured: with `-a` first, `-o -s -e` were ignored and five default frames landed in `/tmp`. `#` characters set frame padding; `-- --cycles-device CPU|METAL` is read by Cycles. Estimate total time as one final frame × N.

## Cycles twin

Render the exported GLB, not the `.blend`, so [realism-gate](realism-gate.md) can split design gap from real-time gap, with the same `shots.json`:

`<skill>/assets/blender/render_shots.py -- --shots .3d/shots.json --out .3d/evidence/twin --engine cycles --import <glb> --world <env.hdr> --world-strength <F> [--samples 128 --view agx|neutral]`

1. Same HDRI, rotation, strength and view transform as the live scene, or the twin measures your settings.
2. With no `.blend` loaded the default cube, light and camera are removed first. GLB lights return with power (1000 W round-tripped as 1000 W on 5.2.2, mode `export_import_convert_lighting_mode`); verify per project.
3. Only to confirm a CEILING claim (≤ 2 per project).

## Traps

- Stills from Blender do not prove the three.js scene; re-render in three.
