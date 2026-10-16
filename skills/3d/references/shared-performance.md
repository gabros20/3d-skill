# Performance

Purpose: The canonical budgets by target, the frame-loop rules, and the hardening for adaptive quality; every other reference links here instead of restating numbers.

Read when:
- Choosing or recording budgets in `3D.md`, or setting `scripts/glb-report --budget`.
- A scene is slow, hot, janky on first frame, or memory grows.

Skip when:
- Deciding how to prove a number (→ [shared-verification](shared-verification.md)).
- Compressing a GLB (→ [asset-pipeline](asset-pipeline.md)).

Inputs:
- Target use (hero object, world, AR, render), target devices, a production build.

Produces:
- Budget numbers recorded in `3D.md`; a frame-loop and quality plan.

## Budgets

Starting contracts, not laws: no official three.js numbers exist. Pick by target, record in `3D.md`, document overruns with the reason. Sources disagree; defaults below are the reconciled choice, ranges show the spread.

| Target | Triangles | GLB | Textures | Draw calls |
|---|---|---|---|---|
| Hero object, desktop (default) | ≤ 100k (range 30k–150k) | ≤ 3 MB (range 1–5) | 1024; 2048 for a close-up hero | ≤ 300 |
| Hero object, mobile | ≤ 50k–100k | ≤ 2 MB | 1024, KTX2 where possible | ≤ 100 |
| World / scene, desktop | ≤ 750k | ≤ 15 MB total | ≤ 60 textures, ≤ 256 MB GPU | ≤ 300 |
| World / scene, mobile | ≤ 300k | ≤ 8 MB | ≤ 40 textures, ≤ 128 MB GPU | ≤ 150 (aim ≤ 100) |
| AR (Quick Look / Scene Viewer) | ≤ 100k | ≤ 5 MB | 1024 | few |
| Offline renders (stills, video) | unconstrained | n/a | any | n/a |

Also: shadow-casting lights ≤ 2 desktop / 1 mobile, shadow map ≤ 2048 / 1024; post passes ≤ 2 desktop / 0–1 mobile; idle GPU about 0 when nothing moves; frame budget 16.6 ms at 60 fps. Transparency overdraw and fullscreen passes, not triangles, are the usual mobile killers. A Blender triangle count becomes 1.5–3x engine vertices (seams, hard edges). Splat budgets: [splats-xr](splats-xr.md).

## Frame-loop discipline

1. One render loop. No allocations or `setState` in the hot path; reuse vectors.
2. `frameloop="demand"` (R3F) or render-on-change when the scene can rest; invalidate on scroll, input, animation.
3. Cap DPR: `min(devicePixelRatio, 2)` desktop, 1.5 or lower on phones; drei `AdaptiveDpr` / `PerformanceMonitor` for steps.
4. `matrixAutoUpdate = false` plus `updateMatrix()` for static objects; raycast a filtered list; `InstancedMesh` for 100+ identical meshes; merge only static, non-interactive geometry.
5. Time from `THREE.Timer`, clamp delta, `timer.connect(document)` so a hidden tab does not produce a giant step.
6. Pause when off-screen (IntersectionObserver) and when `document.hidden`.
7. Never animate material or light counts at runtime: new programs compile and stall.

## Triage order

Fix the scenario (route, viewport, DPR, state), measure p50/p95 and `renderer.info`, then toggle one at a time: lower DPR, disable post, freeze shadows, remove transparency and particles, hide groups, swap to a basic material. DPR win means fill, post or shadow; basic-material win means shader cost; group-visibility win means draw or geometry; no GPU win with high scripting means update, raycast or DOM.

## Adaptive quality (hardened)

1. One flat quality config (DPR scales, shadow on/off, post on/off, tier) that is also the debug API.
2. Sample a rolling window only AFTER the reveal; discard the first 2–3 windows.
3. Discard any window containing a frame over about 100 ms (a transition, not steady state).
4. Latch degradation one way. Cheapest lever first (DPR), then a tier drop; skip 1–2 windows after each step because the change itself hitches.
5. Escalate only if the cheap lever measurably failed.
6. Cache the tier classification (it flaps); suspend the monitor during benchmarks; start mobile Safari at DPR 1 with no MSAA-heavy post.

A simple "120 frames over 22 ms, degrade" rule produces false positives; use the hardened form.

## Preload and warm-up

Decode, upload and shader-compile before reveal so the first visible frame is not the first draw: [threejs-loading](threejs-loading.md).

## Mobile thermal

Sustained 60 fps at DPR 2 heats a phone within minutes and the OS throttles. Prefer 30 fps-capable scenes on phones, render on demand, drop post first, and test a 2-minute sustained run on a real device, not an emulator. iOS Low Power Mode throttles timers and video scrubbing: provide a still fallback.

## Traps

- Judging performance on the dev server or in headless software GL.
- Uncapped DPR on a 3x phone.
- Raising budgets silently instead of recording the overrun.
- Compiling shaders on first reveal.
