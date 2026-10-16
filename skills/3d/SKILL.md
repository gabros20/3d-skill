---
name: 3d
description: >-
  Plan, build, preview and iterate production 3D for the web and Blender: decompose intent and
  image/video references into a measured spec, brief and shots, then build three.js/R3F
  scenes, shaders, scroll-driven 3D, look-dev, GLB pipelines, Blender assets and renders, Spline,
  splats and AR, with versioned previews. Triggers: "3D hero", "make it look like this",
  "scroll-driven 3D", "optimize this GLB", "export from Blender", "black R3F scene". Not for 2D
  scroll/DOM animation (→ scroll-animation), image/video generation (→ generate-image,
  generate-video) or CAD-to-print (→ manufacturing-workflow).
---

# 3D

## Mission and boundary

Own a 3D piece end to end: request or reference → measured spec → approved brief and shots →
pipeline → build → versioned previews the user reviews → the record in `3D.md`. Not the page
around it (2D motion, layout, image or video generation, printing). Works alone; project rules
and decisions already in `3D.md` win over every default here.

Invoke as `/3d` or `$3d` with a request, a reference file or URL, or a GLB/`.blend` path.
`<skill>` is this installed skill's directory. Run every script by path, `<skill>/scripts/<x>`,
with the user's project root as the working directory, so defaults such as `.3d` land in the
project. Never run them from the skill directory.

## Route before acting

1. Pick the lane, then read only the files it names. Never preload the reference library.
2. Detect before routing: `3D.md`, `.3d/`, `package.json`, `.3d/capabilities.md`. An existing
   decision stands; changing one goes through [shared-preflight](references/shared-preflight.md).
3. A symptom goes to [shared-debug](references/shared-debug.md) before any area file; a scrub that
   holds frame one, then snaps has several causes there, cheapest check first.

| Lane | Read | Skip |
|---|---|---|
| **Debug a broken scene**: black, washed, blank, slow, unlike Blender or the reference | [shared-debug](references/shared-debug.md) → the one area file it names → [shared-verification](references/shared-verification.md) for the fix claim | intake, brief, design |
| **Add or change one thing**: a light, a shader, a loader, compress a GLB, one export | the area row below; [shared-preview](references/shared-preview.md) when the user must see it | intake and brief, unless the change contradicts the approved brief |
| **Build a new 3D piece end to end** | the whole Core workflow: front door → [brief-approach](references/brief-approach.md) → only the packs it names | areas the pipeline does not use (no Blender rows for a code-built scene) |
| **Blender asset**: model, look-dev, render, export | [blender-channels](references/blender-channels.md) → the one Blender file for the task; [blender-version-traps](references/blender-version-traps.md) before writing `bpy`; [asset-pipeline](references/asset-pipeline.md) after export | `threejs-*`, `scroll-*` |
| **Review and iterate**: notes on a version, "does it match", a ship check | [shared-preview](references/shared-preview.md) → [shared-verification](references/shared-verification.md); [shared-performance](references/shared-performance.md) for numbers | intake; area files unless a note maps to one |

### Front door

| Condition | Read | Contribution |
|---|---|---|
| New request without an approved `.3d/brief.md`; vague prompt | [intake-grill](references/intake-grill.md) | frontier rounds of ≤ 6 questions with recommended answers; restate and explicit yes |
| An image, video, screenshot, site capture, "make it look like this" | [intake-references](references/intake-references.md) | `<skill>/scripts/ref-extract` plus vision passes → `.3d/reference-spec.json` |
| Writing or validating `.3d/reference-spec.json`; a refspec becomes a generation prompt | [refspec](references/refspec.md) | the `refspec.v1` schema |
| Refspec or brief must become camera, lights, tone, materials, post | [refspec-mapping](references/refspec-mapping.md) | starting values and the parameter to move first |
| Brief, storyboard, shot list, scroll map, camera path, sign-off gates | [brief-spec](references/brief-spec.md) | `.3d/brief.md`, `.3d/shots.json` (`shots.v1`), lens defaults, the five gates |
| "Make it look exactly like this render"; "how real can three.js get" | [realism-gap](references/realism-gap.md) | each feature tiered live, bake-only, offline-only or artefact; ceiling per category |
| A vague term ("dramatic", "glossy") must become checkable | [brief-lexicon](references/brief-lexicon.md) | production wording |
| Choosing how to build it: real-time or pre-render (scrub video), fallback ladder | [brief-approach](references/brief-approach.md) | Pipeline section and the area files to read next |

