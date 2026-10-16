# Realism gate

Purpose: Decide before building how close live three.js can get to a reference, label every critic defect, and stop the loop deterministically with a "MAX REACHED" report instead of retrying.

Read when:
- The brief matches or styles a reference (photo, Cycles render, AI image or video) or the user asks for realism: run the feasibility gate.
- A critic round returns defects, scores stall, or the user says "keep going" / "still not right".
- A defect needs a label, or a CEILING claim needs a twin.

Skip when:
- Stylised brief with no reference (→ [brief-approach](brief-approach.md)).
- Choosing a technique (→ [realism-toolbox](realism-toolbox.md)); judging a feature's tier (→ [realism-gap](realism-gap.md)).
- Generic evidence rules (→ [shared-verification](shared-verification.md)).

Inputs:
- `.3d/reference-spec.json` (with `provenance`), the brief's pipeline and target, `.3d/rounds.jsonl`.

Produces:
- `.3d/feasibility.json` (`feasibility.v1`), a user statement, per-round `rounds.v1` lines, a `preview rounds` verdict, and on stop a MAX REACHED report.

## Feasibility gate

One table pass over the refspec; no renders. Re-run when pipeline, target tier, dynamics or the reference changes.

1. Provenance: read `refspec.provenance` (`kind`, `consistency`). AI image or video is an art-direction target, not physical truth; a failed consistency check becomes an artefact cap (R1–R4).
2. Classify each refspec feature into a G id and tier for this pipeline, dynamics and target ([realism-gap](realism-gap.md)).
3. Ceiling per category (composition, lighting, materials, colour/tone, motion, fidelity) by the caps in realism-gap.
4. Bars (D46): per category `min(2, ceiling)`; average `min(2.3, mean(ceilings) - 0.2)`. The user may raise them.
5. Planned techniques: for every LIVE-WITH-TECHNIQUE or BAKE-ONLY feature, the T id that closes it, in toolbox rank order. This is the build order.
6. Statement to the user, at most 150 words, with the approach yes: reference kind and how it is treated, expected ceiling per category, offline-only features by G id, planned T ids, ship bar, iteration budget (default 3 critic rounds per gate, at most 2 versions per technique; adjustable at intake). If a must-have sits above the ceiling, say so and offer, inside the core, the pipeline with the higher ceiling (baked lighting if static, path-traced idle refine) or a brief change worded as a change.
7. Write `.3d/feasibility.json`: `{schema:"feasibility.v1", pipeline, dynamics, target, provenance, features[{g,category,visibility,tier,technique}], ceiling{}, reference_target{}, ship_bar{}, budget{rounds}, accepted}`. Validate with `<skill>/scripts/spec-check`. Add one decision line to `3D.md`. No build before `accepted: true`.

The critic scores against the reference anchors; the stop rules judge against `ship_bar`.

## Defect labels

The fresh critic ([shared-verification](shared-verification.md)) stays blind to what was fixed. It receives the realism-gap feature table, the technique id list and `feasibility.json`. Every defect gets exactly one label:

- `FIXABLE(T#)`: names a technique (or `fit:<param>` for a measured fit such as camera or timing), a `gain` (0.5 or 1) and a category.
- `CEILING(G#)`: valid only if that G is OFFLINE-ONLY for this pipeline (or BAKE-ONLY on a dynamic brief) AND no untried T id closes it. A defect visible in the twin is a design defect, never CEILING.
- `ARTEFACT(R#)`: the reference itself is inconsistent; needs the provenance result or a named frame pair.

Spend rounds only on FIXABLE items, highest gain first, one change-set per version. Name it: `<skill>/scripts/preview new-version --technique T1,T8 --note "…"`. Tried-status is computed from version manifests, never told to the critic. The builder may contest a CEILING label once, only with twin evidence; without a twin it stays FIXABLE. Append one `rounds.v1` line per round to `.3d/rounds.jsonl`: `{schema, round, version, scores{}, avg, defects[{id,category,label,technique|feature|ref,gain,note}], twin?}`.

Core integrity is an automatic fail in a live-3D brief: reference pixels used as colour or lighting (plate, projection, reference frame as texture), 2D warps standing in for 3D motion, overlays, fog or glow standing in for geometry. Allowed: tileable roughness/normal detail derived from a reference crop (D50).

## Twin

Design gap = reference vs a path-traced render of our scene. Real-time gap = that render vs the live one (same scene, same camera; `preview diff` is meaningful here, unlike against the reference).

Run only to confirm a CEILING claim not already tiered OFFLINE-ONLY, or once at the first look-dev round for a photo/offline-render reference. At most 2 per project, 2 shots each, 854x480.
- Primary: `<skill>/scripts/preview capture --pathtrace [--samples 256] [--shot ID]` (WebGPU; exits 1 with a message when unavailable; `--headed` if headless lacks WebGPU) writes `<shot>_pt.png`.
- Fallback: Blender Cycles through `render_shots.py` with an imported GLB ([blender-lookdev-render](blender-lookdev-render.md)); light units differ, compare structure not exposure.

## Stop rules

After every critic round run `<skill>/scripts/preview rounds [--json]`. It reads `feasibility.json`, `rounds.jsonl` and manifests and prints `continue | pass | stop` with the rule. Obey it; "iterate until it passes" never overrides it.

- S0 pass: every category at its bar and the average at its bar. Present to the user.
- S1 nothing fixable: every open defect in a failing category is CEILING, ARTEFACT or tried-out.
- S2 plateau: in the last 2 rounds no failing category rose and the average gained < 0.15.
- S3 diminishing returns: every open FIXABLE item has gain < 0.5, or needs a pipeline or brief change. That is the user's decision.
- S4 budget: rounds used = `budget.rounds` (3 per gate), or the user's token cap.
- Per-technique cap: a T id applied in 2 versions without its category rising is tried-out.
- Best-so-far: if the latest average < best - 0.15, present the best version, not the last.

## MAX REACHED report

On S1–S4, write this (at most 400 tokens), then end the turn. Start no new round.

```
MAX REACHED: best vNNN (round N), rule S#
Evidence: board, twin (if run)
Scores vs bar: <category score/bar> … avg x (bar y)
Ceiling-bound: G# …   Artefacts: R# …   Tried without gain: T# …
Directions inside the brief (live 3D), best first, untried only:
 1 <lever> - T#: what changes; category +gain; runtime cost; effort
 … (3 to 6 items)
Changes the brief (only if you want it): B1 pre-rendered video · B2 plate + live light · B3 path-traced clip
Reply: a number, "accept vNNN", or "change the brief"
```

Menu items map user words (lighting, texture, colour, shadow, highlights, bloom, noise, GLSL, baked lighting, path-traced stills) to ids via [realism-toolbox](realism-toolbox.md). Brief changes are listed apart and never numbered. A chosen item opens a bounded extension: `budget.rounds += 2` with a stated gain target; S2 applies again. A rejected approach rejects its whole family ([shared-preview](shared-preview.md)).

## Traps

- Calling a LIVE-NATIVE gap (G3, G4, G12) a limit. Try T1, T2, T3, T4 before any CEILING claim.
- Bloom, fog or glow to hide a material gap.
- Treating the best version as the last one.
