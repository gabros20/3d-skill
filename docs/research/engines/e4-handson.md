# E4 — Hands-on: what survives Blender 5.2.2 → glTF → three.js r186.1 vs Babylon.js 9.31.0

All grades [B] (measured 2026-10-16, Apple M3 Pro, Chrome headless via Playwright, WebGL2/ANGLE-Metal) unless stated.
Contact sheet (Cycles / EEVEE / three / Babylon, COMPAT-light export): `docs/research/engines/e4-contact.png`.
Scratch (scene, scripts, all screenshots): `/private/tmp/claude-501/-Users-tamas-Documents-Work-Projects-Eagle-eagle-website/07e0d037-d35a-42a8-9494-fafedac02fe9/scratchpad/e4/`
(`build.py` scene, `export.py`, `render.py`, `three.html`, `babylon.html`, `cap.py`; `ref_cycles.png`, `ref_eevee.png`, `three_{default,compat,raw}.png`, `babylon_{default,compat,raw}.png`, `sheet8.png`).

## Test setup
- 8 spheres (4 back, 4 front), cube animated 2 s (rotation), GN mesh-line of 12 instanced cubes, floor, point 1000 W, spot 1000 W, camera 40 mm, one HDR (Blender `courtyard.exr` saved as `env.hdr`, same file in all four renders), view transform Khronos PBR Neutral (Blender) = `NeutralToneMapping` (three) = `TONEMAPPING_KHR_PBR_NEUTRAL` (Babylon), exposure 1.
- Exporter: Khronos glTF Blender I/O v5.2.40. Options used: `export_format=GLB, export_lights=True, export_cameras=True, export_animations=True, export_apply=True, export_image_format=AUTO, export_yup=True`, plus `export_gpu_instances=True, export_gn_mesh=True` for the main file; `export_import_convert_lighting_mode` in {SPEC (default), COMPAT, RAW} for the light variants. The full operator has ~100 props (introspected); the ones above are the ones that changed results.
- Environment alignment: three needs rotation 0 for the Blender equirect (pixel MAE vs Cycles on the sky strip 0.4/255). Babylon needs `HDRCubeTexture.rotationY = PI/2` (MAE 3.8; at 0/PI/3PI/2 it is 65-121). Env rotation set on the scene texture is applied to the lighting too (verified by reflections).

## Support matrix (measured)

| Feature (Blender input) | Blender export | three r186.1 | Babylon 9.31 | Look vs Cycles |
|---|---|---|---|---|
| Brushed metal: Principled Anisotropic 0.85 | `KHR_materials_anisotropy` (strength only; rotation 0 omitted; no tangent export by default) | Loaded, streaked highlight, no warning | Loaded; highlight shape differs from three | Both read as "brushed" but differ from Cycles' reflection; ok qualitatively. Region MAE 40 (three) / 35 (Babylon) vs Cycles; EEVEE 31 |
| Clearcoat car paint (Coat 1, coat rough 0.02) | `KHR_materials_clearcoat` | Good, two-lobe highlight | Good | Region MAE 5 / 7 (EEVEE 5): matches |
| Sheen fabric | `KHR_materials_sheen` (colour, roughness) | Good soft rim | Good | MAE 19 / 22 (EEVEE 26); lighter edge than Cycles |
| Glass: Transmission 1, IOR 1.5, Volume Absorption | `KHR_materials_transmission` + `ior`; **volume ONLY with a "glTF Material Output" group**, see gotchas | Green tinted via attenuation, believable | Same | MAE 27 / 24; EEVEE 60 and wrong (opaque mirror ball without raytracing) |
| Iridescence: Principled Thin Film 550 nm | `KHR_materials_iridescence` only with the glTF output group (Iridescence Factor); exports `iridescenceIor`, `thicknessMaximum` | Loaded, effect subtle/near-invisible on a dark metal ball | Loaded, same | Cycles shows only a dark metal ball too; MAE 7 / 6. This case did not discriminate engines |
| Emission colour (1,.45,.1), strength 5 | `emissiveFactor` + `KHR_materials_emissive_strength` 5 | OK; saturates to peach under Neutral | Same | MAE 0.6 / 1.4: matches |
| Dispersion | Only `KHR_materials_dispersion` with glTF output group (Dispersion 5) AND volume present (code: no volume ext = no dispersion ext) | Loaded; coloured fringe on the glass sphere interior | Loaded; stronger fringe | Cycles/EEVEE render none (Principled has no dispersion). Cannot be called "right"; engines agree with each other |
| Textured PBR: albedo + normal map + ORM-style roughness/metal | baseColor, normalTexture, metallicRoughness PNGs (3 textures) | Good | Good | MAE 3.2 / 3.5; checker + bumps match |
| Point 1000 W | `KHR_lights_punctual`; value depends on lighting mode (below) | Loaded as PointLight | PointLight, intensity copied verbatim | See light table |
| Spot 1000 W, 50 deg, blend 0.3 | spot inner 0.305 / outer 0.436 rad | OK | OK | cones match; no shadows |
| Animation (cube rotation, 2 s) | 1 sampler, 49 keys, key times 0.0417-2.0417 s (frame/fps, **not slid to 0**) | Plays; mixer pose at t=0.25 s equals Babylon's to 7 digits | Plays (frames 2.5-122.5 at 60 fps) | Cube moves in both (quaternion differs between two samples 0.6 s apart) |
| GN instanced array (12 cubes) | **Default export: dropped completely** (empty node, "Mesh 'Plane.001' has no primitives"). With `export_gn_mesh=True`+`export_gpu_instances=True`: `EXT_mesh_gpu_instancing` TRANSLATION/ROTATION/SCALE x12 | `InstancedMesh` count 12 | `thinInstanceCount` 12 | Identical to Blender's row. The instancing *source* object is also exported (visible extra cube) unless hidden/excluded |
| Camera | exported only with `export_cameras=True` (default False) | `gltf.cameras[0]`, yfov 0.4958 | `FreeCamera`, same fov | framing identical to Cycles to the pixel |
| Shadows | not in glTF at all | none unless `castShadow` set manually | none unless shadow generator | Cycles/EEVEE have soft shadows; web renders have none (largest visual gap on the floor) |

