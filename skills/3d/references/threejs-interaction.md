# three.js Interaction and Animation

Purpose: Add pointer picking, inspect and exploded views, camera controls, authored and procedural animation and (rarely) physics without fighting the render loop or the page's scroll.

Read when:
- Hover/click/drag on 3D objects, raycasting, orbit/transform controls, camera mode handoffs.
- Pick up and inspect an object; an exploded view; code-driven motion (springs, decay, posing).
- Playing a glTF animation clip, cross-fading states, or scrubbing a clip.
- Someone proposes physics for a marketing page.

Skip when:
- Scroll position drives the scene → [scroll-conductor](scroll-conductor.md).
- Authoring the clip in Blender → [blender-export](blender-export.md).

Inputs:
- Interactive objects list, clip names from `<skill>/scripts/glb-report` or `useAnimations`, touch targets.

Produces:
- Event wiring, one camera writer, a mixer owned by one component.

## Contents

- Picking · Inspect and pick-up · Exploded views · Controls · Animation · Procedural motion · Physics · Traps

## Picking

1. R3F raycasts only objects that have handlers. Events bubble by distance; `e.stopPropagation()` also blocks farther hits. Use `onPointerMissed` for deselect.
2. Heavy meshes: pick against a low-poly invisible proxy, a layer, or wrap in drei `<Bvh>` (three-mesh-bvh) instead of raycasting the hero.
3. Vanilla: one `Raycaster`, reused; `setFromCamera(ndc, camera)` with NDC from the canvas rect in CSS pixels, `(clientX - rect.left) / rect.width` (drawing-buffer size offsets picks at DPR ≠ 1); intersect a filtered array, `recursive=false` where possible; raycast once per frame, and not at all when the pointer is unchanged or nothing is available.
4. GPU-displaced or shader-deformed geometry does not match CPU bounds or raycasts; use a proxy.
5. Camera moving under a still pointer: call `state.events.update()` in `useFrame` only for those cases.
6. Touch: give tiny objects DOM buttons on mobile; a hit proxy follows the camera's rendered pose, not target state.
7. Cursor feedback via CSS `cursor` on the canvas wrapper, set from hover handlers.
8. Each interactive object runs `unavailable → idle ↔ hover/focus → active` through ONE setter shared by pointer and DOM focus; availability comes from exact progress, hidden or occluded proxies never take a hit; an open detail never blocks scroll and closes when progress leaves its range.
9. A pointerdown on an interactive object disables orbit until release, cancel or leave (else the camera turns mid-drag, or stays dead); a moving camera moves the drag plane.

## Inspect and pick-up

- Click and drag share one pointerdown: under 6 px and 600 ms opens, anything else is a drag and never opens. Tighter than DOM drag hysteresis (`frontend` `ui-motion.md` "Gestures and drag", ~10 px) because the canvas also orbits: a 6 px move already turns the camera, so the piece under the pointer has moved. Hover state comes from the last `pointerType`, not `(hover: hover)` (wrong on hybrid laptops and headless).
- Freeze camera lean on pointerdown and while inspecting; raycast again at pointerup.
- Lift by layer, not clone: room on layer 0, a dim full-screen quad, `clearDepth()`, then layer 1, with `autoClear = false`, `setClearColor` and no `scene.background` (it re-clears the second pass); lights need `layers.enable(1)` or the piece renders black. Draw both states once at load (first-click compile hitch); flag shadows `needsUpdate` when the piece leaves (ghost shadow).
- Interpolate the hand-off in camera space (x/z and y/z first, then depth) so it moves sideways at once; close runs on its own clock from the current eased value. Lean bounded and damped, zoom clamped around the fit distance (one demo: ±0.30 / ±0.09 rad, 0.70-1.45 of fit), pitch bounds that ease home.
- `touch-action: none` only while inspecting. A real button opens it; focus Close; Esc closes and returns focus; announce through a separate `role="status"` node. Reduced motion: an instant lift, direct manipulation kept.

## Exploded views

