# Recipes

Copy-paste starting points. Each is one request; no flags are needed. The loop runs the same way
underneath ([loop.md](loop.md)): references are measured, only the gaps are asked, nothing is built
before your yes, and every version is captured and reviewed. For what each stage writes see
[loop.md](loop.md#the-3d-layout); for which reference a request reads see [areas.md](areas.md).

The examples use `/3d` as shorthand. Use `$3d` in Codex, or the form your client provides.

## Build from references

### Scene from a reference image
```text
Use $3d to make a hero scene that looks like this screenshot [attach]. Measure it first and show me the brief.
```
**What happens**: `ref-extract` and vision passes write `.3d/reference-spec.json` with ranges,
confidence and a hidden-or-unknown list; intake asks one intent question (match or style), then only
the open gaps; the turn ends on a restated brief for your yes.
**Reach for it when**: you can show the look but not describe it.

### Match a camera move from a video
```text
/3d recreate the camera move in this clip [attach] for a 3D product section. Tell me what you measured vs what you guessed.
```
**What happens**: `ref-extract` adds `cuts.json` and `motion.json`; the refspec `video` block records
move type, direction, amount and a sampled easing curve; the shots seed `.3d/shots.json`. Anything
the clip cannot show stays a range tagged `inferred`.

### Vague brief, no reference
```text
/3d I need a 3D hero for the homepage. I have no idea what it should look like.
```
**What happens**: after at most two rounds, the open look becomes three labelled directions (three
looks on a greybox of the subject) and you answer "A, B or C plus one change". If `generate-image` is
installed it is recommended for the stills; you run it, `3d` never does.

## Scroll

### Scroll-driven 3D in an existing app
```text
/3d add a scroll-driven product reveal to /products in this Next app. Motion is our scroll library.
```
**What happens**: the project's scroll owner and rules are detected and win; the Canvas goes in a
Client Component behind a lazy wrapper; one conductor turns scroll into a normalised state; the Motion
adapter feeds it. `3d` owns what is inside the pin. You give the dev-server URL; it never starts one.

### Pre-rendered scroll scrub
```text
/3d turn this exploded-view animation into a scroll-scrubbed video that works on iPhone. Blender file attached.
```
**What happens**: [scroll-video](../skills/3d/references/scroll-video.md): frames from `render_shots.py`,
an all-intra or short-GOP H.264 encode (a default GOP is the cause of "mud" and "frame one, then
jump"), a poster cut from the encoded file, and a player that seeks at most once per frame. A short
move may use an image sequence instead. iPhone behaviour is listed under checks not run unless a real
device was used.

## Fix

### Black or washed-out render
```text
/3d my R3F scene renders black on load
```
**What happens**: the Debug lane: symptom, one confirming check (zero-height canvas, camera, near and
far, no light or environment, no GL context), one change, and a capture for the fix claim. No intake.

### A scrub that holds frame one, then snaps
```text
/3d the pinned scroll video holds the first frame while I scroll and jumps to the end at the bottom
```
**What happens**: [shared-debug](../skills/3d/references/shared-debug.md) checks the causes in order of
cost: sparse keyframes (`ffprobe` the keyframe interval), zero pin travel, progress not wired to the
scene, then a stale stylesheet after a dev-server restart (it asks you to open a fresh tab; it never
restarts your server).

### Brand colour renders wrong
```text
/3d our brand orange looks off in the web scene vs Blender
```
**What happens**: one look-dev preset and one view transform for both tools (Khronos PBR Neutral for
brand accuracy, AgX for cinematic), recorded in `3D.md`; the same intent is applied in Blender and
three.

## Assets and Blender

### Optimize a heavy GLB
```text
Use $3d to optimize hero.glb for mobile and report tris, draw calls, textures and size.
```
**What happens**: `glb-report --budget hero --target mobile` baselines it; explicit passes (never bare
`optimize`) write new files from the kept master; the result is validated, re-measured and compared
by pixel parity with `preview diff`.

### Blender product turntable
```text
/3d model a simple hard-surface speaker in Blender and render a 6 s turntable, then export a GLB.
```
**What happens**: headless Blender for export and render; an MCP bridge only if you want to watch
(consent first). Modeling passes a numeric gate; export is uncompressed from a copy, then compressed
once.

### Export from Blender, materials flat in three.js
```text
/3d my Blender export looks flat in three.js
```
**What happens**: [blender-export](../skills/3d/references/blender-export.md) and the debug table
check export options, packed textures and the view transform before touching the scene.

## Optional paths

### Custom shader
```text
/3d add a glassy refraction shader to the hero mesh, with a mobile fallback
```
**What happens**: GLSL on `WebGLRenderer` with stable uniforms and a cache key; TSL and
`WebGPURenderer` only when you need node materials or compute, with a verified WebGL2 fallback.

### Spline scene
```text
/3d our designer maintains this Spline scene; embed it in the page
```
**What happens**: decides runtime embed vs exported GLB vs R3F, without creating a second scroll or
render authority; says so if the Spline MCP is not connected.

## Review and iterate

### Notes on a version
```text
/3d here are my notes on v002 [paste]
```
**What happens**: each note is restated with the intended change, grouped by shot; a note that cannot
be mapped to a parameter gets a question; v003 is captured for every shot, diffed against v002, judged
by a fresh critic, then shown.

### Ship check
```text
/3d is v004 ready to ship? Be strict.
```
**What happens**: claim-scoped verdicts (pass, fail, unmeasurable) and the 0-3 scorecard, with
`glb-report` against the recorded budget. A performance claim needs a production build, a named
device and viewport, and p50 and p95 frame times; headless runs cannot prove real fps or Safari
rendering, and say so.

## Pairing with other skills

`3d` recommends and never invokes: `scroll-animation` for page-level scroll, pin and reduced-motion
authority, `fluid-design` for layout scaling, `generate-image` and `generate-video` for stills and
clips, `manufacturing-workflow` for CAD-to-print. Run them yourself when the receipt recommends one.