Console warnings: **none** about unsupported extensions in either engine. three logged only deprecation warnings (`RGBELoader` -> `HDRLoader`, `THREE.Clock` -> `THREE.Timer`). Babylon logged all 11 extensions as loaded (`EXT_mesh_gpu_instancing`, `KHR_lights_punctual`, clearcoat, iridescence, anisotropy, emissive_strength, sheen, ior, transmission, volume, dispersion).
Extensions in the final GLB: `KHR_materials_{clearcoat,transmission,emissive_strength,anisotropy,ior,sheen,volume,iridescence,dispersion}`, `KHR_lights_punctual` (marked **required**), `EXT_mesh_gpu_instancing`. `gltf-transform inspect`: 14 meshes/primitives, 3 PNG textures, 1 animation. Skill `glb-report`: 31.8k tris, ~11 draws (static estimate does not count the 12 GPU instances), hero budget PASS, 601 KB.

## Light intensity mapping (the biggest practical finding)

Exporter's `export_import_convert_lighting_mode` (introspected default `SPEC`) turns 1000 W into:

| Mode | glTF intensity | three | Babylon | Result vs Cycles (global MAE /255, sphere luminance ratio range) |
|---|---|---|---|---|
| SPEC (default) | 54351.4 cd | `PointLight.intensity` 54351 (physical candela, `decay` 2) | `intensity` 54351, mode AUTOMATIC | blown out: MAE 48.8, ratios 1.2 to 2.0, floor pure white |
| RAW | 1000 | 1000 | 1000 | still blown out: MAE 42.2 / 41.8, ratios 1.07 to 1.9 |
| COMPAT | 79.58 (=W/4pi) | 79.58 | 79.58 | best: MAE 16.7 (three) / 15.7 (Babylon) vs 15.4 for EEVEE itself; sphere ratios 0.98-1.2 |

- three and Babylon behave the same: both take the candela number literally; **neither rescales for the HDR/environment exposure**, so a SPEC export needs an exposure around 1/683 and a matching IBL scale, which in practice nobody does. For environment-lit web scenes use COMPAT or hand-set intensities.
- Floor brightness matches Cycles within 3% (ratio 1.03) in COMPAT for both engines, so the IBL path is consistent: tone mapper + env map + exposure were equivalent across the two web engines.

## Per-sphere difference vs Cycles (mean abs error, 0-255, 38 px circle, COMPAT)

