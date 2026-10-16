# Realism Toolbox: Ranked Techniques

Purpose: Rank the techniques that close real-time gaps in three r186, with backend, cost, expected gain and where the recipe lives.

Read when:
- A FIXABLE defect names a technique, or the gate lists planned ones.
- Building the direction menu, or "make three.js look like the Blender render".

Skip when:
- Only one API detail is needed → the recipe home in the row.
- Deciding whether a gap is a ceiling → [realism-gap](realism-gap.md).

Inputs:
- Defect or gap ids (G#), backend, device tier, [shared-performance](shared-performance.md) budget.

Produces:
- Ordered technique list with ids for `preview new-version --technique`.

## Contents

- Ranked table · Stack by budget · Matching a Blender look · Path-trace recipe · Direction menu map · Traps

## Ranked table

Rule: T1-T4 before any screen-space effect. Costs marked [U] are unmeasured: measure on target. Node and class names are checked against the r186 tree unless tagged.

| id | technique | closes | WebGL | WebGPU | cost | gain | recipe home |
|---|---|---|---|---|---|---|---|
| T1 | contrasty studio env: strip/softbox emitters via `PMREMGenerator.fromScene`, or drei `Environment` + `Lightformer` | G3 G4 (G2 part) | yes | yes | ~0 | +1 on metal | [threejs-lookdev](threejs-lookdev.md) |
| T2 | tone + exposure settled on reference luma; AgX / Neutral / LUT (no AgX punchy variant exists in r186 or pmndrs 6.39: add contrast in the grade or a LUT) | G12 | yes | yes | 0 | high | [design-lookdev-presets](design-lookdev-presets.md), [threejs-renderer](threejs-renderer.md) |
| T3 | material detail: roughness/normal maps, anisotropy, clearcoat, per-instance variation | G18-G20 | yes | yes | texture MB | high | [design-lookdev-presets](design-lookdev-presets.md), [threejs-lookdev](threejs-lookdev.md) |
| T4 | baked lighting from Cycles (lightmap/AO on uv1; metal gets a probe, not a lightmap) | G1 G5-G7 | yes | yes | 0 runtime, ~1 h, static | high | [blender-lookdev-render](blender-lookdev-render.md), [threejs-lookdev](threejs-lookdev.md) |
| T5 | reflection probe: `CubeCamera` once per object/group, or every N frames, into `envMap` | G2 | yes | yes | 1-3 ms/update [U] | med-high on metal | [threejs-lookdev](threejs-lookdev.md) |
| T6 | shadows: contact / accumulative (static) / PCSS / VSM | G5 | yes | yes (VSM) | low-med | high | [threejs-lookdev](threejs-lookdev.md) |
| T7 | AO: N8AO (WebGL), `GTAOPass`; WebGPU `ao()` (GTAONode) | G6 | yes | yes | 0.5-2 ms [U] | high | [threejs-postfx](threejs-postfx.md) |
| T8 | `RectAreaLight` strips (LTC; no shadows; Standard/Physical only) | G4 G7 | yes, needs `RectAreaLightUniformsLib.init()` | yes, `RectAreaLightNode.setLTC(RectAreaLightTexturesLib.init())` | med | med-high | [threejs-lookdev](threejs-lookdev.md) |
| T9 | selective / emissive-only bloom | G13 | yes | yes (MRT) | 0.5-1.5 ms [U] | med | [threejs-postfx](threejs-postfx.md) |
| T10 | finish: LUT, vignette, grain, dither, mild CA | G17 R5 | yes | yes | ~0.3 ms [U] | med | [threejs-postfx](threejs-postfx.md) |
| T11 | AA: MSAA / SMAA / TRAA (TRAA excludes MSAA) | G16 | yes | yes | low | med | [threejs-postfx](threejs-postfx.md) |
| T12 | depth of field | G14 | yes | yes | 1-3 ms [U] | med | [threejs-postfx](threejs-postfx.md) |
| T13 | SSR / planar reflector (`SSRPass`, `MeshReflectorMaterial`; WebGPU `ssr()`) | G2 on-screen, floors | yes | yes | 2-4 ms [U] | med, artefacts | [threejs-postfx](threejs-postfx.md) |
| T14 | screen-space / voxel GI, probe grid (`ssgi()`; `vxgi()` from `three/addons/lighting/vxgi/VXGINode.js`; `LightProbeGrid`) | G1 dynamic | none first-party | yes, desktop | 3-8 ms [U] | med, noisy | [threejs-postfx](threejs-postfx.md) |
| T15 | motion blur / sub-frame accumulation | G15 | custom | `motionBlur()` function (tsl/display) | 1-2 ms [U] | med | [threejs-postfx](threejs-postfx.md) |
| T16 | transmission, `MeshTransmissionMaterial`, dispersion | G8 | yes | yes | one scene pass per object | material-specific | [threejs-lookdev](threejs-lookdev.md) |
| T17 | custom GLSL/TSL fakes: rim, gap gradients, projected caustics, godray cones, wrap-SSS | G9-G11 | yes | yes | dev time | varies | [shader-glsl](shader-glsl.md), [shader-tsl](shader-tsl.md) |
| T18 | in-browser path tracing (`WebGPUPathTracer`) | G1-G11, stills | deprecated tracer only | yes | seconds-minutes/frame | ceiling-grade stills | this file |

## Stack by budget

Post passes (full-screen) are T7, T9, T11 when SMAA/TRAA, T12, T13 (`SSRPass`, `ssr()`), T14, T15. T10 costs no pass when LUT, grain and dither are folded into the final tone-map/grade pass. MSAA, planar reflectors, T6 and T8 are not post passes (planar and shadows cost extra scene renders). Every stack below must fit the post-pass count in [shared-performance](shared-performance.md); pick within it, do not add.

- Mobile (0-1 passes): T1 (128-256 px env), T2, T3 (KTX2), T4, T6 contact, MSAA instead of an AA pass, T10 as static grain in the final pass. Spend the one pass on T9 half-res, only if the brief has glow. Skip T7, T12-T16. DPR 1.5-2 max.
- Laptop (2 passes): same non-pass base plus T3 lobes, T6 accumulative, T8 x1-2, planar T13. Pick two of: T7 half-res, T9, T11 SMAA. T10 folded into the final pass.
- Desktop WebGPU (2 passes): pick two of T7, T9, T11 TRAA, T13 `ssr`, T14, T12, T15 by the defect list. T16 as material cost. Anything beyond two is a documented overrun in `3D.md`, not a default.
- Offline-in-browser: T18 with a denoiser, for stills; clips only as a brief change (B3).

Numeric budgets stay in [shared-performance](shared-performance.md).

## Matching a Blender look

1. Same view transform both sides ([design-lookdev-presets](design-lookdev-presets.md)). Three's AgX is not Blender's AgX (no Looks, gamut clamp) [P].
2. Bake static diffuse and AO in Cycles ([blender-lookdev-render](blender-lookdev-render.md)).
3. Wire maps without double lighting ([threejs-lookdev](threejs-lookdev.md)).
4. Metal stays live: T1 and/or T5. A lightmap on metalness 1 has no visible effect.
5. Add the missing grade (T2/T10).
6. Tune with sliders against a paired capture, never by guessing.

## T18 path-trace recipe

1. `import { WebGPUPathTracer } from 'three-gpu-pathtracer/webgpu'` (v0.0.25+, three r185+); `setScene(scene, camera)`; `renderSample()` once per frame. `maxSamples` is a property (0 = render forever); the denoiser runs only once it is reached, and `OIDNDenoiser` needs `oidn-web` plus a weights URL injected by you.
2. Limits: WebGPU only; Standard/Physical materials only; environment must be a `Color`, `CubeTexture` or equirect texture, never a PMREM; Spot/Directional/Point lights need MIS on (leave `multipleImportanceSampling` enabled); emissives are traced but not MIS-sampled, so use area lights for clean light; do not use `@react-three/gpu-pathtracer` (wraps the deprecated WebGL tracer); any scene change resets accumulation; BVH rebuilds on geometry change.
3. Uses: the twin capture (see [realism-gate](realism-gate.md)), poster/hero stills, refine-when-idle only: with a static camera, swap in the accumulated image when the page is idle and drop it on the first input.
4. NEVER ship path-traced clips as live rendering: that replaces the deliverable and is a brief change (B3), not a technique.

## Direction menu map

User words to ids: lighting rig (T1, T8) · texture / roughness detail (T3) · colour / grade (T2, T10) · shadow technique (T6, T4) · highlights / specular (T1, T5, T3 per-instance variation) · selective bloom (T9) · grain / noise / dither (T10) · custom GLSL/TSL look (T17) · baked lighting (T4) · path-traced stills / idle refine (T18) · WebGPU realism passes (T14, T13).

Brief changes, never menu items: B1 pre-rendered video or scrub frames · B2 plate + live light/projection · B3 path-traced clip as video. A tileable detail map derived from a reference crop is allowed for T3; the reference image as a plate is not.

## Traps

- Bloom or fog to hide a material gap (auto-fail).
- Stacking screen-space passes before T1-T4.
- A lightmap on metalness 1.
- WebGPU-only rows promised on a WebGL or mobile target.
