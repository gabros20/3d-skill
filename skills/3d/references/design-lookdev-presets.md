# Lookdev Presets and Colour Policy

Purpose: Pick a look (named preset), set the one colour and tone policy, and apply the same lighting and material intent in Blender and three.

Read when:
- Choosing a look at intake ("pick A, B or C"), or lighting a scene from nothing.
- Brand colour renders wrong, the scene is washed or grey, or Blender and three disagree.

Skip when:
- Three API calls for lights, PMREM, shadows → [threejs-lookdev](threejs-lookdev.md).
- Blender API for lamps, view transform, bake → [blender-lookdev-render](blender-lookdev-render.md).
- Shot and composition choices → [design-art-direction](design-art-direction.md).

Inputs:
- Brand colours (hex), subject material, mood words or a reference analysis, target device tier.

Produces:
- One preset plus overrides, one view transform, both recorded in `3D.md`.

## Contents

- Colour and tone policy · Lighting recipes · Material recipes · Matching Blender · Presets A-E · Intake use · Traps

## Colour and tone policy (canonical)

1. **One view transform per project**, same intent in Blender and three, recorded in `3D.md`.
   - **Khronos PBR Neutral** when brand or product colour must read as authored (marketing hero, product, configurator).
   - **AgX** for cinematic worlds where highlight roll-off beats hue fidelity.
   - Not ACES by accident: R3F turns it on by default (`flat` or an explicit `gl.toneMapping` overrides); raw three defaults to none.
2. three: `renderer.toneMapping = NeutralToneMapping | AgXToneMapping`, `outputColorSpace = SRGBColorSpace`, exposure via `toneMappingExposure`. Blender: `scene.view_settings.view_transform` (read the enum for the exact names). Brightness through exposure, never by scaling lamps.
3. Colour textures sRGB, data textures (normal, roughness, metalness, AO) `NoColorSpace`; never one file as both. Author brand hex in sRGB.
4. Tone map once, at the end. With an `EffectComposer` the tone mapping happens in `OutputPass`; effects before it are linear HDR, display-referred ones (vignette, grain) go after ([threejs-postfx](threejs-postfx.md)).
5. `scene.environmentIntensity`, not `envMapIntensity`, for `scene.environment`. PMREM and PBR changed in r181, r185 and r186: re-tune after a three upgrade; never promise "same HDRI, same look".
6. Prove it: render the same shot on both sides, compare in `preview diff` ([shared-verification](shared-verification.md)); read the EXR, AgX hides clipping.

## Lighting recipes (renderer-neutral; stops relative to key)

- **One sun**: key direction = sky disc = warm side of the environment = shadow terminator. A light is added only for a visible relationship (key, fill, rim, practical).
- **Contrast comes from ratio, not exposure.** Start about key 4 against `environmentIntensity` 0.4-0.5 in three; env near 0.85 reads grey and CG. Starting values, scene-specific [P]: tune by capture, translate to Blender by ratios, never absolute numbers.
- Shadows: 1-2 casters on mobile, 2-4 desktop; fog separates depth planes.
- Bloom only on real lights: threshold just above the brightest lit surface (about 1.1-1.2 linear), strength 0.25-0.35, radius about 0.2. Emissive about 3; above about 7 AgX washes to white. Wide radius reads as haze.
- HDRI: 512x256 is enough for diffuse light once PMREM blurs it; visible reflections (chrome, glass, strips) want 1-2k [P].

## Material recipes

- **Brushed metal**: metalness 1, roughness 0.25-0.45, `anisotropy` with `anisotropyRotation` (needs UV or tangent direction), base colour a measured reflectance, strip-light environment. Metals with no environment render black.
- **Glass / transmission**: `transmission` 1, `ior` 1.45-1.5, `thickness` > 0, roughness 0-0.1, `attenuationColor`/`attenuationDistance` for tint. Needs something to refract (gradient, panels). Transmission costs a pass and many transmissive materials compile slowly: keep to a few.
- **Paper / clay**: roughness 0.8-1, `sheen` for fuzz, generous bevel, strong AO and contact shadow, soft shadows. Never tile a small texture on a close-up.
- **Dark premium**: black glass + dark metal, roughness 0.2-0.4, light shaped by strips and rims, not fill.
- Detail by scale: geometry for silhouette, normal/roughness for surface. Texel budget: required px = projected CSS px x DPR x 1.0-1.5. `normalScale` 0.25-0.8. Wear is causal.

