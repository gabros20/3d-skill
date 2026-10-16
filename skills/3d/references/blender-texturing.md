# Blender Texturing

Purpose: Get a correct, tiling, PBR image-texture set onto a Blender material: fetch or generate, gate, derive maps, look at it, hand off to bake and export.

Read when:
- A material needs image textures (stone, wood, fabric, painted metal) that are not yet on disk.
- A texture shows seams, a repeating lattice, baked-in light, inverted bumps or a wrong scale.
- The brief says "texture this mesh from a prompt" or asks for AI-generated textures.

Skip when:
- Building a node graph from values or procedurals (→ [blender-shading](blender-shading.md)).
- Unwrapping, texel density rules, baking procedurals or hi-to-lo (→ [blender-uv-bake](blender-uv-bake.md)).
- Colour-space rules, glTF-surviving nodes: [blender-shading](blender-shading.md). Export: [blender-export](blender-export.md).

Inputs:
- Material, physical size of one tile in metres, hero or background, commercial yes/no, client territory.

Produces:
- A map set (albedo sRGB, others Non-Color), a material, a looked-at render, a licence line in the `3D.md` ledger.

## Contents

- Gates G0 to G6 · Prompt · Seams · De-light · Derive · Material · Procedural recipes · Whole-mesh lanes · Licences · Traps

## Gates

Do not skip a gate; a failed gate stops the chain.

- **G0 brief.** Fix tile size (m), role, commercial flag. The flag decides the tools allowed in Licences.
- **G1 source.** Poly Haven or ambientCG first (CC0, tiled, de-lit, known scale, full PBR set; fetch 1-2K via their download links, never scrape). Only if no set matches, generate (Prompt). Record URL and licence per asset ([asset-acquire](asset-acquire.md) holds the line format).
- **G2 tile.** `assets/blender/texture_prep.py --seam IMG` must give ratio <= 1.3. Fail: `--tile` or the offset repair (Seams), re-measure, then render 3x3.
- **G3 de-light.** `--report IMG` shows the low-frequency luminance spread (std/mean); above 0.12 run `--delight IMG --out OUT` (it exits 1 if still above `--max-lowfreq`), else regenerate.
- **G4 derive.** Missing maps, in the order below.
- **G5 material.** `assets/blender/material_from_maps.py`, then look at the `--preview` render.
- **G6 deliver.** `assets/blender/uv_check.py --res` for texel density; `assets/blender/bake_maps.py` if the result is procedural or layered; then `assets/blender/export_web.py`, `scripts/glb-report`, and a re-import check (images present, normal image Non-Color).

Scripts run under `blender -b … --python-exit-code 1 --python assets/blender/<script> -- <args>`; contract in [blender-scripting](blender-scripting.md). `texture_prep.py` uses numpy as shipped with Blender, so it reads 16-bit and EXR.

## Prompt (generation)

Recommend the `generate-image` skill; never invoke it yourself. The user runs it or approves the call; a paid or quota-spending call needs approval per job. Prose, not JSON. Shape:

`Top-down orthographic photograph of <material, colour, wear>, flat even diffuse light, no shadows, no highlights, no perspective, no vignette, no borders, no text, uniform detail across the frame, seamless tileable texture, <scale cue, e.g. "pebbles about 3 cm">, square 1:1, 2048x2048`

Flat and shadowless is the biggest quality lever. "Seamless" is a request, not a guarantee: always run G2. Regular structure (planks, bricks, logos) reads better procedural than generated.

## Seams

Seam ratio = mean abs difference between opposite edges / mean abs neighbour-pixel difference; about 1 means the edge looks like an interior line. Measured earlier: a non-tiling field scored 14.9, 1.12 after the fix below.

1. Organic materials: cross-fade with the half-offset copy, `out = a*W + roll(a,(h/2,w/2))*(1-W)`, W a separable sin^2 window (0 at edges, 1 at centre). Ghosts large features; the 3x3 render shows it.
2. Anything with structure: roll the image half a tile on both axes, so the seam sits in the middle as a cross; inpaint that cross (an image-edit call with a mask); roll back; re-measure.
3. Lattice without a seam: a distinctive blemish repeats. Mix two copies at different Mapping scale and rotation through a low-frequency Noise mask, or use BOX projection with blend 0.2 on large surfaces.

## De-light

Baked shadows or a lamp-shaped gradient rotate wrongly under scene light. Reject the image, or subtract a heavy blur (radius about 1/4 of the image) and add back the mean. Meshy `remove_lighting` does the same on whole meshes.

## Derive maps

Order: library map > luminance-height > normal > roughness > metallic > AO.

