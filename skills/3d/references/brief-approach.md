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

- Decision rule · Matrix · Fallback ladder · Feasibility gate · Recreating a reference · Stages · Adjacent skills · Traps

## Decision rule

Pre-render when the viewer does not drive the camera or state AND device or weight risk is high. Build real-time when the viewer drives camera or state, when assets must react to brand or data, or when resolution independence matters. When both are plausible, state the ladder and start at the cheapest rung that meets the thesis.

## Matrix

Engine: default is three.js + R3F; run the engine gate in [engine-choice](engine-choice.md) when the project or team hints otherwise.

| Use | Strategy | Choose when | Read next |
|---|---|---|---|
| HERO live | Real-time three.js or R3F scene, compressed GLB, poster first | interactivity, brand-reactive, crisp at any size | [threejs-renderer](threejs-renderer.md), [threejs-r3f-next](threejs-r3f-next.md) (Next/React), [threejs-lookdev](threejs-lookdev.md), [threejs-loading](threejs-loading.md), [asset-pipeline](asset-pipeline.md) |
| HERO simple, VIDEO loop | Pre-rendered WebM/MP4 (or frame sequence) from Blender, poster image | no interaction, photoreal wanted, zero GPU risk | [blender-lookdev-render](blender-lookdev-render.md), [blender-channels](blender-channels.md), [shared-performance](shared-performance.md) (weight) |
| SCROLL world | Real-time scene driven by normalised scroll progress; camera path from `shots.json` | camera freedom, interactivity, copy synced to state | [scroll-conductor](scroll-conductor.md), [scroll-adapters](scroll-adapters.md), [threejs-r3f-next](threejs-r3f-next.md) or [threejs-renderer](threejs-renderer.md) |
| SCROLL scrub | Pre-rendered frames or keyframe-dense video scrubbed by progress | photoreal, no interaction, mobile risk | [blender-lookdev-render](blender-lookdev-render.md), [scroll-conductor](scroll-conductor.md), [scroll-adapters](scroll-adapters.md) |
| PROD stills, turntable | Offline Blender render, comp tweaks | highest fidelity, no runtime budget | [blender-lookdev-render](blender-lookdev-render.md), [blender-modeling](blender-modeling.md); in-browser path-traced stills (T18, refine-when-idle only inside a live-3D brief) in [realism-toolbox](realism-toolbox.md) |
| Spline | Spline scene or `@splinetool/react-spline` embed | designer-owned, non-engineer editable, fast prototype | [spline](spline.md) |
| SPLAT | Gaussian-splat viewer (capture, clean, compress) | a real place or object captured from photos or video | [splats-xr](splats-xr.md) |
| AR | GLB plus USDZ (Quick Look) or WebXR | try-in-space on phones | [splats-xr](splats-xr.md), [asset-pipeline](asset-pipeline.md) (AR budget in [shared-performance](shared-performance.md)) |
| GAME asset | glTF or engine-native handoff; engine work is out of scope | asset only | [blender-modeling](blender-modeling.md), [blender-export](blender-export.md), [asset-pipeline](asset-pipeline.md) |
| PRINT | Offline render at 300 dpi or more, 16-bit, ICC | fidelity | [blender-lookdev-render](blender-lookdev-render.md) |
| CAD part | CAD to mesh; printing or manufacturing handled elsewhere | physical part | [cad-print](cad-print.md) |

Always add: [design-art-direction](design-art-direction.md) for look decisions, [asset-acquire](asset-acquire.md) when geometry or textures must be sourced, [shared-verification](shared-verification.md) for the exit criteria.

## Fallback ladder

State it in the brief, top to bottom, and give the trigger for each step:

1. **Live** scene at full quality.
2. **Live, reduced**: lower DPR cap, no transmission or DOF, fewer lights, smaller textures. Trigger: frame time over budget on the device floor.
3. **Poster plus video**: pre-rendered clip or scrub frames from the same `shots.json`. Trigger: no WebGL, low-power mode, data saver.
4. **Static composition**: the poster from the first real frame. Trigger: `prefers-reduced-motion`, no JS, failed load.

Poster, reduced-motion frame and live first frame must match; the poster carries first paint.

## Feasibility gate

When the brief matches a reference or asks for realism, run the gate in [realism-gate](realism-gate.md) before building: it sets the achievable ceiling per category, the ship bar and the planned techniques, states them to the user, and writes `.3d/feasibility.json`. Re-run it when pipeline, target tier, dynamics or the reference changes. A stylised brief with no reference skips it.

## Recreating a reference

The brief's core is binding: no option or fallback may drop it. A live-3D brief ("recreate in three.js") requires live geometry and its motion; plates, stills and videos are not deliverables for it. Ask at intake for source stills or a clean plate (the reference without baked-in UI or animation) to measure from.

Live-3D directions (rebuild geometry, studio environment, lighting, texture, shadow, bloom, grain, GLSL, baked lighting) come from the direction menu in [realism-toolbox](realism-toolbox.md), chosen by the feasibility gate; change direction when lookdev plateaus (rule in [shared-verification](shared-verification.md)).

Light-only animation over a plate, 2D displacement warps, projection mapping and pre-rendered video ([scroll-video](scroll-video.md)) drop the live-3D core. Offer them only as a **brief change**, worded as one ("this changes the deliverable from live 3D to a plate"), and only after the user agrees. Projection mapping, where the brief allows it, goes only onto geometry that stays locked or moves less than the plate-to-geometry fit error; never project baked moving elements (the baked copy stays and the moving geometry doubles).

Rejected approaches: [SKILL.md](../SKILL.md) universal rule 7. Record each switch and its reason in the `3D.md` decision log.

## Stages

Brief → style frames or lookdev → greybox with cameras (`shots.json`) → asset prep (decimate, UV, bake, compress) → scene assembly → motion → light and post tuning → performance pass → verify against acceptance tests. Offline uses replace "performance pass" with the render and comp pass. Preview and iteration run after every stage that changes pixels ([shared-preview](shared-preview.md)).

## Adjacent skills

Recommend, never invoke: see the universal rules in [SKILL.md](../SKILL.md). Project rules (for example a motion doc) win over this reference.

## Traps

- Picking real-time because it is fashionable when the thesis needs no interaction.
- Choosing pre-render and then promising a pointer response.
- A ladder with no triggers; the fallback is never reached.
- Treating the poster as an afterthought; it is the LCP element.
