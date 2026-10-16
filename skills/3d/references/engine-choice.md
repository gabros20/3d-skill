# Engine Choice

Purpose: Decide whether the project builds on the default three.js stack or another web engine, and carry Babylon-specific notes when it does.

Read when:
- Approach is being chosen and the project, team or brief hints at Babylon.js, PlayCanvas, Needle, model-viewer, Spline, or "which engine".
- The project already uses Babylon (`@babylonjs/*` in `package.json`).

Skip when:
- A three.js or R3F project with no engine question (→ [threejs-renderer](threejs-renderer.md)).
- Spline-only work (→ [spline](spline.md)).

Inputs:
- Brief sections 2, 6, 11 and 12, `.3d/capabilities.md` (detected stack), team background if known.

Produces:
- One engine decision line in `3D.md` (engine, reason, rejected alternatives).

## Contents

- Gate · Decision table · Facts · If the project uses Babylon · Traps

## Gate

Default: **three.js + R3F + drei** (plain three without React). Switch only when a row below fires and the user agrees; an existing project keeps its engine. Recommend, never migrate unasked. Record the decision in `3D.md`.

## Decision table

| Situation | Recommend | Why |
|---|---|---|
| Marketing hero, one product, scroll story | three + R3F | smallest bundle; scroll libraries and this skill's helpers assume it |
| Rotate-and-swap viewer, AR Quick Look, no custom scene | model-viewer (+ USDZ for iOS) | no engine to maintain; limited look control |
| Heavy or game-like scene: many lights, physics, in-3D UI, XR-first | Babylon | clustered lighting, first-party Havok, GUI, built-in WebXR features |
| Team from game or C# background, wants tooling and a stable API | Babylon (or PlayCanvas) | Inspector and node editors; stated back-compat policy |
| Team of React/TS web developers, shader and post driven look | three + R3F | TSL/GLSL, `postprocessing`, drei |
| Long-lived product, few developers, upgrade pain matters | Babylon | fewer breaking changes per year than three's per-release churn |
| Exotic Blender 5 materials (`coat`, `fuzz`, `diffuse_transmission`, `volume_scatter`) | test the GLB in both; Babylon loads more of these | three's loader lacks them; Blender itself does not export `diffuse_transmission` |
| Designer owns the scene, few revisions | Spline | no engineering; accept runtime weight, plan cost and perf risk ([spline](spline.md)) |
| Unity or Blender artist authors interactions | Needle Engine | component workflow; still alpha 6.0 at last check |
| Cloud editor and collaborative scene authoring | PlayCanvas | editor-first workflow |
| Bundle budget is tight | three | see Facts |

Never recommend react-babylonjs: one maintainer, about 3,200 weekly downloads vs R3F's 6.2 million. Babylon in React means plain Babylon in a client component.

## Facts

Measured 2026-10-16 (one minimal scene, esbuild minified and tree-shaken, gzip): three box scene 134 KB, with `GLTFLoader` 157 KB; Babylon PBR scene 481 KB, with the glTF loader 868 KB. npm weekly downloads: three about 21.4 million, Babylon about 0.40 million. WebGPU is at parity: three has `WebGPURenderer` and TSL with automatic WebGL2 fallback, Babylon has WGSL core. All engines consume the same GLB, so the Blender pipeline does not decide the engine. Babylon's `.babylon` Blender exporter is frozen: use glTF only ([blender-export](blender-export.md)). Prefer the three/R3F corpus when an agent writes the code; with Babylon, give the exact import-path rules below.

## If the project uses Babylon

1. **Assets**: GLB through `@babylonjs/loaders`; apply the same compression and budgets as elsewhere ([asset-pipeline](asset-pipeline.md), [shared-performance](shared-performance.md)). Meshopt decoder injection is not supported in Babylon's docs; prefer the `EXT_` meshopt extension or Draco and test.
2. **Environment**: Blender equirect HDRs need `HDRCubeTexture.rotationY = Math.PI / 2` to match Blender. Set it on the skybox's `reflectionTexture` as well: `createDefaultSkybox` clones the texture. Use a cube `size` of 1024 or more for a visible background; 512 pixelates at narrow FOV. The rotation moves lighting too.
3. **Colour**: set `scene.imageProcessingConfiguration.toneMappingType` to `TONEMAPPING_KHR_PBR_NEUTRAL` for the Neutral intent in [design-lookdev-presets](design-lookdev-presets.md); exposure 1 as the start.
4. **Lights**: exported punctual lights take candela literally and nothing rescales for the HDR; export with COMPAT lighting mode ([blender-export](blender-export.md)) or hand-set intensities.
5. **Lightmaps**: bake Diffuse (no colour) in Cycles on a second UV, export the GLB, then assign the lightmap to each material in code; the GLB does not carry it.
6. **Inspector**: `@babylonjs/inspector` and the Sandbox are the second verifier: drop the GLB in, override materials, compare with the capture ([shared-verification](shared-verification.md)).
7. **Next App Router**: a `'use client'` component creates `Engine` and `Scene` in `useEffect`, calls `engine.dispose()` in the cleanup, loads Babylon with a dynamic import, and keeps the render loop outside React state. Import from deep paths (`@babylonjs/core/...`) plus the needed side-effect imports; `import { X } from '@babylonjs/core'` bloats the bundle 3-4×.
8. **CDN demos**: pin the version and use unpkg (`unpkg.com/babylonjs@<version>`); jsDelivr stalled on Babylon in testing. Self-host for production.

## Traps

- Recommending a switch because of a 2022 comparison; WebGPU and TypeScript gaps have closed.
- Counting Babylon's bundle as a deal-breaker for a heavy scene, or ignoring it for a hero.
- Promising Needle or R3F 10 as stable; both are alpha.
- Forgetting the skybox rotation, so reflections match but the background does not.
