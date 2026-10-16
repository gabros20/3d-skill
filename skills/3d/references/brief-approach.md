# Brief Approach

Purpose: Map a target use to a pipeline, a fallback ladder and the area references to read next.

Read when:
- The brief is approved (or assumptions recorded) and you must choose how to build it.
- A build is failing on budget or device risk and the strategy may need to change.

Skip when:
- The pipeline is already recorded in `3D.md` and still fits.
- Requirements are unclear (→ [intake-grill](intake-grill.md)).

Inputs:
- Brief sections 2, 3, 6, 11; `.3d/capabilities.md`; budgets.

Produces:
- The brief's Pipeline section: strategy, stages, fallback ladder, next references; recorded in `3D.md`.

## Contents

- Decision rule · Matrix · Fallback ladder · Stages · Adjacent skills · Traps

## Decision rule

Pre-render when the viewer does not drive the camera or state AND device or weight risk is high. Build real-time when the viewer drives camera or state, when assets must react to brand or data, or when resolution independence matters. When both are plausible, state the ladder and start at the cheapest rung that meets the thesis.

## Matrix

| Use | Strategy | Choose when | Read next |
|---|---|---|---|
| HERO live | Real-time three.js or R3F scene, compressed GLB, poster first | interactivity, brand-reactive, crisp at any size | `threejs-renderer.md`, `threejs-r3f-next.md` (Next/React), `threejs-lookdev.md`, `threejs-loading.md`, `asset-pipeline.md` |
| HERO simple, VIDEO loop | Pre-rendered WebM/MP4 (or frame sequence) from Blender, poster image | no interaction, photoreal wanted, zero GPU risk | `blender-lookdev-render.md`, `blender-channels.md`, `shared-performance.md` (weight) |
| SCROLL world | Real-time scene driven by normalised scroll progress; camera path from `shots.json` | camera freedom, interactivity, copy synced to state | `scroll-conductor.md`, `scroll-adapters.md`, `threejs-r3f-next.md` or `threejs-renderer.md` |
| SCROLL scrub | Pre-rendered frames or keyframe-dense video scrubbed by progress | photoreal, no interaction, mobile risk | `blender-lookdev-render.md`, `scroll-conductor.md`, `scroll-adapters.md` |
| PROD stills, turntable | Offline Blender render, comp tweaks | highest fidelity, no runtime budget | `blender-lookdev-render.md`, `blender-modeling.md` |
| Spline | Spline scene or `@splinetool/react-spline` embed | designer-owned, non-engineer editable, fast prototype | `spline.md` |
| SPLAT | Gaussian-splat viewer (capture, clean, compress) | a real place or object captured from photos or video | `splats-xr.md` |
| AR | GLB plus USDZ (Quick Look) or WebXR | try-in-space on phones | `splats-xr.md`, `asset-pipeline.md` (AR budget in [shared-performance](shared-performance.md)) |
| GAME asset | glTF or engine-native handoff; engine work is out of scope | asset only | `blender-modeling.md`, `blender-export.md`, `asset-pipeline.md` |
| PRINT | Offline render at 300 dpi or more, 16-bit, ICC | fidelity | `blender-lookdev-render.md` |
| CAD part | CAD to mesh; printing or manufacturing handled elsewhere | physical part | `cad-print.md` |

Always add: `design-art-direction.md` for look decisions, `asset-acquire.md` when geometry or textures must be sourced, [shared-verification](shared-verification.md) for the exit criteria.

## Fallback ladder

State it in the brief, top to bottom, and give the trigger for each step:

1. **Live** scene at full quality.
2. **Live, reduced**: lower DPR cap, no transmission or DOF, fewer lights, smaller textures. Trigger: frame time over budget on the device floor.
3. **Poster plus video**: pre-rendered clip or scrub frames from the same `shots.json`. Trigger: no WebGL, low-power mode, data saver.
4. **Static composition**: the poster from the first real frame. Trigger: `prefers-reduced-motion`, no JS, failed load.

Poster, reduced-motion frame and live first frame must match; the poster carries first paint.

## Stages

Brief → style frames or lookdev → greybox with cameras (`shots.json`) → asset prep (decimate, UV, bake, compress) → scene assembly → motion → light and post tuning → performance pass → verify against acceptance tests. Offline uses replace "performance pass" with the render and comp pass. Preview and iteration run after every stage that changes pixels ([shared-preview](shared-preview.md)).

## Adjacent skills

Recommend, never invoke, and work without them: `scroll-animation` when installed owns scroll authority, pin and reduced-motion collapse; `manufacturing-workflow` for CAD to print; `generate-image` and `generate-video` for stills and clips; `fluid-design` for viewport-fluid layout around the canvas. Project rules (for example a motion doc) win over this reference.

## Traps

- Picking real-time because it is fashionable when the thesis needs no interaction.
- Choosing pre-render and then promising a pointer response.
- A ladder with no triggers; the fallback is never reached.
- Treating the poster as an afterthought; it is the LCP element.