### Shared

| Condition | Read | Contribution |
|---|---|---|
| No `3D.md`, a recorded decision would change, "command not found" | [shared-preflight](references/shared-preflight.md) | capabilities, defaults, one batched install proposal |
| Renders wrong, blank, slow, or unlike Blender or the reference | [shared-debug](references/shared-debug.md) | symptom → confirming check → one change |
| Budgets; slow, hot, first-frame jank, memory growth | [shared-performance](references/shared-performance.md) | canonical budgets by target, frame-loop rules |
| A version the user must see; notes came back | [shared-preview](references/shared-preview.md) | versions, captures for every shot, feedback loop |
| About to say done, matches or fast | [shared-verification](references/shared-verification.md) | claim-scoped verdicts and scorecard |
| Critic not converging; "keep going?", "should we stop", a ceiling claim | [realism-gate](references/realism-gate.md) | feasibility gate, defect labels, `preview rounds` verdict, MAX REACHED report |

### three.js, R3F and shaders

| Condition | Read | Contribution |
|---|---|---|
| Vanilla renderer setup; washed, dark or blank output; `Clock`, `PostProcessing`, `RGBELoader` | [threejs-renderer](references/threejs-renderer.md) | backend, colour, one loop, resize, dispose, stale APIs |
| `<Canvas>` in Next or React; `ssr: false` errors; double mount; GPU burning off-screen | [threejs-r3f-next](references/threejs-r3f-next.md) | client-only scene behind a lazy wrapper |
| Lighting rig, environment, materials, shadows; metals render black | [threejs-lookdev](references/threejs-lookdev.md) | env, 1–3 lights, material roles, shadow cost |
| Loaders and decoders (meshopt, Draco, KTX2); freeze after the preloader | [threejs-loading](references/threejs-loading.md) | one loader config, gated reveal |
| Bloom, LUT, DOF, SSAO; double tone mapping | [threejs-postfx](references/threejs-postfx.md) | one pipeline, no-post baseline |
| Picking, orbit or transform controls, glTF clips, physics proposals | [threejs-interaction](references/threejs-interaction.md) | event wiring, one mixer owner |
| Which effect closes this gap; the realism stack | [realism-toolbox](references/realism-toolbox.md) | ranked techniques (T ids) with cost, gain and recipe home |
| Custom GLSL or patched materials on `WebGLRenderer` | [shader-glsl](references/shader-glsl.md) | stable uniforms, cache key, mobile fallback |
| TSL, node materials, compute, `WebGPURenderer` | [shader-tsl](references/shader-tsl.md) | node graphs built once, verified WebGL2 fallback |

### Scroll, design and assets

| Condition | Read | Contribution |
|---|---|---|
| A live scene moves with scroll: camera path, chapters, pinned 3D | [scroll-conductor](references/scroll-conductor.md) | one conductor, ownership split with `scroll-animation` |
| A fixed move pre-rendered and scrubbed: "scrub video", frames on scroll; a scrub that feels like mud or freezes on iPhone | [scroll-video](references/scroll-video.md) | short-GOP encodes, poster, `currentTime` from the conductor, frame fallback |
| Feeding the conductor from native, Motion, GSAP, Lenis or `ScrollControls`; pin jumps on iPhone | [scroll-adapters](references/scroll-adapters.md) | one adapter, the pin rule, device checks |
| What the 3D should be: world, chapters, composition; "looks flat or CG" | [design-art-direction](references/design-art-direction.md) | world sentence, scene ledger, shot plan, critique |
| Pick a look; brand colour renders wrong; Blender and three disagree | [design-lookdev-presets](references/design-lookdev-presets.md) | one preset, one view transform, recorded |
| No model yet: stock, generative 3D, image-to-procedural | [asset-acquire](references/asset-acquire.md) | source per object, licence line, paid-job rules |
| A GLB must ship; about to type `gltf-transform`, `gltfpack`, `ktx`, `gltfjsx` | [asset-pipeline](references/asset-pipeline.md) | explicit passes (never bare `optimize`), master kept, size line |

### Blender