| Sphere | EEVEE | three | Babylon |
|---|---|---|---|
| 1 brushed metal | 30.8 | 39.6 | 35.0 |
| 2 car paint | 5.1 | 5.2 | 6.8 |
| 3 sheen | 25.5 | 19.3 | 22.1 |
| 4 glass+volume | 59.9 | 27.4 | 23.5 |
| 5 iridescence | 13.1 | 7.2 | 6.4 |
| 6 emission | 0.5 | 0.6 | 1.4 |
| 7 clear glass (+dispersion) | 122.5 | 41.9 | 42.9 |
| 8 textured | 2.7 | 3.2 | 3.5 |
| whole frame | 15.4 | 16.7 | 15.7 |

Reading: the two web engines are within 1-3 points of each other everywhere and both beat EEVEE on glass; the biggest gap to Cycles is metal anisotropy (reflection structure), glass interiors (no multi-bounce/refraction of the scene, only screen-space-ish transmission of opaque objects) and missing shadows. The numbers are my own metric (no `preview diff` used: the pixel-circle MAE was needed per sphere), so treat them as relative.

## Exporter settings / things that mattered
1. **`glTF Material Output` node group is mandatory for volume, thickness, dispersion and iridescence.** Without it: no `KHR_materials_volume`, no dispersion, no iridescence (first export contained none of them, despite Volume Absorption and Thin Film being wired). Required group name starts with "glTF Material Output" and inputs named exactly `Thickness`, `Dispersion`, `Iridescence Factor`, `Iridescence Thickness Minimum`, `Occlusion`. Volume export requires Thickness != 0; dispersion needs volume; attenuationDistance = 1/Volume Absorption Density; attenuationColor from the absorption colour. [V] exporter source `blender/exp/material/extensions/{volume,dispersion,iridescence}.py` in Blender 5.2.2.
2. `export_import_convert_lighting_mode=COMPAT` for any web scene with an IBL. SPEC (default) is unusable without re-exposing.
3. `export_lights=False` and `export_cameras=False` are the defaults: set True or you get neither.
4. `export_gn_mesh=True` + `export_gpu_instances=True` for Geometry Nodes instances; default drops GN-only objects.
5. `export_anim_slide_to_zero=False` default leaves key times at frame/fps (animation starts at 0.0417 s; duration 2.0417 s for a 48-frame range). Harmless but explains "off by one frame" mismatches.
6. Every material came out `doubleSided: true` (Blender "Backface Culling" off by default). Costs fill rate; tick backface culling in Blender per material.
7. Texture wiring: "More than one shader node tex image used for a texture" warning when the same texture node feeds several inputs through a separate-colour node; export still works (roughness from G, metallic from B packed to metallicRoughness).
8. Not tested: Subsurface, Diffuse Roughness, Thin Wall, Coat Tint/Normal, Specular Tint (no test sphere used them).

## Gotchas
- Babylon `HDRCubeTexture` + `createDefaultSkybox` clones the texture for the skybox: set `rotationY` on `skybox.material.reflectionTexture` too; the default needs +PI/2 relative to three for the same Blender equirect. Low cube `size` (512) visibly pixelates the background at a narrow FOV; used 1024.
- Babylon animation group frame range is in 60 fps frames (2.5-122.5), not seconds; `goToFrame(t*60)`.
- First CDN fetch of Babylon from jsDelivr stalled (~35 KB/s, page load timeout) while unpkg gave 8.6 MB in 1.7 s; the page used `unpkg.com/babylonjs@9.31.0`. Pin versions and consider self-hosting for production.
- three r186 deprecates `RGBELoader` (use `HDRLoader`) and `THREE.Clock` (use `THREE.Timer`): warnings only.
- `KHR_lights_punctual` is written as **required**; a loader without it will refuse the file (strip or `gltf-transform` it if targeting minimal viewers).
- EEVEE (Blender 5.2) renders transmission as an opaque mirror unless Raytracing is on (`scene.eevee.use_raytracing=True`); even then it was far from Cycles. Use Cycles for the realism reference, not EEVEE.
- Cycles/EEVEE "Khronos PBR Neutral" in Blender matched three/Babylon Neutral to within 3% on floor luminance: a consistent tone map is achievable.
- Not covered: KTX2/Draco/meshopt paths, WebGPU renderers (three WebGPURenderer, Babylon WebGPUEngine), `KHR_animation_pointer`, skins/morphs, multi-UV, large scenes' load time.
