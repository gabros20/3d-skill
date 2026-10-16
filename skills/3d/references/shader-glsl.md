# GLSL Shaders in three

Purpose: Write custom GLSL for the WebGL renderer (ShaderMaterial or patched built-in materials) that survives version bumps, caching and mobile GPUs.

Read when:
- Adding a custom effect (fresnel, dissolve, gradient, noise, vertex deformation) on `WebGLRenderer`.
- A patched material recompiles wrongly, shows the wrong variant, or breaks on a phone.

Skip when:
- Renderer is `WebGPURenderer` or the scene needs compute → [shader-tsl](shader-tsl.md).
- A built-in material property already does it → [threejs-lookdev](threejs-lookdev.md).

Inputs:
- Effect description, whether PBR lighting must be kept, target tier.

Produces:
- A material with stable uniforms, cache key, and a tested mobile fallback.

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
4. Time uniform from the `Timer` delta accumulation, not `Date.now()`.

## onBeforeCompile

1. Set before first render; patch by string-replacing a chunk marker (e.g. `#include <begin_vertex>`, `#include <color_fragment>`) and append uniforms to `shader.uniforms`.
2. Chunk names change between versions: print `shader.fragmentShader` once, replace with a guard (assert the marker exists, throw otherwise), render-test after each three bump.
3. When different variants of the patch exist, set `material.customProgramCacheKey = () => 'dissolve-v2-' + variant`. Without it three reuses one program for all materials of the same type and your variants collide.
4. Cloned materials copy `onBeforeCompile`; patched uniforms live in your closure, so keep a reference per instance.
5. R3F: `onBeforeCompile` prop is fine; store the shader ref to update uniforms in `useFrame`.

## Recipes

- Fresnel: `float f = pow(1.0 - saturate(dot(normalize(vNormal), normalize(vViewPosition))), 3.0);` — both in view space. `normalMatrix * normal` is view space: never dot it with a world-space camera vector.
- Dissolve: `float n = noise(vWorldPos * scale); if (n < uProgress) discard;` + emissive edge `smoothstep(uProgress, uProgress + 0.05, n)`. Mirror in `customDepthMaterial` or shadows ignore the cut.
- Gradient: mix on `vUv.y` or local `position.y`; colours in linear.
- Vertex deformation: raise subdivisions, recompute normals, mirror in `customDepthMaterial`/`customDistanceMaterial`. Culling and raycast bounds do not follow GPU displacement: set `frustumCulled = false` or enlarge `geometry.boundingSphere`.

## Mobile and precision

- Declare precision explicitly in `RawShaderMaterial`; `ShaderMaterial` sets it from `material.precision`. Use `mediump` only for colour math that needs no range; keep `highp` for positions, UV math and time.
- A growing `uTime` loses precision on long-running pages: wrap with `mod(t, 1000.0)` or drive loops with `fract`.
- Avoid dynamic loops with unbounded counts, dependent texture reads in loops, and per-pixel `pow` chains; use a lookup texture.
- Test noise-heavy shaders with DPR 3 on a phone: fill rate is the cost.

## Traps

- A backtick or `${` anywhere in GLSL (even a comment) inside a JS template literal ends the string early.
- Uniform names clash with built-ins (`time`, `color`) if declared twice; prefix `u`.
- GLSL does not run on `WebGPURenderer`; the same effect must be re-expressed in TSL.
- A shader that compiles proves nothing about the look: compare with a no-shader baseline screenshot ([shared-verification](shared-verification.md)).
