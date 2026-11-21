# GLSL Shaders in three

Purpose: Write custom GLSL for the WebGL renderer (ShaderMaterial or patched built-in materials) that survives version bumps, caching, mobile GPUs and the page it sits on.

Read when:
- Adding a custom effect (fresnel, dissolve, gradient, noise, vertex deformation) on `WebGLRenderer`.
- A patched material recompiles wrongly, shows the wrong variant, or breaks on a phone.
- Procedural detail shimmers or swims; an effect pops or cuts off; a canvas sits over a light page or inside 2D art.

Skip when:
- Renderer is `WebGPURenderer` or the scene needs compute → [shader-tsl](shader-tsl.md).
- A built-in material property already does it → [threejs-lookdev](threejs-lookdev.md).
- A named effect (particles, water, volumes, hologram, reveal) → [shader-effects](shader-effects.md), which links back here.

Inputs:
- Effect description, whether PBR lighting must be kept, target tier.

Produces:
- A material with stable uniforms, cache key, footprint-filtered detail, and a tested mobile fallback.

## Contents

- Choose the path · ShaderMaterial · onBeforeCompile · Recipes · Aliasing and footprint · Procedural fields · Envelopes and edges · Canvas over a page · Mobile and precision · Traps

## Choose the path

| Need | Path |
|---|---|
| Property exists on a built-in material | built-in |
| Keep PBR lighting, tweak colour/vertex | `onBeforeCompile` patch |
| Fully custom look or full-screen quad | `ShaderMaterial` / `RawShaderMaterial` / drei `shaderMaterial` |

## ShaderMaterial

