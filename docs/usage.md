# Usage reference

How to invoke `3d`, how a request becomes a lane, the preview and review controls you hold, and five
worked examples end to end. For the stages and artifacts see [loop.md](loop.md); for which reference
reads when see [areas.md](areas.md); for ready-to-paste prompts see [recipes.md](recipes.md).

## Activation

Codex invokes the skill as `$3d`; slash-command clients use `/3d`; others use an at-mention, a skill
tool or natural language. The docs use `/3d` as host-neutral shorthand.

```text
/3d <request | reference file or URL | path/to/model.glb | path/to/scene.blend>
```

Implicit triggers: "3D hero", "make it look like this", "scroll-driven 3D", "optimize this GLB",
"export from Blender", "black R3F scene", a GLB or `.blend` path.

Not for: 2D scroll or DOM animation (`scroll-animation`), layout scaling (`fluid-design`), image or
video generation (`generate-image`, `generate-video`), CAD-to-print (`manufacturing-workflow`). `3d`
recommends these and never invokes them. Project rules (`CLAUDE.md`, a motion doc, decisions already
in `3D.md`) win over every default.

## Lanes

The request decides what is read; you never name a lane. Detail in [loop.md](loop.md#lanes-entering-the-loop-partway).

| Lane | Typical request | Skips |
|---|---|---|
| Debug | black, washed, blank, slow, differs from Blender | intake, brief, design |
| Add or change one thing | a light, a shader, a loader, compress a GLB | intake and brief, unless the change contradicts the approved brief |
| Build end to end | a new 3D piece | areas the pipeline does not use |
| Blender asset | model, look-dev, render, export | `threejs-*`, `scroll-*` |
| Review and iterate | notes on a version, a ship check | intake |

## What you control

| Moment | What you do | Why it matters |
|---|---|---|
| Intake | answer with "yes" to accept a recommended answer, or change one | rounds are capped at six questions |
| Gate 0 | reply to the restated brief with an explicit yes, or edit it | "sounds good" is re-asked as an A/B, not taken as approval |
| Style frames | pick "A, B or C plus one change" | three directions that genuinely differ |
| Installs | approve or decline each proposed tool | nothing installs without your yes; `sudo` is yours to run |
| Capture | `capture: ask\|auto` in `3D.md` | the skill always asks before driving your app or browser |
| Review | open the URL, leave notes in the viewer (keys 1-9 jump shots, `[` and `]` change versions), mark `approved` or `changes` | notes land in append-only `.3d/feedback.jsonl` |
| Dev server | run it yourself and give the URL | the skill never starts, kills or restarts it |

Headless runs (no live user) write `.3d/questions.md` and stop; they build only if you said to assume
defaults, and then every assumption is tagged `[assumed]` and the brief is marked
`needs-confirmation`.

## Tools by hand

You rarely call these yourself, but they are plain CLIs. Run each by path from your project root
(`<skill>/scripts/<x>`); every one supports `--help`.

```bash
<skill>/scripts/capabilities [--root PROJECT] [--json]
<skill>/scripts/ref-extract ref.png ref.mp4 [--out .3d/refs] [--frames 12] [--scene 0.3]
<skill>/scripts/spec-check .3d/reference-spec.json .3d/shots.json .3d/look.json
<skill>/scripts/glb-report hero.glb --budget hero --target mobile [--json]

<skill>/scripts/preview serve [--dir .3d] [--port 4173]
<skill>/scripts/preview new-version --note "first greybox"
<skill>/scripts/preview capture [--version v001] [--url http://localhost:3000] [--size 854x480] [--end]
<skill>/scripts/preview diff v001 v002
<skill>/scripts/preview board --version v002
<skill>/scripts/preview feedback --version v002
<skill>/scripts/preview stop
```

Exit codes: 0 ok, 1 problems (`glb-report` FAIL, `spec-check` bad fields, a failed or blank capture),
2 usage. Blender scripts run only inside Blender:

```bash
blender -b scene.blend --factory-startup --python-exit-code 1 \
  --python <skill>/assets/blender/export_web.py -- --out .3d/versions/v001/hero.glb
```

`inspect_scene.py --json out`, `export_web.py --out x.glb [--apply auto|none|all]` and
`render_shots.py --shots .3d/shots.json --out dir` are the three; load the `.blend` before
`--python`, and keep `--python-exit-code 1` or a failed script exits 0.

## Worked examples

### 1. Vague hero prompt with a reference image

> `/3d a premium 3D hero for our landing page, like this [image]`

1. **Prepare.** No `3D.md`, so `capabilities` runs. It finds Next 16 with R3F and no Blender; the one
   proposal asks for ffmpeg and Playwright (both free). You approve.
2. **Measure.** `ref-extract` writes `contact.jpg`, `palette.json` and `luma.json` into
   `.3d/refs/ref/`. Vision passes fill `.3d/reference-spec.json`: medium `stylised-3d`, three anchors
   (silhouette, a hard rim light, a muted teal-to-orange palette), lens as a range with `low`
   confidence, and a `hidden_or_unknown` list: back of the object, absolute scale.
3. **Grill the gaps.** One question about intent (match the image or borrow its style?), then round 1:
   is it an object or an abstract form, static or scroll-driven, mobile behaviour, brand colour. Each
   comes with a recommended answer; "yes" accepts it. Brand colours and the stack are looked up, not
   asked.
4. **Gate 0.** The restated brief ends the turn with `[assumed]` tags and an Out of scope line. You
   approve.
5. **Brief and approach.** `brief.md`, `shots.json` (three shots), one look preset recorded in `3D.md`.
   Approach picks real-time R3F with a poster first.
6. **v001.** `preview new-version`, build, `preview capture` for all three shots, `preview diff`
   against the reference, `preview board`. A fresh critic reads the PNGs, the brief and the refspec
   and finds the rim light too soft; that is fixed before you ever see it. Your notes drive v002.

### 2. Video reference to measured motion to a scroll world in a Next app with Motion

> `/3d build a scroll-driven 3D section for /products. Match the camera move in this clip [ref.mp4]; we use Motion.`

1. **Detect.** The project's scroll owner, stack and rules are read from `package.json`, `CLAUDE.md`
   and any motion doc. A motion doc or an installed `scroll-animation` skill owns scroll authority and
   the pin; `3d` owns what is inside it. You are asked for your dev-server URL; the skill never starts
   it.
2. **Measure the clip.** `ref-extract ref.mp4` writes `frames/`, `contact.jpg`, `palette.json`,
   `luma.json`, `cuts.json` (scene changes) and `motion.json`. The `video` block of the refspec
   records each shot's `camera_move` (type, direction, amount, a `sampled` easing curve), its cuts per
   ten seconds and whether it loops. Those shots seed `.3d/shots.json`; speed and easing stay ranges
   unless measured.
3. **Brief with a scroll map.** Progress ranges 0-1 against beat, camera, object state and copy,
   plus the reduced-motion composition. Gate 3 shows greybox captures of every shot before any look
   work.
4. **Approach: live or scrub.** The reader steers nothing, the move is fixed and mobile risk is high,
   so the ladder starts at a pre-rendered scrub ([scroll-video](../skills/3d/references/scroll-video.md))
   with a short-GOP encode and a poster; if the scene must react to the pointer or brand data it
   stays live. The decision and its triggers are recorded in `3D.md`.
5. **Build the live variant.** The Canvas sits in a Client Component behind a lazy wrapper
   (`SceneCanvas.tsx`); `conductor.ts` turns scroll into one normalised state; the Motion adapter
   (`useMotionScrollConductor`) feeds it with progress over `wrapperHeight - 100lvh`. Camera, world
   and assets read that state; nothing is bound to React state per frame.
6. **Verify.** Mode B capture proves layout and progress through `?3d-preview` (the bridge is added to
   your repo only after you say yes). Safari and iPhone pin behaviour cannot be proven headless, so
   the receipt lists them under checks not run.

### 3. Blender product turntable

> `/3d model this speaker in Blender, render a turntable, export a GLB for the site`

1. **Channel.** Headless CLI for export and render; an MCP bridge only if you want to watch (consent
   first, one server at a time, arbitrary Python disclosed).
2. **Model.** Blockout to hard-surface, checked by a numeric gate (`inspect_scene.py`) and a render
   against your references. `blender-version-traps` is read before any `bpy` is written.
3. **Look-dev and render.** Web-safe materials, baked procedurals, then `render_shots.py` renders
   `shots.json` as numbered frames; the turntable encodes from those frames with the same view
   transform as the page.
4. **Export.** `export_web.py` writes an uncompressed GLB from a copy into `.3d/versions/v001/`;
   [asset-pipeline](../skills/3d/references/asset-pipeline.md) compresses once, keeping the master.
   `glb-report` states triangles, draw calls, textures and size against the budget, and a pixel-parity
   capture compares master and optimised GLB.

### 4. Heavy GLB to pipeline and pixel parity

> `/3d hero.glb is 38 MB; get it web-ready`

1. `glb-report hero.glb --budget hero` baselines it and names the heavy axis (here, textures).
2. The pipeline runs explicit passes, each writing a new file: `dedup`, `weld`, `prune --keep-leaves
   true`, `resize` to the recorded texture budget, then KTX2 (`etc1s` for colour, `uastc` for normals)
   if `ktx` is installed or WebP if not, then `meshopt --level high`. It never runs bare
   `gltf-transform optimize`: its defaults are lossy.
3. `gltf-transform validate out.glb`, then `glb-report out.glb --budget hero` against the `3D.md`
   budget, then a node-and-material-name comparison with the master.
4. **Pixel parity.** The same shots are captured from master and optimised file (one version each) and
   `preview diff vA vB` scores them. Lossless-intended passes fail below SSIM 0.99 or above 0.5%
   changed pixels, and the offending pass is redone from the master; lossy texture passes are judged
   by eye and the numbers recorded. If headless GL is unavailable, that is reported rather than passed.
5. The before and after byte counts go into the `3D.md` version log, and the loader config is checked
   against [threejs-loading](../skills/3d/references/threejs-loading.md) (`MeshoptDecoder`, KTX2
   transcoder path).

### 5. Debugging a black R3F scene

> `/3d my R3F scene renders black`

This is the Debug lane: no intake, no brief.

1. [shared-debug](../skills/3d/references/shared-debug.md) is read first. It reproduces on the same URL
   and viewport (you supply it), reads console and network errors, and confirms the tab is current.
2. The black-canvas rows are checked cheapest first: the Canvas has zero CSS height; the camera is
   inside or facing away from the object; near and far are wrong; a lit material has no light or
   environment; no GL context was created (`renderer.getContext()`, `renderer.info.render.calls`).
3. One change is made, and the claim "fixed" cites a capture. If it is black only in headless capture,
   that is a hidden-page or no-GL problem (`document.visibilityState`, the capture report's renderer
   string), not a scene bug.
4. Only the one area file the table names is opened ([threejs-renderer](../skills/3d/references/threejs-renderer.md)
   or [threejs-lookdev](../skills/3d/references/threejs-lookdev.md)); nothing else is read.

## Outputs and completion

| Output | Complete when |
|---|---|
| `.3d/brief.md`, `.3d/shots.json` | you approved the restated brief |
| `.3d/versions/vNNN/` and `.3d/evidence/vNNN/` | a capture exists for every shot |
| GLB or render | `glb-report` is within budget, or the overrun is recorded |
| `3D.md` | matches what shipped; version log updated, one line per critic round |

Done when you approved a version (or the single change is verified), `preview stop` has run, and the
bridge is removed if you asked. The handoff is a receipt of at most 400 tokens: files changed,
versions and status, evidence paths, measured budgets, checks not run (real devices, Safari), open
notes and proposals, and any adjacent skill worth recommending.