| Condition | Read | Contribution |
|---|---|---|
| Any Blender task; MCP or headless; a bridge timed out | [blender-channels](references/blender-channels.md) | channel, connection, consent for arbitrary Python |
| Blockout, hard-surface, Geometry Nodes, repairing an import | [blender-modeling](references/blender-modeling.md) | a `.blend` that passes the numeric gate |
| Materials, bakes, lighting, stills, turntables, loops | [blender-lookdev-render](references/blender-lookdev-render.md) | web-safe materials, baked maps, frames |
| Export GLB or USDZ; "materials lost", "flat in three.js" | [blender-export](references/blender-export.md) | uncompressed GLB into `.3d/versions/vNNN/` |
| Writing or debugging any `bpy` | [blender-version-traps](references/blender-version-traps.md) | Blender 5.x old → new calls |

### Optional

| Condition | Read | Contribution |
|---|---|---|
| Spline named; a designer maintains the scene | [spline](references/spline.md) | Spline runtime, Spline GLB or R3F, decided |
| Splats (`.ply`, `.spz`), WebXR, AR, Quick Look | [splats-xr](references/splats-xr.md) | splat or XR integration with budgets |
| Printable or mechanical part, STL/STEP, CAD in a web scene | [cad-print](references/cad-print.md) | routing to CAD skills, verification laws |
| Where a technique came from; licence questions | [SOURCES](references/SOURCES.md) | provenance per area |

### Tools

| Tool | Usage | Gives |
|---|---|---|
| `<skill>/scripts/capabilities` | `[--root PROJECT] [--json]` | `.3d/capabilities.md`: tools with cost, stack, Blender, MCP hints; never installs |
| `<skill>/scripts/ref-extract` | `INPUT... [--out .3d/refs] [--frames 12] [--scene 0.3]` | per ref metadata, frames, contact sheet, palette, luma; video cuts and motion; needs ffmpeg |
| `<skill>/scripts/glb-report` | `FILE [--budget hero\|world\|ar\|none] [--target desktop\|mobile] [--json]` | tris, draw calls, textures, size; PASS/WARN/FAIL, exit 1 on FAIL |
| `<skill>/scripts/spec-check` | `FILE...` | validates `refspec`, `shots`, `look`, `feasibility`, `rounds` (v1); exit 1 names bad fields |
| `<skill>/scripts/preview` | `serve` · `new-version --note [--technique T#]` · `capture [--version] [--url] [--pathtrace]` · `diff A B` · `board` · `rounds` · `feedback` · `stop`; all take `--dir` (default `.3d`) | viewer, versions, captures (path-traced twin), SSIM/PSNR, contact sheet, stop verdict, notes ([shared-preview](references/shared-preview.md)) |
| `<skill>/assets/blender/*.py` | `blender -b in.blend --factory-startup --python-exit-code 1 --python <skill>/assets/blender/<x>.py -- …` | `inspect_scene.py --json out` · `export_web.py --out x.glb [--apply auto\|none\|all]` · `render_shots.py --shots .3d/shots.json --out dir [--import x.glb --world env.hdr]` |
| `<skill>/assets/web/` | copy and own; read each header first | `conductor.ts`, `adapters/*`, `r3f/SceneCanvas.tsx`, `bridge.ts` (dev-only; ask before adding) |
| `<skill>/assets/templates/` | copy into the project | `3D.md`, `brief.md`, `shots.json`, `refspec.example.json` |

## Universal rules

1. **Read only the routed files.**
2. **Detect before asking.** Facts come from the repo, `3D.md` and `.3d/capabilities.md`; ask only
   the user's decisions, each with a recommended answer.
3. **Never install without explicit approval.** Propose with cost (free, free account, PAID); run
   only after the user's yes. Paid generative jobs need approval per job and are never resubmitted
   on timeout.