## Matching Blender

three's AgX is not Blender's: r186's shader has the AgX look step commented out (no Looks) and no Punchy variant exists in the source (verified in the 0.186.1 source; three PR #27618 was closed unmerged). Blender's grade will read flatter-or-punchier than the browser.
- Pick by need: **Neutral** on both sides when brand hex must match (the safest cross-renderer match); AgX only for cinematic, then accept a small drift.
- Match exposure first (EV in Blender = 2^EV on `toneMappingExposure`), then contrast/saturation with a grade in the post chain: a CDL (slope/offset/power, saturation) or 3D LUT after `OutputPass`, fitted to a render-vs-capture pair; never by changing lamps.
- Bake and render with the same view transform. Colour maps sRGB, data maps `NoColorSpace`, glTF UVs `flipY = false`; one lighting setup in both (Blender's default world is not neutral).
- An export that looks flat: no environment in three (Blender's world is gone), baked lighting multiplied onto metalness (lightmap plus metal double-lights), or a missing sun. Fix the environment first.

## Presets

| | A Studio Product | B Night Silicon | C Glass Atrium | D Paper Craft | E Golden Daylight |
|---|---|---|---|---|---|
| Mood | clean, trustworthy | dark, precise, premium | airy, refined | soft, tactile, friendly | warm, cinematic |
| Key / fill / rim | large softbox 45 deg high, fill -2 EV, rim +0.5 EV narrow | low cool side key, no fill, strong accent rims | soft overhead key, window gradient behind | huge overcast key, fill -1 EV | sun key, cool sky fill -2.5 EV, warm rim |
| HDRI | studio softboxes | dark studio with strip lights | high-key gradient or panels | overcast sky | clear sky with sun |
| Env intensity | 0.5-0.8 | 0.15-0.3 | 0.8-1.0 | 0.8-1.0 | 0.4-0.5 |
| Exposure (EV, Blender) | 0 | -0.5 | +0.3 | +0.3 | 0 |
| Tone mapping | Neutral | AgX (Neutral if an accent hex must match) | Neutral | Neutral | AgX |
| Palette logic | neutral ground, brand only on the product | near-black ground, one accent on edges | pale ground, glass tint from brand | 3 pastels by role, low contrast | warm key, cool shadow |
| Finish | satin plastic, anodised, roughness 0.25-0.5 | black glass, dark metal | transmission, polished | matte, sheen | mixed, weathered |
| Post | none; contact shadow | bloom, light grain after OutputPass | none | light grain | vignette, light radial CA, grain after OutputPass |
| Chapters | 1-3 | 4-8 | 2-5 | 3-6 | 4-8 |

## `.3d/look.json` values

At build time write `.3d/look.json` (`schema: "look.v1"`) from the chosen preset; the viewer reads it. `exposure` is three's `toneMappingExposure` multiplier (2^EV), not stops.

| | A | B | C | D | E |
|---|---|---|---|---|---|
| `toneMapping` | `neutral` | `agx` | `neutral` | `neutral` | `agx` |
| `exposure` | 1.0 | 0.7 | 1.2 | 1.2 | 1.0 |
| `environment` | `room` | dark strip-light HDRI (path or URL) | high-key gradient HDRI | overcast HDRI | clear-sky HDRI with sun |
| `background` | `#f2f2f0` | `#0a0b0d` | `#eef1f4` | `#efe9df` | `#bcc9d8` |

Backgrounds are starting hexes: replace with the brand palette. Env intensity stays in the scene, not in `look.json`.

## Intake use

Offer A to E as "pick one, then override" with a one-line mood each; map a reference analysis to the nearest preset, then override palette and exposure only. Record `preset`, `tone`, overrides in `3D.md` and write `.3d/look.json`.

## Traps

- Fixing flatness with exposure instead of key-to-env ratio.
- Bloom radius up to hide weak materials.
- Tone mapping twice (renderer and `OutputPass`), or effects after tone mapping that expect HDR.
