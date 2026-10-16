# Gaussian splats and XR/AR

Purpose: Ship Gaussian splat scenes with Spark and add WebXR or AR (Quick Look, model-viewer) without breaking device rules.

Read when:
- The brief has a captured real scene, a `.ply`/`.splat`/`.spz` file, or the word "splat" or "NeRF".
- The brief needs VR, AR, "view in your space" or a headset.

Skip when:
- The scene is meshes only (→ [threejs-loading](threejs-loading.md), [asset-pipeline](asset-pipeline.md)).
- A flat product viewer with no AR (→ [threejs-r3f-next](threejs-r3f-next.md)).

Inputs:
- Splat file(s) with format and size, or the target AR platforms; device tier; HTTPS availability.

Produces:
- A splat/XR integration decision with budgets in `3D.md` and a working embed.

## Gaussian splats (Spark)

Spark 2.x (`@sparkjsdev/spark`, MIT, World Labs) is the default library: three.js-native, WebGL2, streamed level-of-detail for very large scenes. `@mkkellogg/gaussian-splats-3d` is no longer developed; `gsplat.js` is a lighter alternative that lacks spherical harmonics in `.splat`.

1. Add `new SparkRenderer({ renderer })` to the scene once, then `new SplatMesh({ url })` per splat. Dispose via `SparkRenderer.dispose()` on unmount.
2. Formats: `.ply` (full precision, huge), `.splat` (compact, no SH), `.ksplat` (tool-specific), `.spz` (small, preferred for web), `.sog` (PlayCanvas), `.rad` (streamed LoD). Ship `.spz` or a pre-built LoD file; avoid raw `.ply` in production.
3. Clean, crop and compress in SuperSplat (PlayCanvas, MIT) before shipping: floaters and bounding noise cost sort time.
4. Starting budgets (practitioner figures, measure on device): phones 1-3M splats, desktop 1-20M, headset about 1M. Set `antialias:false` on the renderer. Prefer pre-built LoD over runtime LoD.
5. Splats have no physical shading or shadows; mix with meshes only when depth order is tested. Provide a poster image fallback.
6. R3F: use `extend({ SparkRenderer, SplatMesh })`. The official R3F/Next examples date from 2025-07 and pin Spark 0.1.x: re-verify against 2.x. Mark Spark modules `"use client"`. Spark's WASM `new URL()` is fragile under webpack (works under Vite/Turbopack): test the production build.
7. Capture (photos/video → splat) is done outside the web stack; ask which tool the user has and take the `.ply` from there. Untested here.

## WebXR

1. three: `renderer.xr.enabled = true`, `ARButton`/`VRButton` from addons, `renderer.setAnimationLoop` (not manual rAF). R3F: `@react-three/xr` 6.x: `createXRStore()`, `<XR store>` inside `<Canvas>`, `store.enterAR()`/`enterVR()` from a user gesture.
2. WebXR needs HTTPS (localhost counts) and a user gesture to start a session.
3. Real-world scale: 1 unit = 1 metre. A mug exported at 9.5 units is 9.5 m in AR. Check with `gltf-transform inspect`; fix at the source, never with CSS or scene scale hacks.
4. Safari on iOS has no WebXR `immersive-ar`. iOS AR is Quick Look with a USDZ.

## AR on the web (lowest effort)

Use `<model-viewer>` (`@google/model-viewer` 4.x, Apache-2.0) for a single product model:
```html
<model-viewer src="model.glb" ios-src="model.usdz" ar ar-modes="webxr scene-viewer quick-look"
  camera-controls alt="…"></model-viewer>
```
- Android: WebXR or Scene Viewer from the GLB. iOS: Quick Look from `ios-src`; users download both files.
- Serve `model/gltf-binary` for `.glb` and `model/vnd.usdz+zip` for `.usdz`; over HTTPS only. No AR button appears on desktop.
- Budget: AR GLB ≤ 5 MB (D6), textures ≤ 2048, basic PBR only (baseColor, normal, occlusion/roughness/metal).
- USDZ: prefer a Meshy `usdz` target, Reality Converter from a GLB, or OpenUSD `usdcat model.gltf -o model.usdc` then `usdzip`. Blender's USD export loses materials Quick Look cannot read. No automated validator is trusted: open it on a real iPhone and say when you could not.
- Render on demand so the idle GPU cost is about zero.

## Traps

- A headless screenshot of a splat or XR page proves nothing: GL may be absent (→ [shared-verification](shared-verification.md)).
- Splat sorting is camera-dependent: orbiting fast shows popping; cap DPR.
- Assuming WebXR works on iPhone, or that Quick Look reads a GLB.
