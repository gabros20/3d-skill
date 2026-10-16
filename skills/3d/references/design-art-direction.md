# 3D Art Direction

Purpose: Decide what the 3D should be and how it is composed and shot, before any geometry: world sentence, concept-to-form, scene ledger, camera as cinematography, critique.

Read when:
- "What should the 3D be", "hero for X brand", "world", "chapters", "mood", "art direction".
- A scene "looks flat / CG / amateur", or six chapters look the same.

Skip when:
- Light numbers, materials, tone mapping → [design-lookdev-presets](design-lookdev-presets.md).
- Writing the brief, storyboard, `shots.json` → [brief-spec](brief-spec.md).
- Driving the camera from scroll → [scroll-conductor](scroll-conductor.md).

Inputs:
- Purpose, audience, ordered beats, brand constants, reference analysis (`.3d/reference-spec.json`), device floor.

Produces:
- World sentence, world bible, scene ledger (in `3D.md`), shot intent per chapter (camera language only; the shot list, storyboard and `shots.json` are built from it in [brief-spec](brief-spec.md)), a critique list.

## Procedure

1. **Intake**: ask only what cannot be inferred, using [intake-grill](intake-grill.md); topology (continuous, connected sets, layered reveal) is the one extra decision here. If a working scene or approved reference exists, copy its measured constants into the ledger; never replace measured details with adjectives.
2. **World sentence** = subject + spatial journey + transformation ("A reader falls through the model's layers until the chip lights up"). Add an interaction sentence: scroll owns the camera and global time; pointer, touch, keyboard reveal local evidence. Reject any sentence that only describes style.
3. **Concept-to-form.** Write "This scene shows ___, moving like ___, because ___" before geometry. Icosahedra, torus knots and floating glass blobs are the default trap. **"No hero object" is a valid answer**: real product UI, a gradient field, type, or video can carry the page better. Motion borrows from the referent (mechanical = stepped, signal = pulse then rest). Calm is not frozen: per-node sine drift with a random phase.
4. **World bible** with real constants, committed in writing before markup: unit (1 u = 1 m), human reference 1.7, bevel 0.5-2% of width, silhouette > structure > accent, palette by role name (one hue family, never one grey), FOV range, horizon, copy-safe zones per breakpoint, motion table (camera damping 4.5-7, pointer parallax 0.1-0.5 deg, dust 0.02-0.12 u/s, word reveal 40-90 ms), named anti-references.
5. **Scene ledger**, 4-8 chapters, one row each:

| id | beat | landmark | change (beyond copy) | weight | camera pos / target / fov (desktop, mobile) | world state | copy zone | assets | fallback |
|---|---|---|---|---|---|---|---|---|---|

   Reject a chapter whose landmark, change and camera cannot be named. Weight is the scroll share of the leg to the next chapter ([scroll-conductor](scroll-conductor.md)).
6. **Camera ledger before curves**: endpoints per breakpoint, roll, near/far, failure risk (clipping, target flips, velocity spikes at joins, copy overlap). Compose endpoints at desktop and mobile first, then interpolate. Sample against coarse proxies offline; do not collide per frame.
7. **Tempo map**: rests, accents, max groups moving at once, one primary peak. At most three scroll-trigger pattern families on a page. Reduced motion is an alternative direction, not zero.

## Composition

- **Marketing hero**: one subject, negative space reserved for copy, HDRI plus contact shadow instead of hand-placed lights, a long-lens look (lens: [brief-spec](brief-spec.md)), a poster that already sells the page.
- **World**: depth planes separated by fog and value, the focal landmark inside the contrast window, foreground element for parallax, a threshold or occluder to hide every seam, never an open-space teleport.
- Frame by viewport height. Mobile is a second composition (pull back, own copy zones), not a crop.

## Camera as cinematography

Lens numbers (full-frame equivalent defaults by shot type) live in [brief-spec](brief-spec.md); here you choose intent and rig.

| Shot intent | Look | Rig (path / conductor) | Use |
|---|---|---|---|
| Establish | wide, deep space | slow dolly in along path | context, scale, first chapter |
| Neutral | natural perspective | track, lateral curve | explaining parts |
| Intimate | mild compression | small orbit, +-0.3 rad | people, UI surfaces |
| Hero product | long, flattering, compressed | orbit or push, long dwell | the object, the payoff |
| Macro / detail | very long, shallow DOF | push-in | one feature, close-up texture |
| Reveal | wide-normal | pedestal or track past an occluder | change of state or place |

Move the camera, not the object, unless the object is the story. One lateral or vertical component per path; at least five control points; fog 0.005-0.02, never above 0.03 (unmeasured taste, [U]). Waypoint copy needs a backdrop.

## Critique: "looks flat / CG / amateur"

| Symptom | Cause | Fix |
|---|---|---|
| Flat, grey | env intensity too high against key; no rim; no depth fog | key:env about 4:0.45 as a start; add rim; fog by plane |
| Plastic, CG | perfect edges, uniform roughness, one grey | bevel 0.5-2%, roughness variation, causal wear (edges polish, recesses grime), palette by role |
| Brand colour muddy | ACES (R3F default) shifting hue | Khronos PBR Neutral; see [design-lookdev-presets](design-lookdev-presets.md) |
| Hazy, amateur glow | bloom radius wide, threshold low, effects hiding weak materials | threshold above brightest lit surface, strength 0.25-0.35; compose the unprocessed frame first |
| Floating objects | no contact shadow or AO | ContactShadows, baked AO |
| Six identical chapters | centred dolly-ins, no change | ledger rule above; vary shot, landmark, world state |
| Dead | nothing moves at rest | life at three tempos: slow drift, 2-4 s accents, rare flicker |

Disable each effect in turn in QA; delete any with no named job. Verify with screenshots at 390, 768 and 1440 px that someone actually looks at ([shared-verification](shared-verification.md)).

## Traps

- Adjectives instead of constants ("premium", "cinematic") in the ledger.
- Starting from geometry before the concept-to-form sentence.
- Treating mobile as a crop of desktop.
- Effects added to rescue a weak material instead of fixing the material.