When the parts are the explanation: move real assemblies (not single meshes) along their real disassembly directions until each silhouette clears. One spring per assembly, just under critical (k 64, c ≈ 14), sub-stepped; starts staggered ~35 ms so nothing passes through anything (outermost first out, last back; threaded parts share a spring). A mid-way reversal reschedules only parts that have not left. Check every frame, including reversals at each stagger boundary; the selected assembly is the one lit accent.

## Controls

- One active control per camera. drei `OrbitControls makeDefault` lets `TransformControls` pause orbit. Dispose on teardown (`controls.dispose()`).
- Product viewer: clamp `minPolarAngle/maxPolarAngle`, `minDistance/maxDistance`, `enablePan={false}`, damping on; disable `enableZoom` when the page must keep scrolling (wheel capture breaks scroll).
- Controls fight scroll-driven cameras: do not enable both on one camera.
- One camera writer per frame: a small navigation state machine (intro, orbit, scroll, inspect) owns the camera; route samplers, orbit and transitions only request. A handoff lerps position and slerps orientation from one eased value, with no follow smoother on top (stacked smoothing stalls mid-move), and copies the target pose exactly at the end. Disable inactive controllers and their damping; save and restore route position on entering and leaving inspection. Interior to exterior goes through checked waypoints, a cut or a fade (a straight lerp crosses the roof).
- Derive camera distances from the subject's bounding radius, never one tuned number for assets of different scale. Huge distances: floating origin (camera at the origin, world offset), sky tethered to the camera.

## Animation

1. R3F: `const { actions, mixer } = useAnimations(gltf.animations, ref)`. Vanilla: one `AnimationMixer(root)`, `mixer.update(delta)` each frame with `Timer` delta.
2. Play: `action.reset().fadeIn(0.3).play()`; switch: `from.fadeOut(0.3); to.reset().fadeIn(0.3).play()`. `action.crossFadeTo(other, 0.3, true)` for warp-matched speed.
3. Loop modes: `LoopOnce` + `clampWhenFinished = true` to hold the last pose.
4. Scrubbing for scroll: `action.play(); action.paused = true;` once, then each frame `action.time = duration * progress; mixer.update(0)`; feed it already-smoothed progress, with no second damping layer (stacked smoothing reads soft).
5. Under `frameloop="demand"` keep calling `invalidate()` while a mixer is active.
6. Clone skinned scenes with `SkeletonUtils.clone` (`three/addons/utils/SkeletonUtils.js`), not `.clone()`.
7. Name clips in Blender; reference by name, not index.

## Procedural motion

- Elapsed seconds and `dt`, never frame counts. Per-frame decay or lerp (`v *= 0.98`, `lerp(a, b, 0.1)`) runs twice as fast at 120 Hz: use `a = 1 - exp(-λ * dt)`; to keep a value tuned at 60 Hz, `a = 1 - pow(1 - k, dt * 60)`. Clamp `dt` to 1/30, reset the time base on resume, check at 30, 60 and 120 fps.
- Named phase windows (`smoothstepRange(start, end, t)`), not one hidden 0-1. Analytic curves for authored travel, exponential response for perceptual values, a second-order spring (`damping = 2ζ√k`) only where inertia matters; at the end copy the terminal pose and zero velocity (spring residue). Shake is a bounded envelope apart from trajectory.
- Reparent with `Object3D.attach()` (keeps the world transform). Seeded random for replay; normalise accumulated quaternions; reset all state on replay.
- Pose an imported rig by direction, not Euler angles (each rigger's bone axes differ): rotate a bone so the segment to its child points along a world direction.

## Physics (only if the design needs it)

- `@react-three/rapier` 2.x with R3F 9. Keep simulation state outside render components, feed input to the step, fixed timestep. Rarely justified on marketing pages; a baked animation is cheaper and deterministic. Never ship physics for a one-off flourish.
- Fixed-step accumulator: cap elapsed time (~0.05 s), at most 2-5 steps per frame, drop the backlog; pause with a flag, never `dt = 0`; non-finite state resets and pauses before the next render; sleep after ~0.4 s under an RMS-velocity threshold (input wakes it) so the frameloop can rest.

## Traps

- Handlers on a parent group fire for every child; stop propagation at the mesh you mean.
- `onPointerMove` setting React state each event floods renders: write to refs or a store selector.
- Skeleton clones share the clip but not the mixer: one mixer per root.
