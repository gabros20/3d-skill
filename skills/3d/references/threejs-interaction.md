# three.js Interaction and Animation

Purpose: Add pointer picking, camera controls, authored animation playback and (rarely) physics without fighting the render loop or the page's scroll.

Read when:
- Hover/click/drag on 3D objects, raycasting, orbit/transform controls.
- Playing a glTF animation clip, cross-fading states, or scrubbing a clip.
- Someone proposes physics for a marketing page.

Skip when:
- Scroll position drives the scene → [scroll-conductor](scroll-conductor.md).
- Authoring the clip in Blender → [blender-export](blender-export.md).

Inputs:
- Interactive objects list, clip names from `scripts/glb-report` or `useAnimations`, touch targets.

Produces:
- Event wiring, one active control per camera, a mixer owned by one component.

## Picking

1. R3F raycasts only objects that have handlers. Events bubble by distance; `e.stopPropagation()` also blocks farther hits. Use `onPointerMissed` for deselect.
2. Heavy meshes: pick against a low-poly invisible proxy, a layer, or wrap in drei `<Bvh>` (three-mesh-bvh) instead of raycasting the hero.
3. Vanilla: one `Raycaster`, reused; `setFromCamera(ndc, camera)`; intersect a filtered array, `recursive=false` where possible; throttle pointermove to once per frame.
4. GPU-displaced or shader-deformed geometry does not match CPU bounds or raycasts; use a proxy.
5. Camera moving under a still pointer: call `state.events.update()` in `useFrame` only for those cases.
6. Touch: give tiny objects DOM buttons on mobile; a hit proxy follows the camera's rendered pose, not target state.
7. Cursor feedback via CSS `cursor` on the canvas wrapper, set from hover handlers.

## Controls

- One active control per camera. drei `OrbitControls makeDefault` lets `TransformControls` pause orbit. Dispose on teardown (`controls.dispose()`).
- Product viewer: clamp `minPolarAngle/maxPolarAngle`, `minDistance/maxDistance`, `enablePan={false}`, damping on; disable `enableZoom` when the page must keep scrolling (wheel capture breaks scroll).
- Controls fight scroll-driven cameras: do not enable both on one camera.

## Animation

1. R3F: `const { actions, mixer } = useAnimations(gltf.animations, ref)`. Vanilla: one `AnimationMixer(root)`, `mixer.update(delta)` each frame with `Timer` delta.
2. Play: `action.reset().fadeIn(0.3).play()`; switch: `from.fadeOut(0.3); to.reset().fadeIn(0.3).play()`. `action.crossFadeTo(other, 0.3, true)` for warp-matched speed.
3. Loop modes: `LoopOnce` + `clampWhenFinished = true` to hold the last pose.
4. Scrubbing for scroll: `action.play(); action.paused = true;` once, then each frame `action.time = duration * progress; mixer.update(0)`; feed it already-smoothed progress, with no second damping layer (stacked smoothing reads soft).
5. Under `frameloop="demand"` keep calling `invalidate()` while a mixer is active.
6. Clone skinned scenes with `SkeletonUtils.clone` (`three/addons/utils/SkeletonUtils.js`), not `.clone()`.
7. Name clips in Blender; reference by name, not index.

## Physics (only if the design needs it)

- `@react-three/rapier` 2.x with R3F 9. Keep simulation state outside render components, feed input to the step, fixed timestep. Rarely justified on marketing pages; a baked animation is cheaper and deterministic. Never ship physics for a one-off flourish.

## Traps

- Handlers on a parent group fire for every child; stop propagation at the mesh you mean.
- `onPointerMove` setting React state each event floods renders: write to refs or a store selector.
- Skeleton clones share the clip but not the mixer: one mixer per root.