1. Height: library map, else luminance (fine for stone, bark; fails on printed patterns). Keep 16-bit or float; 8-bit terraces the normal.
2. Normal OpenGL (+Y), wrap-safe with `np.roll`, strength is the knob. Unreal/Substance DirectX maps (`nor_dx`) need the green channel flipped.
3. Roughness: inverted, contrast-stretched luminance in 0.4-0.9.
4. Metallic: 0, or a binary mask for bare metal. Never a gradient on non-metals (dirty halos).
5. AO: only by bake on real geometry ([blender-uv-bake](blender-uv-bake.md)). Upscale low-res sources before deriving.

`texture_prep.py --derive IMG --out-dir DIR [--height luma|FILE] [--strength 2]` does 1-3.

## Material

`material_from_maps.py --dir MAPS [--tile-m 1.0] [--box 0.2] [--normal gl|dx|auto] [--preview out.png --engine cycles --samples 32]` sets colour spaces, the ORM split, the DX flip and Mapping scale (1 / tile metres). Then open the preview (a 3 m plane plus a sphere) and check: no lattice, scale matches a real reference, bumps not inverted. A passing script is not a passing look.

## Procedural recipes

Names verified on 5.2.2; all are Cycles-side and must be baked for glTF.

- **Edge wear:** `ShaderNodeBevel` (Radius 0.02-0.05) Normal output -> `ShaderNodeVectorMath` `DOT_PRODUCT` with `ShaderNodeNewGeometry` "True Normal" -> `ShaderNodeValToRGB` with stops near 0.9 and 0.999 (flat faces give 1, bevelled edges less; swap stops for an edge mask). Rendered check: mask mean 0.48 on a bevelled cube. EEVEE has no Bevel node.
- **Grime:** `ShaderNodeAmbientOcclusion` (Distance 0.2-0.5, output AO) times a large-scale `ShaderNodeTexNoise` -> ramp -> `ShaderNodeMix` (data_type `RGBA`) between base and dark brown. Invert AO to gather in crevices.
- **Triplanar:** Image Texture `projection='BOX'`, `projection_blend=0.2`, fed by Texture Coordinate "Object"; no UVs needed.
- **Anti-tiling:** two Image Texture nodes at different Mapping scale/rotation mixed by a Noise mask.
- Musgrave is gone (Noise has `noise_type`); Mix is `ShaderNodeMix`, not MixRGB.

## Whole-mesh lanes

- **Meshy Retexture** (`POST /openapi/v1/retexture`): the one scriptable lane; PAID, no script shipped. Use `enable_original_uv=true`, `enable_pbr=true`, `remove_lighting=true`, `texture_resolution` 2k. Needs approval per job; never resubmit on timeout ([asset-acquire](asset-acquire.md)). Pull `texture_urls`, then G4-G6.
- **Tripo texture task:** works best on Tripo's own task ids; paid, same approval rule.
- **StableGen:** Blender 4.2-4.5 or 5.1+ ("5.0 not supported"), ComfyUI, NVIDIA GPU. UI-only; human lane.
- **Projection from a generated image:** render the clay mesh from the intended camera, restyle with the image model, project via Texture Coordinate "Camera" into an Image Texture, bake DIFFUSE to the UV image. Projection paints through geometry, so keep to near-planar views or several cameras.
- **Painting:** `img.pixels.foreach_set(np_array.ravel())` works headless; brush strokes need a viewport.
- **Trim sheets, decals** [untested]: one 2K sheet of horizontal strips with UV islands moved onto rows; decals as planes 0.1-0.5 mm off the surface with `alphaMode MASK`, or bake into albedo for web.

## Licences

| Source | Client work | Gate |
|---|---|---|
| Poly Haven, ambientCG | yes, CC0 | no scraping; API terms separate |
| `generate-image` outputs | per provider terms | user approves; log provider in the ledger |
| Meshy, Tripo | per vendor and plan; PAID | approval per job |
| StableGen, Dream Textures, DeepBump, Materialize | GPL code; your images are yours | human lane; check model licences |
| FLUX.1-dev | own licence | ask before client work |
| TRELLIS.2 Native texture (nvdiffrast) | no, NVIDIA non-commercial | refuse |
| Ubisoft CHORD | no, research-only | refuse |
| Hunyuan3D Paint | not EU, UK, South Korea; >1M MAU | ask territory; default refuse for EU |
| Material Maker | MIT; outputs yours | free; propose install |

## Traps

- `images.new` defaults sRGB: apply the colour-space rule in [blender-shading](blender-shading.md) before writing pixels.
- `Material.use_nodes` warns "removed in 6.0" on 5.2.2; guard it.
- DeepBump has onnxruntime crashes reported on Blender 5.x; use the numpy derivation.
- Heuristic metallic and 8-bit height cause halos and terracing.
