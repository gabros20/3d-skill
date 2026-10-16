# Recipes

Codex uses `$3d`; slash-command clients use `/3d`; others use a mention or natural language.

## Scene from a reference
```text
Use $3d to make a hero scene that looks like this screenshot [attach]. Measure it first and show me the brief.
```
Intake extracts palette, luma and camera language into `.3d/reference-spec.json`, then restates the brief for a yes.

## Scroll-driven 3D in an existing app
```text
/3d add a scroll-driven product reveal to /products in this Next app. Motion is our scroll library.
```
Uses the project's scroll owner; `3d` owns what is inside the pin.

## Black or washed-out render
```text
/3d my R3F scene renders black on load
```
Goes straight to the debug lane: symptom, confirming check, one change.

## Optimize a heavy GLB
```text
Use $3d to optimize hero.glb for mobile and report tris, draw calls, textures and size.
```
Explicit passes (never bare `optimize`), master kept, `glb-report` verdict.

## Blender product turntable
```text
/3d model a simple hard-surface speaker in Blender and render a 6 s turntable, then export a GLB.
```
Headless for export and render; MCP only if you want to watch.

## Export from Blender, materials flat in three.js
```text
/3d my Blender export looks flat in three.js
```
Checks export options and view transform before touching the scene.

## Brand colour renders wrong
```text
/3d our brand orange looks off in the web scene vs Blender
```
Picks one look-dev preset and one view transform (Khronos PBR Neutral for brand accuracy), recorded in `3D.md`.

## Custom shader
```text
/3d add a glassy refraction shader to the hero mesh, with a mobile fallback
```
GLSL on `WebGLRenderer` by default; TSL only when you need nodes or compute.

## Spline scene
```text
/3d our designer maintains this Spline scene; embed it in the page
```
Decides runtime vs GLB vs R3F, and says so if the Spline MCP is not connected.

## Review a version
```text
/3d here are my notes on v002 [paste]
```
Maps each note to the next version, captures shots, diffs against v002.