1. Declare uniforms once (`useMemo` in R3F); change `.value` per frame. Never set `needsUpdate` for a value-only change.
2. `ShaderMaterial` injects `projectionMatrix`, `modelViewMatrix`, `normalMatrix`, `position`, `uv`, `cameraPosition` — do not redeclare (that is `RawShaderMaterial`'s job).
3. Colour output: add `#include <colorspace_fragment>` (after tone mapping chunk if used) so output colour space is applied once; use `<tonemapping_fragment>` only if the material should be tone-mapped. Hex colours into uniforms: `new Color(hex)` converts to linear; raw vectors are already linear.
4. Time: `uTime = frameOffset + Σ dt·speed` from the `Timer` delta, never `Date.now()`: the offset makes first frames and captures deterministic; speed 0 (static, off-screen, hidden) stops the loop, and a still shader redraws once, immediately, on resize.

## onBeforeCompile

1. Set before first render; patch by string-replacing a chunk marker (e.g. `#include <begin_vertex>`, `#include <color_fragment>`) and append uniforms to `shader.uniforms`.
2. Chunk names change between versions: print `shader.fragmentShader` once, replace with a guard (assert the marker exists, throw otherwise), render-test after each three bump.
3. When different variants of the patch exist, set `material.customProgramCacheKey = () => 'dissolve-v2-' + variant`. The default key is the function's source text, so variants collide when the same patch text closes over different values.
4. `clone()` does NOT copy `onBeforeCompile` (nor `customProgramCacheKey`): a cloned patched material renders unpatched. Re-assign both on every clone and keep a uniform reference per instance.
5. R3F: `onBeforeCompile` prop is fine; store the shader ref to update uniforms in `useFrame`.

## Recipes

- Fresnel: `float f = pow(1.0 - saturate(dot(normalize(vNormal), normalize(vViewPosition))), 3.0);` — both in view space. `normalMatrix * normal` is view space: never dot it with a world-space camera vector.
- Dissolve: `float n = noise(vWorldPos * scale); if (n < uProgress) discard;` + emissive edge `smoothstep(uProgress, uProgress + 0.05, n)`. Mirror in `customDepthMaterial` or shadows ignore the cut. Many objects: per-instance attributes (seed, start time) on one material, never a cloned material each.
- Gradient: mix on `vUv.y` or local `position.y`; colours in linear (OKLab mixing for 2D fields: [shader-effects](shader-effects.md)).
- Vertex deformation: raise subdivisions, recompute normals, mirror in `customDepthMaterial`/`customDistanceMaterial`. Culling and raycast bounds do not follow GPU displacement: set `frustumCulled = false` or enlarge `geometry.boundingSphere`. Hard-surface normals (CPU, once at load): `BufferGeometryUtils.toCreasedNormals(geo, angleRad)` (~0.55-0.87 rad; returns non-indexed geometry), never a plain `computeVertexNormals()` (rounds edges). Deforming textured surfaces keep rest UVs, or the weave swims.

## Aliasing and footprint

Procedural detail has no mip chain: filter every band yourself. MSAA fixes none of this.

1. Edges: `smoothstep(e - s, e + s + max(fwidth(v), 1e-4), v)`, so a designed softness of 0 still gets a one-pixel floor (and the edges never meet). Never `step()`.
2. Periodic bands fade by footprint, `* (1. - smoothstep(a, b, fwidth(coord) * freq))`, toward the band's MEAN, never to zero (receding surfaces darken); frequencies stay fixed, bump fades before colour, and a period under ~2.5-5 device px is gone.
3. Specular AA for procedural or bumpy normals: `v = max(dot(dFdx(N), dFdx(N)), dot(dFdy(N), dFdy(N)))`, `rough = clamp(sqrt(rough * rough + v), 0., 1.)`.
4. Thin lines stay ≥ ~1 device px wide; below that, fade coverage. Never displace with frequencies the mesh cannot represent.
5. Output of a standalone effect: tone-map, never `clamp`; then ±1 LSB animated triangular dither gated by `smoothstep(0., 1.5/255., maxChannel)` so empty pixels stay exactly 0 (premultiplied: dither rgb and alpha together).

Prove it with the half-pixel shimmer check in [shared-verification](shared-verification.md).

## Procedural fields

- Write the bundle before code: coordinates → macro form → meso structure → causes (wear, wetness, exposure) → channels. The same named fields feed every channel; independent noise per channel reads as printed on.
- One stable domain per cause: object or undeformed coordinates for form (noise on displaced positions stretches), one shared world plane for water and wetness, a stable per-instance seed. Warp coordinates, not results; separate bands for silhouette, regions, breakup and micro-normal; perceptual names (`ridgeWidth`, not `noise3Amount`) and a debug view per field.
- Bake periodic noise once (1024² RGBA8, repeat, mipmapped, `NoColorSpace`) and sample it at several stretches: mips filter for free and cost a fraction of live octaves. Slopes of a baked field: finite differences a few px apart, never `dFdx` of one texel. Clamp bump gradients so steps never flip the normal.
- Fire, smoke, water and mist evolve in place: drift a warp field through the noise; scrolled or spun noise reads as sliding cloth.

## Envelopes and edges

- **Nothing pops.** Every animated uniform rides an envelope: an event keeps its start time, a `smoothstep` attack (40-120 ms, zero slope at onset), then exponential decay; overlapping events sum (a list, never one overwritten start). Phase changes crossfade on the physical quantity; hue settles separately and slower (~0.3-0.5 s); brightness only falls in a fade-out. Frame-rate-independent decay: [threejs-interaction](threejs-interaction.md) Procedural motion.
- **No hard cut-offs.** Every term reaches 0 before any `if`, bound or canvas edge. Cell noise keeps offset + radius + tail under half a cell or samples the 3×3 neighbours; radial noise uses the direction vector, not `atan` (seam at ±π).
- Build effects in world space with the scene camera (a screen-space glow runs through floors).

## Canvas over a page

- **Light page:** normal blending, premultiplied, never `screen` (over white it stays white). Nothing is brighter than the paper, so light reads through saturation and contrast: saturated body, pale core, coloured rim, an alpha floor at the hot end (else the core reads as a hole). Design the colour seen, then solve the ink: `absorbed = 1. - seen; a = max(maxChannel(absorbed), cover); rgb = a - absorbed` (composites to exactly `seen` over white).
- One accumulator per kind of light (emission alpha ≤ ~.97; light on a surface as a tint, ≤ .5-.8; haze `1. - exp(-density * k)`; sparks on top), composited back to front with `top + under * (1. - top.a)`; inking the summed energy loses the core. Clamp `rgb ≤ a` after sums; no halos in empty air; the cavity holding the light gets a darker physical ground, never a black box.
- `AdditiveBlending` also adds alpha: on an `alpha: true` canvas over the page use `CustomBlending` (src `One`, dst `One`, srcAlpha `Zero`, dstAlpha `One`).
- **Inside 2D art** nothing depth-tests: stack back art, canvas (`pointer-events: none`), front art in one box and viewBox; a part on both sides is split or modelled in the shader as a simple occluder. Ink ends at a stroke's inner edge.
- Judge brightness on the composed page ([shared-verification](shared-verification.md)).

## Mobile and precision

- three compiles at `highp` unless unsupported. An explicit `mediump` (`material.precision`, `RawShaderMaterial`, a raw WebGL canvas) is 23-bit on desktops but 10-bit on many phones, so it passes on a laptop and breaks on Android: read `gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.MEDIUM_FLOAT).precision` and promote below 23. Positions, UVs and time stay `highp`.
- A growing `uTime` loses float32 precision, and `mod(uTime, 1000.)` jumps at every wrap unless each frequency × 1000 is a whole multiple of 2π. Wrap each oscillator's phase `ω·t` to [0, 2π) on the CPU (float64) and upload the phase: large `sin()` arguments jitter.
- `fract(sin(x) * 43758.5)` repeats or biases on Apple Metal and some Android GPUs: use an integer or sine-free arithmetic hash, or a small noise texture.
- Loops compile a constant maximum (e.g. 64) and `break` on an integer quality uniform. Texture reads in loops or non-uniform branches have undefined derivatives: use explicit LOD or gradients. Replace per-pixel `pow` chains with a lookup texture.
- Test noise-heavy shaders with DPR 3 on a phone: fill rate is the cost.

## Traps

- A backtick or `${` anywhere in GLSL (even a comment) inside a JS template literal ends the string early; a `//` comment in a one-line template string comments out the rest of the shader (nothing draws, no error): use `/* */`.
- three compiles GLSL ES 3.00: `texture`, `sample`, `filter`, `input`, `output`, `flat`, `smooth` are reserved or built-in and fail as identifiers. Uniform names clash with built-ins (`time`, `color`) if declared twice; prefix `u`.
- `smoothstep(e0, e1, x)` is undefined when `e0 >= e1` (driver-dependent): write `1. - smoothstep(lo, hi, x)`. `pow` of a negative base is undefined: clamp it. Guard every normalisation (`sum / max(wsum, 1e-5)`; rgb and alpha separately).
- `PointsMaterial.size` is already multiplied by the renderer pixel ratio (r186): scaling by `devicePixelRatio` doubles it. A custom `gl_PointSize` must multiply by it itself.
- `Float32BufferAttribute` copies its array (r186): mutate `attr.array`, then `needsUpdate = true`, or nothing moves; animated attributes `setUsage(DynamicDrawUsage)`.
- Data targets (distance, normal): half-float, nearest-filtered, `samples: 0`. Data masks: a `DataTexture` from `getImageData`, never an alpha canvas texture (premultiplied). Stochastic taps: stable per-pixel noise.
- `#include <colorspace_pars_fragment>` in a `ShaderMaterial` or `ShaderPass` fails with "function already has a body" (`LinearTransferOETF`, `sRGBTransferOETF`): three already prefixes it. Only `RawShaderMaterial` includes it. `<colorspace_fragment>` (the call) stays. The failure is silent unless loud: [threejs-renderer](threejs-renderer.md) "Shader errors".
- GLSL does not run on `WebGPURenderer`; the same effect must be re-expressed in TSL.
- A shader that compiles proves nothing about the look: compare with a no-shader baseline screenshot ([shared-verification](shared-verification.md)).
