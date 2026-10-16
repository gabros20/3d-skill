# three.js Post-Processing

Purpose: Choose and implement post effects (bloom, grade/LUT, DOF) on the correct pipeline without paying for what the brief does not need.

Read when:
- Adding bloom, vignette, grain, LUT, depth of field, SSAO; or post makes the scene slow or double-tone-mapped.

Skip when:
- Look is not yet readable without post → [threejs-lookdev](threejs-lookdev.md) first.
- Custom full-screen shader as the only effect → [shader-glsl](shader-glsl.md) / [shader-tsl](shader-tsl.md).

Inputs:
- Renderer backend, effect list from the brief, per-tier pass budget ([shared-performance](shared-performance.md)).

Produces:
- One pipeline with a single final-render owner and a no-post baseline toggle.

## Pipeline choice

| Backend | Use | Notes |
|---|---|---|
| WebGL + R3F | `@react-three/postprocessing` 3.x (wraps pmndrs `postprocessing` 6.x) | merges effects into one pass; WebGL only |
| WebGL vanilla | pmndrs `EffectComposer` + `RenderPass` + `EffectPass`, or three addons `EffectComposer` + `OutputPass` | |
| WebGPU | `RenderPipeline` (r183 name) with TSL nodes: `bloom`, `fxaa`, `ssao` / `ao` (GTAONode), `traa`, `dof`, `ssr` | API churns every release; pin three |

Never mix the pmndrs composer with `WebGPURenderer`.

## Order and ownership

1. One owner renders the final frame. A composer takes priority over auto-render; extra `gl.render` calls duplicate or overwrite it.
2. Signal order: scene HDR (+ depth/normal) → AO → atmosphere → bloom (HDR) → exposure → tone map once → grade/LUT → lens effects → output.
3. Use `HalfFloatType` buffers for HDR bloom. Tone mapping happens inside the chain (`ToneMapping` effect or `OutputPass`); set renderer `toneMapping` to `NoToneMapping` when the chain does it, or it applies twice.
4. Call `composer.setSize` with `renderer.setSize`; `multisampling` 0–4 only if needed.

## Bloom

0. Bloom only on deliberately emissive sources: selective/MRT, or a threshold above the brightest non-emissive surface. Bloom on metal edges reads as self-lit halos.
1. Start with HDR threshold: `luminanceThreshold` near 1, make glow sources emissive above 1 (`emissiveIntensity` > 1). If nothing glows the threshold is working; raise emission, not bloom intensity.
2. When bright non-emissive surfaces (specular, white UI) bleed: switch to MRT emissive channel read by bloom (WebGPU `mrt`), or selective layers. Dual-pass material-swap selective bloom costs several full renders; restore materials in `finally`.
3. Bloom resolution scale ≤ 0.5 on mobile.

## Realism passes

Ranking: [realism-toolbox](realism-toolbox.md). Measure every pass at DPR 2.

| T | Pass | WebGL | WebGPU r186 node |
|---|---|---|---|
| T7 | AO | `<N8AO>` (n8ao 2.0): `quality` is `'performance' \| 'low' \| 'medium' \| 'high' \| 'ultra'`; neural modes only via ref `setQualityMode("Neural-Medium")`. Skip when AO is baked | `ao()` (GTAONode); `ssao` also exists |
| T9 | selective bloom | pmndrs `SelectiveBloomEffect` / wrapper `Selection` + `Select`; keep `luminanceThreshold` high | `bloom` with an MRT emissive output |
| T11 | AA | SMAA or MSAA | `traa` (needs depth + velocity from the scene pass MRT; excludes MSAA) |
| T13 | reflections | `SSRPass`, drei `MeshReflectorMaterial` for floors | `ssr()`; always keep an env fallback |
| T14 | GI | none first-party | `ssgi()` (temporal filtering, recommended, requires `traa`); `vxgi()` from `three/addons/lighting/vxgi/VXGINode.js`; `LightProbeGrid` |
| T15 | motion blur | custom | `motionBlur(input, velocity, samples)` function |

Order: AO on indirect only, never stacked on baked AO. Grading (T2/T10): AgX has no punchy variant in r186 or pmndrs 6.39, so add contrast with a LUT (`LUT3DEffect`, or `lut3D` node) after tone mapping, then film grain (`film`) and dither last.

## Grade and lens

- LUT after tone map; 32³ is enough. Vignette/grain are cheap; chromatic aberration only if the brief names it.
- Adaptive exposure only if the brief needs it; fixed exposure is the marketing default.
- DOF: `target` is a world position, not a ref; SSAO in the wrapper needs `enableNormalPass`. DOF and SSAO are the expensive ones: budget one.

## Cost rules

- Each full-screen pass scales with pixel count: lowering DPR is the first fix.
- NEVER pass an inline-rebuilt `children` array to `<EffectComposer>`: identity change rebuilds every pass and render target (100–386 ms per frame measured in Safari). `useMemo` the effects; keep conditional children stable (pass `null` slots or toggle `enabled`/`blendFunction`).
- WebGPU: toggle a feature by relinking `outputNode` and setting `material.needsUpdate`/pipeline `needsUpdate = true`, not rebuilding the pipeline.
- Mobile: 0–1 passes.

## Validation

- Toggle post off: silhouette, material separation and focal point must still read ([shared-verification](shared-verification.md)).
- Black canvas with composer: check the render-target type, a missing `RenderPass`, or pipeline never `init`-ed.
