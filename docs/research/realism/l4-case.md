# L4 case study: the eagle-training gold-blade recreation

Sources: local record only, graded [V-local] (read 2026-10-16): `threejs-recreation/3D.md`, `.3d/brief.md`, `.3d/questions.md`, `.3d/reference-spec.json`, `index.html` (v012), `generation-prompts.json`, `README.md`, boards `before_after_v001_v009_v012_ref.png`, `v012.png`, and the reference still. Claims about three.js features come from general knowledge, not fetched in this lane: graded [U] until L1/L2 cite them. Gain estimates are my judgement, [U].

## 0. What the reference is

- Not a render. `generation-prompts.json`: Seedance 2.5, `omni_reference`, start and end image = the same still, "locked camera", loop. So the target is a **diffusion-model image and video**, not path-traced CGI. README says "Higgsfield Seedance 2.5". [V-local]
- Consequences for a gate:
  - Perspective is inconsistent (3D.md decision 5: near blades fit VP ~1.4, far field converges at the edge), so v012 bends the rows to fake it.
  - Reflections are painted: faces vary blade to blade (dark bronze, bright gold, hard stripes); edge bands are mirror strips brightest on gap-facing tips.
  - The spec says "env contrast low", but the images show a high-contrast reflective look; that wording steered the env choice wrong.
  - Blade sway is a model's idea of a 2-degree wave, measured at +/-4.5 px at 960 wide.
- Fidelity target approved at intake: "close match, not pixel-identical" (Q1). Acceptance rubric then demanded critic scores of at least 2 in every category, average at least 2.3, against a diffusion reference. No gate ever compared those two.

## 1. Per-defect table (critic rounds R1-R7 in 3D.md)

Class key: **FIX** = fixable technique gap (missing technique named); **LIM** = real-time limit (offline feature named); **REF** = inconsistent or painted reference artefact.

| # | Defect (round) | Class | Missing technique / offline feature | Notes |
|---|---|---|---|---|
| 1 | Flat D-shaped blades, flat faces (R1, R6 "card-like flat faces + outline rims", R5 "lens-shaped slabs") | FIX | Bevel/chamfer geometry with real normals, plus a face-to-face varied reflection source. Partly done in v012 (rounded bevels). | v012 still shows uniform yellow faces |
| 2 | Faces too uniform/yellow, vs the reference's alternating dark bronze and bright gold (R4 "flat bright faces vs shaded bronze", R5 "alternating dark faces", R7) | FIX (partly REF) | A high-contrast env with a few hard-edged strip/softbox reflections, mapped per face. v010-v012 tried a strip env but by hand and in PMREM; per-face variation needs the reflection direction to differ across blades, which a distant env does not give | Reference variation is painted, so exact match is REF; a similar-feeling variation is FIX |
| 3 | Edge bands matte, not mirror (R7 top defect) | FIX | Sharp, high-dynamic-range env detail seen at low roughness (strip lights as emissive geometry in the env scene, PMREM at roughness near 0.05), or real thin RectAreaLight strips. Edge roughness 0.07 was set, but the env behind it is smooth gradients | Largest single lighting gap |
| 4 | Edge halos and "outline rims" (R1, R6) | FIX | Gap-gradient shading in the shader instead of a constant rim; v011/v012 moved this into a `gapGlow` shader hack | Shader fakes what a light would do |
| 5 | Light from filaments not on the blades: "front-lit banks" (R4), "no wall glow at tips" (R6) | FIX / LIM | FIX: RectAreaLight or a few point lights along the gap, wall spill. LIM: true bounce between blades (global illumination). v012 used emissive-gain hacks and a fake wall quad | Brief section 7 specified point lights; v012 `index.html` has none of `PointLight`, `RectAreaLight` in a grep |
| 6 | Contact shadows and ambient occlusion in the gaps between blades (spec: "soft occlusion where blades meet the wall") | FIX | Baked/vertex AO per blade root, or a cheap SSAO/GTAO pass. Never attempted ("no shadow maps", approved Q4) | Cheap, and it separates blades from the wall |
| 7 | Filament: looked like braided rope, ribbon cable, kinked, loose strands, wavy (R1, R2, R5, R6, R7) | FIX | Ribbon geometry in screen space with additive core + halo and curve fitted to the measured path. 4 of 7 rounds spent here | Technique exists; iteration was spent on parameter tuning, not on a reference-curve fit |
| 8 | Hot pale cream bands, VP bloom blob, VP fog cloud, yellow haze (R2, R3, R6, R7) | FIX | Selective bloom (only filament layer), bloom threshold above scene max, tone-map-aware gain. v007 capped blades at 1.4 under threshold 1.5, which is the right idea, found at R3 | Tuning, not a limit |
| 9 | Banks stop short of the edge, composition 2/3 every round | FIX / REF | Camera/lens-shift fit was done; the residual is the inconsistent-perspective reference (decision 5). A single pinhole camera cannot match, so geometry was bent | Composition capped at 2 by REF, not by three.js |
| 10 | Pulses not travelling, shimmer, 2-hump rhythm, 4-per-loop rhythm, bundle pumping (R3, R4, R5, R7) | FIX | Pure motion tuning from measurements (kymograph); solved by v008, then regressed when look changed | Not a rendering limit |
| 11 | Sway too small (65%, then 5x too small on screen) (R4, R6) | FIX | Measurement error between %W and px, fixed by v012 | |
| 12 | Texture of the satin: mottled, "gold leaf" crinkle in the still | LIM-ish | Anisotropic brushed roughness map, or a baked texture from the still itself. v010 used object-space value noise (procedural) | Texture is a painted detail; a baked normal/roughness map would get closer; procedural will not |

