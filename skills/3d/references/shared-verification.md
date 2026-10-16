# Verification

Purpose: Evidence-first checks so every "done", "matches" or "fast" claim is backed by something measured for exactly that claim.

Read when:
- About to say a shot matches the brief, a scene performs, or an asset passes.
- Interpreting `<skill>/scripts/preview diff`, `<skill>/scripts/glb-report` or a headless capture.

Skip when:
- Deciding the numbers themselves (→ [shared-performance](shared-performance.md)).
- Running the iterate loop (→ [shared-preview](shared-preview.md)).

Inputs:
- Evidence PNGs per shot, `<skill>/scripts/glb-report` output, the brief's shot list and budgets.

Produces:
- Claim-scoped verdicts (pass / fail / unmeasurable), a scorecard, and a sign-off line in `3D.md`.

## Claim-scoped verdicts

1. State each claim and its gate BEFORE looking: class (visual, temporal, performance, resource, lifecycle), the observable, the threshold.
2. A verdict covers only its claim. A good-looking still proves nothing about frame time or leaks.
3. Missing evidence is `unmeasurable`, never a pass. Say what would measure it.
4. Freeze what you can before comparing: three.js revision, renderer actually initialised, camera from the shot, fixed time step, viewport, DPR, asset version.

## Evidence per shot

- One PNG per shot per version in `.3d/evidence/vNNN/`, produced by `<skill>/scripts/preview capture`.
- Also capture a no-post baseline and a far and near view for hero objects, so post effects cannot hide geometry or material faults.
- Reject a capture that is all black, a constant colour, or from a context whose renderer string is missing.
- Scroll scenes: judge at progress values, not pixel offsets; test slow and fast scrub, reverse, and reload mid-scene.

## Spec gate

Before building or presenting, run `<skill>/scripts/spec-check` over `.3d/` (validates `refspec.v1`, `shots.v1`, `look.v1`; exit 1 lists bad field paths). Fix every listed path first; a malformed shot or look file makes captures meaningless.

## Visual diff

`<skill>/scripts/preview diff A B` (ffmpeg; images or version ids) prints `ssim` (0 to 1, structure) and `psnr_db` (pixel error; `null` plus `identical:true` when equal) and writes side-by-side, blend and difference images under `.3d/diffs/A__B/`. Add `--edges` to compare edge maps only (structure and geometry fit, independent of lighting).

| Reading | Meaning |
|---|---|
| ssim ≥ 0.98 or psnr > 40 dB | effectively unchanged: a regression check passes |
| ssim 0.90–0.98 or psnr 30–40 dB | visible local change: confirm it is the intended one |
| ssim < 0.90 or psnr < 30 dB | large change; expected only for a deliberate redo |

These are heuristics, not gates. Compare only same machine, same flags, version to version: GPU and driver differences make cross-machine pixel baselines meaningless. Never gate on pixel equality.

Against a reference photo or render, ssim says little (different pipeline, different pixels). Compare palette and luma instead (`.3d/refs/<name>/palette.json`, `luma.json` from `<skill>/scripts/ref-extract`) plus a side-by-side or overlay, and let the user judge.

For scroll-video seams, ssim between one clip's last frame and the next clip's first: ≥ 0.90 pass, < 0.75 regenerate (source: auteur, see [SOURCES](SOURCES.md)).

## Assets

`<skill>/scripts/glb-report FILE --budget hero|world|ar|none [--target desktop|mobile] [--json]` lists meshes, triangles, draw-call estimate, materials, texture dimensions and formats, extensions and size, and returns PASS / WARN / FAIL against the budgets in [shared-performance](shared-performance.md); exit 1 on FAIL. `--target mobile` tightens bytes and draw calls (and world triangles). Triangles, size and the texture ceiling can FAIL; draw calls only WARN (advisory); any metric above 80% of its limit WARNs. Sizes are MiB. Re-run after every compression step; a size win that loses node names or animation targets is a failure. Spec conformance: `gltf-validator` when installed.

## What headless numbers can and cannot prove

- Can prove: draw calls, triangles, geometries, textures, programs (`renderer.info`), console errors, layout and progress mapping, that frame N looks as intended.
- Cannot prove: real fps, GPU time, thermal behaviour, Safari or iOS rendering. A headless fps is a floor, never a verdict (software GL can run several times slower).
- A performance claim needs: a production build, DPR 2, a named viewport, a warm-up, p50 and p95 frame time, on the named target. The dev server costs roughly 2x per frame.
- Fullscreen passes (bloom, DoF, grain) scale with pixels, so test them at DPR 2.

## Scorecard (0–3 each; score the real page state, not a showroom)

Composition and hierarchy · lighting · materials · colour and tone · motion and timing · performance evidence · fidelity to the refspec.

Ship when every category reaches its ship bar and the average reaches the average bar in `.3d/feasibility.json` (default `min(2, ceiling)` per category and `min(2.3, mean ceiling - 0.2)`; set at the feasibility gate, [realism-gate](realism-gate.md)). Without a feasibility file: every category ≥ 2 and average ≥ 2.3. Automatic fail: core violation in a live-3D brief (reference pixels as colour or lighting, 2D warps for 3D motion), placeholder primitive plus glow, bloom or fog standing in for geometry, one flat grey, text over 3D unreadable, no evidence image for a claimed shot, no renderer diagnostics for a performance claim.

## Fresh-critic gate

Validation passing is not visual verification: render after every stage and look at it.

0. Numbers before images. Run `<skill>/scripts/preview match --version vNNN --json` first (ssim, edge-ssim, mask IoU, region luma and delta E against refspec tolerances, a verdict per channel). For motion, record `preview capture --clip SECONDS`, run `<skill>/scripts/ref-extract --motion-json` (with `--regions N --kymo`) on the clip and on the reference, and compare speed, period and amplitude. These numbers go to the critic as evidence; it does not re-estimate them. At most 4 image views per iteration, and never view the same path twice.
1. From round 1, every round the critic gets the SAME anchored rubric and the same reference frames, with per-category pass criteria derived from refspec measurements (e.g. motion period ±10 %, pulse speed ±15 %, sway amplitude ±15 %, luma p5/p50/p95 ±0.05), so verdicts do not contradict across rounds. After each iteration, hand the evidence PNGs, the measured numbers, the brief and the refspec to a FRESH reviewer context (a new subagent or a clean pass) that is NEVER told what was just fixed or which notes were addressed.
2. It lists defects, each labelled FIXABLE(T#) / CEILING(G#) / ARTEFACT(R#) ([realism-gate](realism-gate.md)), and a scorecard; you fix only what it confirms against evidence.
3. Record each round in the `3D.md` version log (round, critic verdict, defects found, fixed).
4. A failing critic round is fixed as a NEW version and re-captured; only a version whose critic round passes is shown to the user.
5. Stop and continue are decided by `<skill>/scripts/preview rounds`, not by you: caps, plateau, ceiling and the MAX REACHED report are in [realism-gate](realism-gate.md). Never loop silently.
6. Iterate at low resolution (`--size 854x480`); judge the approval candidate at full resolution.

## Sign-off

One `3D.md` line: version, shots checked, metrics with their conditions, known defects, decision. Repeat when three.js version, renderer backend, camera, tier or the asset changes.

## Traps

- Declaring a perf pass from a dev-server headless run.
- Using ssim to prove fidelity to a different-pipeline reference.
- Letting a post effect mask a geometry or material fault.
