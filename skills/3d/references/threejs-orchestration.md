# Live Scene Behind an Entrance

Purpose: Start a live hero scene behind a page-load entrance without making the entrance jump or the scene lag: stages keyed to the entrance's own signal, a start budget, and a worker only where it earns its cost.

Read when:
- A live canvas sits behind a choreographed page-load entrance (headline set word by word, nav, buttons).
- "The headline jumps at the end", "the scene lags while the text comes in", a first-run stall near the reveal.

Skip when:
- The entrance itself (its timing, engine, promotion) → the `scroll-animation` skill, which owns the entrance clock.
- Scroll-driven scenes → [scroll-conductor](scroll-conductor.md).
- Steady-state frame cost → [shared-performance](shared-performance.md).

Inputs:
- Whether the page has a load entrance and who publishes its phase; the scene's prepare cost (chunk, compile, post chain).

Produces:
- Stage cues recorded in `3D.md`, a staged canvas, and a verdict on worker or main thread.

## Contents

- The signal · Stages · Start budget · Main-thread prepare · Worker (opt-in) · Validation · Traps

## The signal

The entrance's owner publishes its phase (the `scroll-animation` skill's `entrances.md` §11 owns the contract); this skill only reads it. Neither imports the other: the DOM is the interface.

- `data-entrance="pending | running | tail | settled"` on `<html>`, plus a bubbling `entrance:phase` event at each change; it only moves forward, and `tail` (display type within about 1 px of rest) may be skipped. No attribute means no entrance: the scene proceeds at once.
- Read it with `<skill>/assets/web/entrance-gate.ts`: `whenEntrance('tail' | 'settled', { timeoutMs: 2500 })` resolves `'phase'`, `'none'` or `'timeout'`. A fixed cue time survives only as that timeout, and the timeout counts from navigation start, not from the call: the entrance starts at first paint, the scene's code runs at hydration, hundreds of milliseconds later on a slow phone. A route's own entrance after a client-side navigation passes `since` (its mount).

## Stages

`SceneCanvas` with `startAfter="entrance"` runs them and writes `data-scene-stage`:

| Stage | Starts when | Does |
|---|---|---|
| prepare | main thread: before the entrance starts, else after `settled`; a worker: at once | the load (three, R3F, the `scene` chunk, into state: no Suspense hold), `compileAsync`, one warm render through the full post chain, the shader guard, a GPU fence ([threejs-loading](threejs-loading.md)) |
| reveal | prepared and proven, and `tail` or later (or the timeout) | one still frame fades in; a static layer costs the compositor almost nothing |
| run | `settled` (or the timeout), and revealed | the frameloop starts; an ambient scene's intro builds it up from empty, so the late start reads as choreography |

A failure in prepare (a shader, a load, a throw) never reaches `ready`; a later one drops `ready` to false and shows the poster. Either way `data-scene-mode="error"` and `onError`. Ambient scene or subject scene decides poster versus build-up reveal: [brief-approach](brief-approach.md).

## Start budget

The hero budget (compositor work only while `running`; costly starts one per task after `settled`; fonts, one tick, no blur over live media) is the `scroll-animation` skill's: `performance.md` §14. The scene's part: its run is first in the start queue, it caps at 60 fps on 120 Hz displays ([shared-performance](shared-performance.md)), and nothing blurs or blends over the canvas until `settled`.

## Main-thread prepare

Without a worker, prepare runs in slices so no task blocks the entrance's frames:

```ts
const yieldToMain = (): Promise<void> =>
  (globalThis as { scheduler?: { yield?: () => Promise<void> } }).scheduler?.yield?.() ??
  new Promise((resolve) => setTimeout(resolve, 0));
for (const build of steps) { build(); await yieldToMain(); } // geometry, noise textures, buffers
```

Use `scheduler.yield()` where it exists; the `setTimeout` path covers the rest. Skip `isInputPending` (superseded) and treat `requestIdleCallback` as missing in Safari. Compile and the warm render are single GPU-bound steps: schedule them before `running` or after `settled`, never between.

## Worker (opt-in)

Not the default, and never for R3F: `@react-three/offscreen` (0.0.8, May 2023) predates R3F 9. A worker scene is plain three: one runtime module that takes a canvas and a message port, so the same file runs on either thread.

- Earns its cost when per-frame CPU is above about 4 ms, the build cannot be chunked, or the main thread is busy by design. Otherwise the stages above are enough.
- **Never for a scroll-synced scene.** Worker frames present out of step with the page's, which breaks the conductor's frame-exact feed.
- Floor: Safari 17.0 (16.4–16.6 transfers the canvas but has no worker WebGL), Firefox 105. Probe `new OffscreenCanvas(1, 1).getContext('webgl2')` before `transferControlToOffscreen()`; a transferred canvas never gets a main-thread context, so the fallback replaces the element.
- The host forwards resize (`ResizeObserver`), pointer (coalesced, one message per frame), `run` and `dispose`; `IntersectionObserver` and `visibilitychange` decide `run`. Dispose posts `dispose`, then terminates after a grace period.
- Missing in a worker: video textures, drei `Html`, DOM controls. `GLTFLoader` works through `ImageBitmapLoader`; KTX2 and Draco spawn nested workers. three lives in the worker chunk only if the main thread never imports it.
- A worker frees the CPU, not the GPU: compile and composite still share the GPU process. Before blaming "GPU contention" for a laggy worker scene, re-measure with a compositor-only entrance and no blur over the canvas; main-thread back-pressure or a blurred nav fit the symptom too.

## Validation

- Phases arrive in order, and nothing costly starts before `settled` (Performance panel, or a log of `entrance:phase` beside the stage attribute).
- A forced shader error lands on the poster with `data-scene-mode="error"`, never `data-scene-ready="true"`.
- During `tail`, Long Animation Frames (`PerformanceObserver`, `long-animation-frame`, Chromium) or rAF deltas stay inside the frame budget; measure per [shared-performance](shared-performance.md) "Measuring".

## Traps

- Cue times copied from one machine (0.3 / 1.0 / 1.8 s): they encode that machine's compile time. Key to phases.
- A cue timer started at mount (hydration's clock), or a scene behind `React.lazy` / `next/dynamic`: each puts the reveal hundreds of ms late ([threejs-r3f-next](threejs-r3f-next.md) "Mount").
- Revealing at `tail` without the warm render: the post programs compile on the reveal frame.
- A worker for a scene that scroll drives.
