# Scroll Conductor

Purpose: Turn one scroll value into the state a 3D scene reads (camera, world, assets), and split ownership cleanly with the `scroll-animation` skill.

Read when:
- A 3D scene must move with scroll: camera path, chapters, "pinned 3D", scrub, "world", scroll-linked uniforms.
- Choosing whether the scene should be real-time at all.

Skip when:
- Wiring Motion, GSAP, Lenis or native to the conductor, or pin and iOS issues → [scroll-adapters](scroll-adapters.md).
- Deciding what the chapters should show → [design-art-direction](design-art-direction.md).
- "Pin holds frame one, then snaps": stale stylesheet first → [shared-debug](shared-debug.md).

Inputs:
- The scene ledger (chapters, weights, camera, world state) from the brief; the page's scroll authority.

Produces:
- One conductor feeding the scene, a camera path keyed by chapter, a reduced-motion/poster plan.

## Ask first

Fixed camera move, nothing the reader can interact with or that reacts to the page? A rendered image sequence or scrub video beats a live world: exact at any scroll speed, no GPU risk. That is the `scroll-animation` skill's lane (`sequences`, scrub video). Go real-time only when geometry must stay spatial, interactive or data-driven. Never disguise a video as three.js.

## Shape

```
scroll authority -> adapter -> exact -> conductor -> { exact, smooth, position, index, direction, reduced } -> camera / world / DOM
```

Copy-and-own: `assets/web/conductor.ts` (`createConductor`, `bindReducedMotion`, `startRafClock`) plus one adapter. Never rewrite it from memory.

## Rules

1. **Native scroll is the only source of truth.** One authority per route. Never integrate wheel delta into a story position: same position must give the same state forward, backward, after a flick, a jump, a reload.
2. **Two numbers.** `exact` drives logic (nav, `aria-current`, gating, analytics, hover availability); `smooth` drives visuals only. A damped value never feeds a threshold: it settles across it and flips.
3. **Smooth once.** The conductor damps with `damp(cur, target, lambda, dt)`, lambda 4.5-7, `dt` clamped to 1/30. Under Lenis or ScrollSmoother create it with `damping: null`. Never `lerp(a, b, 0.1)` per frame, never `scrub: 1` plus a lerp.
4. **Chapters are waypoints.** `position` is a fractional chapter index (2.35). `weight` on chapter i is the scroll share of the leg i to i+1. Progress per viewport is `1/(N-1)`: three one-viewport acts land at halves, so pace with weights or an empty spacer act.
5. **Resolve once per frame**, from `conductor.segment()` (`a`, `b`, `t`; `t` is dwell-shaped so beats rest). Interpolate every channel the ledger declares: light key, fog, emissive, grade.
6. **Camera path.** `CatmullRomCurve3` for position and a separate curve for look-at targets; never `lookAt` your own position. `curve.getPoint(position / (N - 1))` passes through control point k exactly at chapter k (`getPointAt` is arc-length and does not). Quaternion `slerp` only for deliberate roll; never Euler-lerp. Hide unavoidable seams behind occlusion, dark or fog; never teleport in open space.

```ts
const u = conductor.state.smoothPosition / (chapters.length - 1)   // visuals read smooth
camCurve.getPoint(u, camera.position)
lookCurve.getPoint(u, target)
camera.lookAt(target)
```
7. **Responsive.** Author endpoints per breakpoint and rebuild the curves on width or orientation change; never blend a desktop curve into a mobile one. Mobile is a second composition (pull back, own copy zones). Frame by viewport height. Ignore height-only resizes on touch.
8. **Pointer parallax** lives in a child `inputRig` of the path rig, clamped, damped, faded out near transitions; never in waypoint data.
9. **Discrete states change per transition**: `conductor.onChapter` (hysteresis built in), not per frame.
10. **Frame order**: read input, `conductor.tick(dt)`, resolve camera + world, mixers/sims, DOM proxies, render, sample perf. One clock: `ConductorDriver` in R3F, `driveFromGsapTicker` on GSAP pages, `startRafClock` otherwise.
11. **Assets stream by chapter.** Prefetch window `round(position) + direction x {0,1,2}`; keep the previous chapter resident until reverse scroll is safe; report progress by required bytes. Loaders and decoders: [threejs-loading](threejs-loading.md).
12. **Pause and resume**: pause render off-screen (wide warm margin) and on `document.hidden`; `conductor.settle()` on mount, bfcache restore and resume so a reload mid-page does not glide from zero.

## Reduced motion and poster

- Alternate scene, not removal: pin collapses (scroll authority), copy reads as normal DOM, canvas shows the poster. Check the query and WebGL once, render the poster, never load the 3D bundle (`assets/web/r3f/SceneCanvas.tsx` does this).
- Live toggle: `bindReducedMotion(conductor)` snaps to the nearest composed chapter and stops damping.
- The poster is the LCP element: server-rendered, sized, designed. Context loss: `preventDefault`, show the poster, rebuild from retained sources, re-apply `exact`.
- DOM carries meaning: real headings, copy readable with the canvas hidden, 44 px DOM proxies for hotspots. Ambient WebGL longer than 5 s needs a pause control.

## Ownership with `scroll-animation`

Recommend it when installed; never invoke it. Without it, apply the pin rule in [scroll-adapters](scroll-adapters.md). Project rules (a MOTION doc) win over both.

| `scroll-animation` owns | `3d` owns |
|---|---|
| Scroll authority per route, Lenis/ScrollSmoother, one tick | The conductor contract and the adapter that feeds it from that authority |
| Range wrapper, sticky `lvh` pin, acts, holds, `inert` | What is inside the pin: renderer, camera path, world-state channels |
| Reduced-motion collapse of the pin, live query, pause controls | Poster/no-WebGL alternate for the canvas; skipping the 3D bundle |
| `ANIMATION.md` scene ledger | World bible + chapter ledger; link one row of `ANIMATION.md` to it |
| Motion verification, stale-stylesheet check, device discipline | Frame QA, perf (calls, triangles, ms), asset checks ([shared-verification](shared-verification.md)) |
| Image-sequence and scrub-video scenes | Real-time 3D only |

## Traps

- Smoothing twice (Lenis plus conductor damping, or `scrub: 1` plus lerp): the scene trails scroll by about 0.3 s.
- Reading scroll or rects inside the render tick; adapters read, the tick never does.
- Euler-lerp or `lookAt` of the camera's own position: flips and swims.
- Keying chapters by `getPointAt`: waypoints drift off their chapters.
- Marking a chapter without a nameable landmark, change and camera: six dolly-ins at one centre are one scene.
