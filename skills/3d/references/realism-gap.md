# Realism Gap: What Real-Time Can Match

Purpose: Tier each visual feature of an offline or AI reference as live, bake-only, offline-only or reference artefact, and derive the per-category ceiling.

Read when:
- A reference is a Cycles/Redshift render, photo, or AI image/video and the brief says "match".
- The feasibility gate runs, or a critic defect must be labelled FIXABLE / CEILING / ARTEFACT.

Skip when:
- Choosing or applying a technique → [realism-toolbox](realism-toolbox.md).
- Running the iterate loop or stop rule → [realism-gate](realism-gate.md).

Inputs:
- refspec features ([refspec](refspec.md)), scene dynamics (static or moving lights/objects), target device and backend.

Produces:
- Per-feature tier, per-category cap, artefact claims with evidence.

## Contents

- Tiers · Feature table · Reference artefacts · Category caps · Ranking · Traps

## Tiers

- `LIVE-NATIVE`: core API, ~0 cost.
- `LIVE-WITH-TECHNIQUE`: a named technique from the toolbox, cost stated; may be WebGPU- or desktop-only.
- `BAKE-ONLY`: correct only when the element and its lights are static (Blender bake or one-off capture).
- `OFFLINE-ONLY`: no live equivalent; reachable only as path-traced stills (Cycles, or in-browser T18). For a live-3D brief that means a still or refine-when-idle route, never a swap of the deliverable.
- `REFERENCE-ARTEFACT`: the reference is physically inconsistent; nothing computes it.

Tier depends on pipeline, scene dynamics and device. A WebGPU-only technique on a WebGL or mobile target counts one tier down.

## Feature table

Visibility: S = obvious at a glance, O = noticed on inspection, D = defines the look. Costs live in the toolbox.

| id | feature | category | vis | static | dynamic | T |
|---|---|---|---|---|---|---|
| G1 | multi-bounce GI, colour bleed | lighting | D | BAKE | OFFLINE (partial T14, WebGPU desktop) | 4, 14 |
| G2 | glossy inter-reflection between objects | materials | D on polished metal | BAKE (T5 once) | LIVE-T for a few objects; OFFLINE for many moving polished parts | 5, 13 |
| G3 | reflected designed lighting (shaped highlights) | materials | D | LIVE-N | LIVE-N | 1 |
| G4 | area-light highlight shape, softness | lighting | D | LIVE-T | LIVE-T | 1, 8 |
| G5 | soft shadows, contact hardening, exact penumbra | lighting | O | BAKE or accumulated | LIVE-T approx; exact OFFLINE | 4, 6 |
| G6 | AO, contact darkening | lighting | O | BAKE or LIVE-T | LIVE-T | 4, 7 |
| G7 | emissive surfaces lighting neighbours | lighting | O | BAKE | LIVE-T (pair with real lights) | 4, 8 |
| G8 | thin single refraction/transmission | materials | O | LIVE-T | LIVE-T; thick/nested OFFLINE | 16 |
| G9 | caustics | lighting | O | LIVE-T (fake) | fake; true OFFLINE | 17 |
| G10 | subsurface scattering | materials | S/O | LIVE-T approx | same; accurate OFFLINE | 17 |
| G11 | volumetrics, shafts, lit haze | fx | O | LIVE-T approx | shadowed multi-scatter OFFLINE | 17 |
| G12 | view transform, highlight roll-off, hue under brightness | colour | D | LIVE-N | LIVE-N | 2 |
| G13 | bloom, glare | fx | S | LIVE-N (post) | same | 9 |
| G14 | depth of field, bokeh | fx | O | LIVE-T | same; exact optical bokeh OFFLINE | 12 |
| G15 | motion blur | fx | O (fast motion) | LIVE-T | same | 15 |
| G16 | AA, thin-edge specular shimmer | fx | S-O | LIVE-T | same | 11 |
| G17 | banding in dark gradients (8-bit) | colour | O (dark scenes) | LIVE-T | same | 10 |
| G18 | micro-detail, brushed grain, glints | materials | O | LIVE-T; per-pixel moving glints OFFLINE | same | 3 |
| G19 | lobes: clearcoat, sheen, iridescence, anisotropy | materials | S | LIVE-N | LIVE-N | 3 |
| G20 | silhouette detail, displacement | materials | O | BAKE (normal maps) | micro-displacement OFFLINE | 3 |
| G21 | geometry, camera, lens, framing | composition | - | LIVE-N | LIVE-N | design, never a ceiling |
| G22 | motion timing, paths, sway, loop | motion | - | LIVE-N | LIVE-N | design, never a ceiling |

## Reference artefacts (AI image/video)

- R1 inconsistent perspective or vanishing points: caps composition, fidelity.
- R2 painted or sourceless reflections and highlights, per-face variation no environment produces: caps materials, lighting.
- R3 temporal drift: count, spacing or shape morph, loop not closing: caps motion, fidelity.
- R4 light sources drifting between frames: caps lighting.
- R5 baked-in lens and grade: NOT a cap, reproducible with T10/T12 (listed so nobody labels it ARTEFACT).

Claim an artefact only with the intake consistency result (refspec `provenance.consistency`) or a named frame pair showing it.

## Category caps

Start every category at 3.
1. A D-visibility feature at OFFLINE-ONLY: cap 2. An O-visibility one: cap 2.5. S-visibility: no cap.
2. BAKE-ONLY with a dynamic brief counts as OFFLINE-ONLY.
3. An R1-R4 artefact touching the category: cap 2 ("stylised match").
4. Fidelity = min(other caps, artefact cap). Composition and motion are never capped by the renderer (G21, G22), only by R1/R3.

These numbers are calibrated on one case [U]; treat as starting values.

## Ranking

Defining gaps, worst first: inter-reflection, GI, light shape, tone roll-off, grounding. Most live "path-traced" looks fail at T1, T2, T3, T4, not at GI.

## Traps

- Calling a G3/G4/G12 gap a limit: those are LIVE. Try T1, T2 first.
- Labelling an AI reference's lens look (R5) an artefact.
- Trusting ssim against a reference rendered by a different pipeline.
