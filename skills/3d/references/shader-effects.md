# Shader Effects

Purpose: Recipes for the effects web 3D keeps asking for, each as technique, starting parameters and the failure it prevents; backend-neutral (GLSL or TSL).

Read when:
- Particles, sparks, pointer trails, falling leaves or snow; a hologram; a scan, build-up or scene-to-scene reveal; fire or glow ramps.
- Fog, clouds, light shafts, god rays, water, parallax relief, stars, holographic foil, wind on plants, backdrop terrain, snow or moss on a model, a 2D shader background.

Skip when:
- Writing or debugging the shader itself (precision, footprint filtering, cache keys, page compositing) → [shader-glsl](shader-glsl.md) or [shader-tsl](shader-tsl.md).
- Grading, bloom, AO → [threejs-postfx](threejs-postfx.md); metal, glass, fabric values → [design-lookdev-presets](design-lookdev-presets.md).

Inputs:
- The effect, the backend, the tier ([shared-performance](shared-performance.md)), what drives it (time, scroll, pointer).

Produces:
- One effect built from shared fields, its parameters in the tunables object, its failure check named.

## Contents

- Particles · Holograms and handovers · Reveals · Volumes and light shafts · Water · Relief · Stars and glints · Foil · Fire and glow · Wind and terrain · Accumulation · 2D shader backgrounds

## Particles

