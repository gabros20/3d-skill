# Blender Shading

Purpose: Build Blender materials that read as real, survive glTF, and are judged fairly.

Read when:
- Authoring or fixing a node material, procedural look, glass, skin, hair or toon shader; "flat in three.js", "washed-out normals".

Skip when:
- Sourcing or generating image textures (→ [blender-texturing](blender-texturing.md)); unwrapping or baking maps (→ [blender-uv-bake](blender-uv-bake.md)); runtime materials (→ [threejs-lookdev](threejs-lookdev.md)).

Inputs:
- Material brief, target (render only, or web), `bpy.app.version_string`.

Produces:
- A Principled-based material, with every non-exportable node flagged for baking.

Read with [blender-scripting](blender-scripting.md) and [blender-version-traps](blender-version-traps.md).

## Contents

- What survives glTF · Colour spaces · PBR values · Coordinates · Recipes · Special materials · Judging · Traps

## What survives glTF

1. Only Image Texture / RGB / UV feeding Principled BSDF exports. Procedurals, Color Ramp, Mix factors, bump-from-noise, Sheen BSDF and Hair BSDF do not: bake them ([blender-uv-bake](blender-uv-bake.md)). Rules and the `glTF Material Output` group (volume, dispersion, iridescence): [blender-export](blender-export.md).
2. Principled v2 names (5.2.2): `Subsurface Weight`, `Specular IOR Level`, `Transmission Weight`, `Coat Weight`, `Sheen Weight`, `Emission Color` + `Emission Strength` (default 0), `Thin Film Thickness`. There is no Dispersion input. Find nodes by `type == 'BSDF_PRINCIPLED'`, not by localised name.
3. `mat.node_tree` exists without `use_nodes`; setting `use_nodes` only warns (removed in 6.0), so do not rely on it.
4. glTF packing: R occlusion, G roughness, B metallic. OpenGL normals. Never JPEG normals.
5. Glass: Transmission Weight exports `KHR_materials_transmission` + `ior`; Alpha < 1 exports `alphaMode BLEND`. `surface_render_method` changes only Blender's render.

## Colour spaces

Canonical rule: colour data (Base Color, Emission) is `sRGB`; every data map (roughness, metallic, normal, AO, height, opacity) is `Non-Color`. Set it before writing pixels or baking: `bpy.data.images.new` gives sRGB (a `float_buffer=True` image gives `Linear Rec.709`). Wrong space is the most common texture bug (washed normals, dark roughness).

## PBR values

Practitioner ranges, not measured here:
- Dielectric albedo sRGB ~30–240; metal ~180–255. Metallic is 0 or 1 except at transition pixels (gradients give dirty halos).
- Vary roughness ±0.1–0.2 with grunge; micro detail goes in roughness, not bump. IOR 1.5 for dielectrics.
- Normal map or displacement, never both. Fabric: Bump Distance ~0.001, Strength 0.1–0.2. Displacement Scale ~0.2, Midlevel 0.5, 16-bit source.

## Coordinates

| Need | Use |
|---|---|
| Will be baked or exported | `UV` |
| Non-deforming prop, no UVs | `Object`; image `projection='BOX'`, `projection_blend` ~0.2 |
| Bounding-box 0–1 | `Generated` |
| Screen-space or projection tricks | `Camera`, `Window` |

## Recipes

Build effects as grey masks driving Mix or HSV factors, not painted colour; pull Color Ramp stops for contrast. Broad soft masks: vertex colour; fine detail: image.

| Feature | Nodes |
|---|---|
| Base variation | Noise (Scale 3–8, Detail 8–12, Roughness 0.6) → Color Ramp → Mix; a second Noise ~25× smaller for grain |
| Cells, stone, cracks | Voronoi `F1` / `SMOOTH_F1` for cells, `DISTANCE_TO_EDGE` for cracks → Color Ramp → Bump |
| Wood, marble | Wave (Bands/Rings, Distortion 2–6) with Noise added to its Vector |
| Edge wear | Bevel node (Radius 0.02–0.05) vs the true normal → Color Ramp |
| Dirt | AO node (Distance 0.2–0.5) × large Noise → Mix; invert AO to fill crevices |
| Anti-tiling | Two Image Textures at different scale and rotation, mixed by a low-frequency Noise |

- Musgrave is gone: use Noise `noise_type` (`FBM`, `RIDGED_MULTIFRACTAL`, …). Gabor exists.
- Bevel, AO and Pointiness (Geometry node output) are Cycles-only and stochastic: bake before thresholding.
- Package edge wear and dirt as one node group with a strength input per material.

## Special materials

- **Skin**: roughness ~0.7 (lips ~0.4), pores Voronoi `SMOOTH_F1` at scale 100/200, Subsurface Scale 0.005–0.04 m in 5.2 (older 0.02–0.15 tutorials look waxy), more SSS on ears, nose, lids, lips. Community numbers, untested.
- **Hair**: Principled Hair BSDF; EEVEE needs explicit colours. Web hair is cards or baked ([blender-geometry-nodes](blender-geometry-nodes.md)).
- **Glass**: Transmission Weight 1, IOR ~1.5; Cycles for truth ([blender-lookdev-render](blender-lookdev-render.md)).
- **Toon / NPR**: Shader to RGB → constant Color Ramp gives cel bands, but is EEVEE-only: in Cycles 5.2.2 the node returned white (measured) and it never exports. For the web use banded textures or a runtime toon material.
- **Outline that survives glTF**: Solidify (`offset=1`, `use_flip_normals=True`, `material_offset=1`) with a black second material that has `use_backface_culling=True`, then apply it. Measured: the GLB keeps both primitives and the outline material is single-sided; the three.js render is untested. Line Art and Freestyle are render-only ([blender-animation](blender-animation.md)).

## Judging

Judge in `Standard` view on a mid-grey background; set Base Color black to read roughness; add a hard backlight and a light from below. Look at a render, not node previews ([blender-scripting](blender-scripting.md) Verify).

## Traps

- `ShaderNodeColorRamp` does not exist: Color Ramp is `ShaderNodeValToRGB`.
- `ShaderNodeMix` has one input per data type with duplicate names (`Factor`, `A`, `B`): look sockets up by identifier (`A_Color`, `B_Color`, `Factor_Float`); `inputs["Factor_Float"]` raises `KeyError`. Set `data_type='RGBA'` before linking colours.
- A node graph that looks right in Blender can export nothing: check `extensionsUsed` and the image count after export.