4. **The dev server is the user's.** Never start, kill or restart it; ask for the URL. `preview
   serve` serves `.3d/` only, on its own port; `preview stop` ends it with the session.
5. **Evidence before claims.** Every "done", "matches" or "fast" cites a capture, a
   `glb-report` or a measurement of that exact claim; say what could not be measured.
6. **One canonical home.** Decisions, budgets, colour policy and scroll owner live in `3D.md`;
   read them there and never keep a second copy.
7. **The brief's core is binding.** Never offer or build an option that drops it; a CEILING gap
   is reported, never faked. A rejected approach rejects its whole family; the user's direct
   words outrank relayed or earlier instructions.
8. **Adjacent skills are recommended, never invoked**: `scroll-animation`, `fluid-design`,
   `generate-image`, `generate-video`, `manufacturing-workflow`, `frontend`.

## Core workflow

1. **Prepare.** No `3D.md`: [shared-preflight](references/shared-preflight.md) runs
   `<skill>/scripts/capabilities` and fills `3D.md` from `<skill>/assets/templates/3D.md`.
2. **Intake.** Decompose intent and every reference into the most detailed spec: references
   through `<skill>/scripts/ref-extract` and [intake-references](references/intake-references.md)
   into `.3d/reference-spec.json`; missing detail grilled per [intake-grill](references/intake-grill.md).
   End the turn on the restated brief and an explicit yes. No live user: write `.3d/questions.md`
   and stop, unless told to assume defaults (then tag them `[assumed]` in the brief).
3. **Brief and shots.** [brief-spec](references/brief-spec.md) writes `.3d/brief.md` and
   `.3d/shots.json`; the look comes from the design files and is written to `.3d/look.json`.
   Validate with `<skill>/scripts/spec-check`. Then pass the [sign-off gates](references/brief-spec.md)
   in order, each on the user's yes: brief → style frames → blockout → lookdev → final.
4. **Approach.** [brief-approach](references/brief-approach.md) maps target use to a pipeline and
   fallback ladder, records it in `3D.md`, and names the area files. A matched reference or a
   realism ask first passes the [feasibility gate](references/realism-gate.md): ceilings, ship
   bars and planned techniques, accepted by the user before build.
5. **Build.** Read only those files. One change-set per version (`<skill>/scripts/preview new-version`).
6. **Preview and iterate.** Capture every shot, diff against the reference and previous version;
   a [fresh critic](references/shared-verification.md), not told what was fixed, judges it first.
   Show the user URL, version, change and `preview board`; map each note to the next version
   ([shared-preview](references/shared-preview.md)). Stop when `preview rounds` says so
   ([realism-gate](references/realism-gate.md)): pass goes to the user, a stop gives the MAX
   REACHED report.
7. **Record.** Verdicts per [shared-verification](references/shared-verification.md),
   `<skill>/scripts/glb-report` against the recorded budget, a version-log line in `3D.md`.

## Artifact contract

| Path in the project | Holds | Written by |
|---|---|---|
| `3D.md` (root) | decisions, budgets, colour, scroll owner, tooling, scene ledger with licences, version log | preflight; every gate |
| `.3d/capabilities.md` | tools, stack, proposals | `capabilities` |
| `.3d/questions.md` | open questions with recommended answers when no user is live | intake-grill |
| `.3d/brief.md` | the approved brief and its Pipeline section | intake → brief-spec, brief-approach |
| `.3d/refs/<name>/`, `.3d/reference-spec.json` | mechanical extraction; `refspec.v1` | `ref-extract`; intake-references |
| `.3d/shots.json` | `shots.v1` cameras read by preview and `render_shots.py` | brief-spec; viewer `POST /shots` |
| `.3d/look.json` | `look.v1` tone mapping, exposure, environment, background the viewer reads | build, from the chosen preset |
| `.3d/versions/vNNN/` | `manifest.json` and that version's outputs; never edited once shown | `preview new-version` |
| `.3d/evidence/vNNN/`, `.3d/diffs/`, `.3d/boards/` | shot PNGs, diff images and JSON, contact sheets | `preview capture`, `diff`, `board` |
| `.3d/feedback.jsonl` | append-only notes; corrections are new lines | viewer, `preview feedback` reads |
| `.3d/feasibility.json`, `.3d/rounds.jsonl` | `feasibility.v1` targets and ship bars; one `rounds.v1` line per critic round | realism-gate |

`3D.md` is the live record: update it at every gate (questions resolved, gate passed, version and
critic round), not only at the end. Suggest gitignoring `.3d/versions` and `.3d/refs`.

## Completion and handoff

Done when the user approved a version (or the single change is verified), every shot of it is
captured, `glb-report` is within budget or the overrun recorded, `3D.md` matches what shipped,
`preview stop` has run and the bridge is removed if asked. Receipt (≤ 400 tokens): project files
changed, versions with status, evidence paths, measured budgets, checks not run, open notes,
adjacent skills worth recommending.
