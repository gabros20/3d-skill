# TSL and Node Materials

Purpose: Use three Shading Language for WebGPU-backed scenes (node materials, compute, render pipeline) and decide when not to.

Read when:
- The brief needs compute (GPU particles, simulation), node materials, or `RenderPipeline` effects.
- Old TSL code from 2024–25 posts breaks on r186.

Skip when:
- Default WebGL scene → [shader-glsl](shader-glsl.md) or built-in materials.
- Post effects on WebGL → [threejs-postfx](threejs-postfx.md).

Inputs:
- Pinned `three` version, target browsers (check WebGPU availability, especially iOS Safari and Linux Firefox), fallback plan.

Produces:
- Node graphs built once, a verified WebGL2 fallback, a pinned three version.

## When NOT to use TSL

- The effect is a built-in property or a small `onBeforeCompile` patch.
- Needs drei or `@react-three/postprocessing` (WebGL-only on drei 10 / wrapper 3).
- The team cannot re-test every three bump: TSL has no stability guarantee.
- A design that only needs one custom shader on a marketing hero: GLSL on WebGL is cheaper to maintain.

## Setup

```ts
import * as THREE from 'three/webgpu';
import { Fn, uniform, uv, time, mix, vec3, positionLocal, sin } from 'three/tsl';
const renderer = new THREE.WebGPURenderer({ canvas });
await renderer.init();              // before first render() / compute()
```

R3F 9: async `gl` factory that awaits `init()`, plus `extend(THREE)` from `three/webgpu`. Mixing class identities from `three` and `three/webgpu` is a risk: import everything from `three/webgpu` in WebGPU modules.

## Node materials

1. Use `MeshStandardNodeMaterial` etc. Express changes as nodes: `material.colorNode`, `positionNode`, `emissiveNode`, `opacityNode`.
2. Build graphs once (`useMemo`/module scope). Update `uniform(...)` nodes' `.value` per frame; never rebuild the graph per frame.
3. Wrap reusable logic in `Fn(([a, b]) => ...)`.
4. Mutation: a JS reassignment of a node (`v = v.add(1)`) is not tracked. Use `.toVar()` then `.assign()`, `select()`, and capital `If(...)`.
5. Skinned meshes: `positionGeometry` is the untransformed attribute; `positionLocal` no longer reflects skinning (r185). Pick per intent.

## Compute

1. `await renderer.init()` first, then `renderer.compute(node)` (sync) each frame or once. `computeAsync` still works but is deprecated; resolution means submission, not GPU completion.
2. Storage: `instancedArray(count, 'vec3')` buffers; dispatch size from the node's `.compute(count)`.
3. Read back only for verification (`getArrayBufferAsync`); never per frame.
4. Device loss: listen to `device.lost`, rebuild GPU content from source.
5. GPU timing needs `trackTimestamp: true` at construction.

## Fallback behaviour

- WebGPURenderer falls back to WebGL2 backend automatically; node materials still work, compute features may be absent or slower. Verify the fallback separately with `forceWebGL: true`.
- Where WebGPU/WebGL2 are both unavailable show the static fallback (poster), see [threejs-r3f-next](threejs-r3f-next.md).
- Verify on the real backend: read `renderer.backend.isWebGPUBackend` and record it in evidence ([shared-verification](shared-verification.md)).

## Version drift (r168–r186 samples)

Chaining removed r168; `varying()` → `toVarying()`, `vertexStage()` → `toVertexStage()` r173; `PI2` → `TWO_PI` r181; `directionToColor` → `packNormalToRGB` r185; `TiledLighting` → `ClusteredLighting` r185; `AnamorphicNode` → `BloomNode` r185; `resolution` → `resolutionScale` on several nodes; `PostProcessing` → `RenderPipeline` r183. Treat any TSL snippet older than r185 as suspect: check the installed source or migration guide before use.

## Traps

- No `ShaderMaterial`, `onBeforeCompile` or drei shader materials on WebGPU.
- Type-checking proves nothing about GPU compatibility; render on both backends.
- Blank canvas with no error is almost always a missing `await renderer.init()`.