Counts over the 12 groups: 9 FIX, 1 FIX-or-LIM, 1 LIM-ish, 1 REF (REF also caps #2 and #9). Almost nothing that failed was an unreachable offline-only feature. What failed was **technique selection and its order**, not the renderer.

## 2. Realistic real-time ceiling for this reference

- Honest ceiling in three.js for gold blades on a grey wall: **close in feel, not close in pixels.**
  - Look-dev score a fresh critic would give with the best known techniques: lighting/materials 2/3, composition 2/3, motion 2/3, fidelity 1-2/3. Average about 2.0-2.2. Overall: a strong stylised cousin that is recognisably the same piece.
  - The brief's ship bar (every category at least 2, average at least 2.3) sat above this, because composition and fidelity are capped by the reference's inconsistent perspective and painted reflections. The bar was unreachable by definition; the run could not have known that without a gate.
- Offline-only features this reference leans on:
  - Global illumination and inter-reflection (blade-to-blade, filament-to-blade, wall bounce). Real-time substitutes: baked AO, RectAreaLight, SSR, light probes. Each recovers part, none all.
  - Path-traced caustic-like edge highlights with exact area-light shapes.
  - Painted, per-face reflection variation (REF; nothing computes this).
  - Spatially consistent volumetric halo around filaments (real-time: additive ribbons plus bloom, which is close for a halo this soft).
- Not offline-only, despite how it read in the rounds: mirror edge bands, per-face tonal variation, filament glow and core, DOF falloff, wall light spill.

### Techniques v012 never tried (grep of `index.html`: no `RectAreaLight`, `PointLight`, SSR, SSAO/GTAO, `anisotropy`, `clearcoat`, baked maps, shadows)

| # | Technique | Targets defect | Expected gain [U] |
|---|---|---|---|
| T1 | Contrasty custom env with hard emissive strip lights (thin, very bright quads in the env scene, PMREM, near-zero roughness on edge bands). v010 had softboxes, but smooth (width 0.45-0.5 half-width, intensity 0.35-0.6), so bands read matte | #3, #2 | Edge bands go matte to mirror-ish: +1 lighting, +0.5 materials. Cheapest, biggest |
| T2 | RectAreaLight strip(s) along the gap (needs `RectAreaLightUniformsLib`, works on Standard/Physical only, no shadows) to light blade faces and edge bands from the filament line, replacing the `gapGlow` shader hack | #5, #4, #1 | +0.5 lighting; faces gain a real gradient toward the gap |
| T3 | Baked/vertex AO at blade roots and between blades, or one GTAO pass | #6, #1 | +0.5 materials/composition feel; separates blades from the wall |
| T4 | Selective bloom (filament layer only, via `SelectiveBloomEffect` in pmndrs postprocessing or a layer mask in the composer) so blade edges never bloom and bloom radius is tunable per source | #8 | Removes the haze/blob class of defects (4 critic rounds); +0.5 colour/lighting |
| T5 | Anisotropic brushed gold: `MeshPhysicalMaterial.anisotropy` (+ rotation) with a small roughness map baked from the still's crop (the still has visible leaf texture) | #12, #2 | +0.5 materials on close faces; low risk |

None needs an offline renderer. The run tried a studio env and one bloom pass; T2-T5 never, T1 only in smooth form. T6 (SSR / one-bounce fake) is a costly last resort.

## 3. Where a feasibility gate would have spoken

1. **Intake, before Q1 was answered (3D.md decision 1/2, 2026-10-16 ~16:40).** `reference-spec.json` was written with `medium: cgi-real` and `lighting.env.contrast: low`, while `generation-prompts.json` sat in the same folder saying "Seedance" and "locked camera". A gate that reads provenance says:
   - "Reference is generative video. Expected ceiling ~2.0-2.2 of 3 average; perspective is inconsistent so composition caps at 2; offline-only: inter-reflection/GI, painted per-face reflections. Fixable: edge mirror bands, AO, filaments, motion. Proposed rubric: ship at average >= 2.0 and no category < 1.5, or pick approach B (still plate + live light) up front."
   - That would have replaced the unreachable "avg >= 2.3 / all >= 2" bar and surfaced option B (the user's eventual choice) at hour 0 rather than at v015.
2. **After v004 (R1 FAIL, 1.29).** The first critic list contained only FIX items. A gate that classifies defects after round 1 would have produced the T1-T5 list here and ordered them by gain; the run instead tuned parameters for 7 rounds.
3. **After R3 (v006, avg 1.5, composition 2).** Composition 2 / colour 2 / anchors 2 appeared and then never moved again (R3, R4, R6, R7 all 2 on the same three). That plateau is the signal that the cap is REF, not effort.

## 4. Stop point a good mechanism would have chosen

Critic averages (3D.md):

| Round | Version | Avg | Delta | Categories moving |
|---|---|---|---|---|
| R1 | v004 | 1.29 | n/a | |
| R2 | v005 | 1.17 | -0.12 | worse after "lean + thick bands" |
| R3 | v006 | 1.50 | +0.33 | composition 2 |
| R4 | v008 | 1.50 | 0.00 | comp 2, colour 2, anchors 2; lighting/materials/motion 1 |
| R5 | v010 | 1.33 | -0.17 | dark env regressed to braided rope, pumping |
| R6 | v011 | 1.50 | +0.17 | same 2/2/2 |
| R7 | v012 | 1.50 | 0.00 | same 2/2/2; lighting/materials/motion 1 |

- Best 1.5 reached at R3 (v006), then 4 more rounds produced no net gain: deltas across R3 to R7 sum to 0.00 with a range 1.33-1.50.
- Lighting, materials and motion sat at 1 in every failing round that listed them. The same three never moved because the changes tried (colour, parameters) were not the missing techniques (T1-T5).
- **Stop rule that would have fired:** "two consecutive rounds with delta <= 0.15 and the same lowest-scoring categories unchanged, and the open defects are mapped to unlisted techniques or offline-only." That fires at **R4 (v008)**: R3 to R4 delta 0.00 with lighting/materials/motion still 1.
- At R4 the right output is not "keep iterating" but: "Real-time ceiling reached for the techniques tried: 1.5. Unlocked next steps with expected gain: T1 (+1 lighting), T2, T3, T4. Offline-only: GI, painted reflections. Choose: (a) try T1-T4 for at most 2 more rounds with a gain target of 0.3 per round, (b) accept ~2.0 as the ship bar, (c) switch to plate + live light (B), (d) ship the supplied loop.mp4."
- Rounds saved: R5-R7 (3 critic rounds) and v013-v016 (four versions, two rejected approaches), about 2.5 h of the 16:40-19:30 run [V-local timestamps].
- Secondary: luma (+/-0.05 from v003) and SSIM 0.70 passed or hovered while critics failed; across pipelines they carry no progress signal.

## 5. Gate requirements this case implies

1. Provenance check: generative reference means cap composition and fidelity at 2 and say so before intake.
2. Per-round defect classifier FIX(untried technique) / LIM(offline feature) / REF.
3. Ceiling statement before build; ship bar set from it.
4. Stop rule: two rounds with |delta| <= 0.15 and unchanged lowest categories, or no untried FIX left; then present best version, ceiling, untried list and choices.
5. Offer plate-plus-live-light and video fallback at intake when ceiling < bar.
6. SSIM/luma guard regressions only; never count them as progress.