- Renderer first: a few branded fragments are DOM or SVG, dozens of simple motes a 2D canvas (the `scroll-animation` skill's layer); WebGL earns its cost at thousands, depth or shading.
- Allocate a worst-case pool once (typed arrays: origin, velocity, birth, seed) and spawn into a ring (`head = (head + 1) % N`). Flight is analytic in the vertex shader from `age = uTime - aBirth`; dead points get size 0 outside clip; upload only respawned ranges.
- Density = `setDrawRange(0, n * density)`, never a reallocation (it hitches), and count ÷ band area: tighten the band before raising count; scale authored counts by `clamp(sqrt(W * H / (1440 * 900)), .5, 1.3)`.
- Seeded per-instance parameters, uploaded once; vary every parameter or it reads as a scrolling texture.
- Pointer emitters emit by distance travelled, placed along the segment, capped (~14 per frame: a resumed tab hands over one huge move), plus a rare idle trickle.
- Spawn and recycle where the camera looks, prewarm so nothing is born on frame 1, fade at the band edge. Remove by swapping the last live instance into the hole with its matrix and every custom attribute.
- Cost is overdraw and uploads, not flight maths: small round sprites.

## Holograms and handovers

- Shell: front faces, `AdditiveBlending`, `depthWrite: false` (order-free, reads as projection). `f = pow(1. - abs(dot(N, V)), 2.)` softened as `f * (1. - smoothstep(0., .8, f))` (squared Fresnel alone is a hard outline); incidence in view space via `normalMatrix`.
- Scanlines phased on world height so the shape turns inside them, footprint-faded to the band's mean, never to zero. Glitch: a band gated by three incommensurate sines, so most of the surface sits at exactly 0.
- Shape handover: one normalised sweep over the UNION of all shapes' bounds (+0.1; per-shape ranges make the line jump); complementary discards (`n < p` outgoing, `n >= p` incoming) so additive passes never double; a linear sweep (eased lines brake visibly); index from absolute time (`floor(t * rate) % N`); every shape preallocated.

## Reveals

- Scan: one world-space front drives two representations: the solid discards beyond `R - lag` while a `LineSegments` cage of the same geometry (gaussian rim, trailing fade, additive, depth test on) leads it. Start outside the silhouette (centred reads as a loader); bend the front with two long sines (a perfect circle reads as a clip-path); `1 - (1 - t)^1.35` over ~3.4 s; reach = bounding diagonal × 1.3, measured after layout and matrix updates. On completion drop the discard branch and dispose the cage.
- Build-up: one clipping plane through every structural material plus a cap shaped like the section (a clipped shell is hollow); scaffolding runs one step ahead.
- Scene-to-scene wipe: a frozen snapshot of the outgoing scene composited with the live incoming one, scissored to the revealed side, at ~0.75 scale while moving, full size ~150 ms after rest.
- Reduced motion: a designed mid-reveal still.

## Volumes and light shafts

- March only the occupied interval (ray-box or shell entry and exit), clipped at opaque scene depth. Density = a shaped mask eroded by detail. Front to back with early exit at low transmittance; a capped ray returns mean radiance, not wherever it stopped. Start jitter: without temporal accumulation ≤ ¼ step from a stable per-pixel pattern (interleaved gradient noise), so stills do not crawl; with a temporal resolve, full-step spatiotemporal blue noise.
- Render at ½-¼ resolution into a half-float single-sample target; upsample depth-aware, or with a temporal resolve that resets on cuts and resizes and rejects disocclusion. Shadows from a cheap separate representation, never the beauty march. The low tier keeps silhouette and one short light march.
- Screen-space god rays: a dedicated sky-visibility mask (cutouts and wind matched); one sun direction for sky, rays and light; skip a sun behind the camera; divide by the weight sum (sample count must not change exposure); reject UVs outside the mask and fade as the sun leaves frame (edge clamping paints bands); add in linear HDR before tone mapping; 24-48 samples at half resolution. Whiteout is a bad mask or intensity, not missing bloom.
- Cheap shafts: additive planes faded by world height, kept behind solids (a plane through a solid draws a bright wedge), tone-mapped once. On an alpha canvas: [shader-glsl](shader-glsl.md) Canvas over a page.

## Water

- Per-pixel analytic normals from the same wave bundle as the displacement (a scrolling normal map that disagrees with the crests is the tell). Gerstner steepness ΣQ < 1 or the surface folds. Fade each wave by footprint, `1 - smoothstep(.18 * L, .5 * L, footprint)` (pixel: `2. * (fwidth(x) + fwidth(z))`; vertex: ~1.2 × grid spacing).
- Fresnel with `F0 = ((1 - η) / (1 + η))²` (0.02), never constant opacity. Reflect the visible sky and sun with `R.y = abs(R.y) + .002` (else grey smears on wave backs). Clear water has no colour: refraction + Fresnel + absorption; screen-space refraction depth-rejects foreground objects. Foam from the crest or Jacobian metric, never a scrolling texture. Fog takes the sky's horizon haze.
- Above or below water is decided once per draw, never per triangle; floating objects read height by inverting horizontal displacement.

## Relief

Parallax occlusion: layers `mix(maxL, minL, abs(viewDir.z))` (tiers 8/32, 16/96, 32/160), step guarded by `max(abs(v.z), minViewZ)` at grazing angles. March once and share the hit UV with every map; take gradients before `discard`; clamp fetches to the tile. Self-shadow lights direct only; cast shadows need the marched depth in the shadow pass.

## Stars and glints

- A cell lattice, one candidate per cell, hashed from the CELL and evaluated at the star's own direction (per-pixel tests flicker as the camera moves). Flux-conserving size, radius `max(S0, .62 * footprint)` with peak ∝ `S0² / s²`: sub-pixel stars widen and dim instead of aliasing; past ~one cell per pixel fade to the layer mean.
- Point skies: three size classes, `sizeAttenuation: false`, `fog: false`, `depthWrite: false`, additive, only in the band of sky the camera can reach.

## Foil

Hue from wavelength under the real light and view directions (grating equation), never from UV or time; motif masks choose groove angle and pitch only; the groove frame follows the object's world quaternion (world or camera axes make it slide or follow the viewer); add HDR radiance before tone mapping. Showing nothing can be correct: first check light and camera sit on the reflecting side.

## Fire and glow

Hot ramps run dull red → orange → yellow → near-white, only in that order (red mixed toward white is a salmon no temperature makes); rims cooler than centres, the pale core only where emission peaks. One stop table feeds the shader and its fallback. Spark streaks ≥ ~1.25 device px, saturated head, cooler tail. On a light page, smoke and steam stay light grey, never glow-inked.

## Wind and terrain

- Wind weight ∝ along² (or the card's `uv.y`) so roots stay put; leaves rotate about the petiole, heads follow the bent stem's tangent. Two incommensurate frequencies (`sin(1.1t + φ) + .32 sin(.63t + .4φ)`), phase from low-frequency noise; leaf, branch and plant sway are separate; the shadow depth material deforms identically. Grass: one instanced ribbon bent in the vertex shader on a camera-anchored, cell-snapped grid.
- Backdrop terrain: a polar grid under the camera, rings `r = R0 + (R1 - R0) * t^2.4` (a square heightfield spends triangles behind the camera). One analytic height function feeds mesh, scatter and fog, or props float; ridge amplitude grows with distance; vertex colour from slope, height and moisture, no tiled texture.

## Accumulation

Snow, moss, dust or wetness on a model: coverage in model-locked coordinates (world coordinates swim when it moves), gated by `smoothstep(.3, .85, worldNormal.y)` × a shelter tag (upward normals alone whiten covered floors), displaced along the normal in world thickness. One mask drives coverage, height and every PBR channel; raising coverage grows the same patches, never re-rolls them. Falling particles and the surface read the same wind and time uniforms; the settled amount is its own slow variable with separate build and melt rates.

## 2D shader backgrounds

- Mix gradient colours in OKLab, neutralising hue at very low chroma (sRGB mixing greys the middle); add the gated dither in [shader-glsl](shader-glsl.md) Aliasing and footprint.
- Object shaders fit a virtual world box (contain or cover) so composition survives any aspect; pattern shaders size in CSS pixels so density never stretches; screen-locked grain or dither grids come from `gl_FragCoord`.
- Size the canvas from ResizeObserver `devicePixelContentBoxSize` (fallback: DPR × rounded CSS size) × `visualViewport.scale`, capped by the pixel budget in [shared-performance](shared-performance.md). A heavy full-screen march renders at a fixed internal size, cover-fitted.
- Precompute logo masks once on the CPU (edge distance, opacity) and animate them in the shader.
