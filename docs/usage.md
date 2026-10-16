# Usage reference

## Activation

Implicit triggers: "3D hero", "make it look like this", "scroll-driven 3D", "optimize this GLB",
"export from Blender", "black R3F scene", a GLB or `.blend` path. Explicit: `$3d` in Codex, `/3d`
in slash-command clients, a mention or skill tool elsewhere.

Not for: 2D scroll or DOM animation (`scroll-animation`), image or video generation
(`generate-image`, `generate-video`), CAD-to-print (`manufacturing-workflow`). `3d` recommends these
and never invokes them. Project rules (CLAUDE.md, a motion doc, existing `3D.md` decisions) win.

## The loop

```text
prepare → intake → brief + shots → approach → build → preview → iterate → record
```

1. **Prepare.** No `3D.md`: `<skill>/scripts/capabilities` inventories tools and stack; one batched install proposal.
2. **Intake.** References go through `<skill>/scripts/ref-extract` and vision passes into
   `.3d/reference-spec.json`; missing detail is asked in rounds of at most six questions, each with a
   recommended answer. The turn ends on a restated brief and an explicit yes. Headless runs record
   assumptions and do not build.
3. **Brief and shots.** `.3d/brief.md` and `.3d/shots.json` (cameras, beats, scroll map); the chosen look is written to `.3d/look.json`. `<skill>/scripts/spec-check` validates the refspec, shots and look files.
4. **Approach.** Target use maps to a pipeline and fallback ladder, recorded in `3D.md`.
5. **Build.** Only the area files the pipeline names; one change-set per version (`preview new-version`). Scroll-scrubbed video follows the `scroll-video` reference when `scroll-animation` is absent.
6. **Preview and iterate.** Every shot is captured and diffed against the reference and the previous
   version (`preview capture`, `diff`, `board`); a fresh critic judges that evidence; you get the URL, version and change, and your notes
   become the next version. You sign off stage by stage; stop on approval, then `preview stop`.
7. **Record.** Verdicts, `glb-report` against the budget, a version-log line in `3D.md`.

`<skill>` is the installed skill directory; run its scripts by path from your project root. `preview` takes `--dir` (default `.3d`).

## Lanes

You can enter directly; the lane decides what is read.

| Lane | Typical request | Skips |
|---|---|---|
| Debug | black, washed, blank, slow, differs from Blender | intake, brief, design |
| Add or change one thing | a light, a shader, a loader, compress a GLB | intake and brief unless the change contradicts the brief |
| Build end to end | a new 3D piece | areas the pipeline does not use |
| Blender asset | model, look-dev, render, export | `threejs-*`, `scroll-*` |
| Review and iterate | notes on a version, ship check | intake |

## Worked examples

### Vague hero prompt with a reference image

> `/3d a premium 3D hero for our landing page, like this [image]`

- `ref-extract` writes palette, luma and contact sheet; vision passes fill `.3d/reference-spec.json` (what one view hides is flagged, not invented).
- Round 1 asks the frontier: object or abstract form, static or scroll-driven, mobile behaviour, brand colour. Each has a recommended answer; "yes" accepts.
- You approve the restated brief. Approach picks real-time R3F; look-dev preset and colour policy are recorded.
- v001 renders; shots are captured and diffed against the reference; the critic's findings are fixed before you see it. Your notes drive v002.

### Blender product turntable

> `/3d model this speaker in Blender, render a turntable, export a GLB for the site`

- Channel: headless CLI for export and render; MCP only if you want to watch (consent first, one server at a time).
- Modeling passes a numeric gate; look-dev uses web-safe materials; `render_shots.py` renders `shots.json`.
- Export is uncompressed from a copy; `asset-pipeline` compresses once; `glb-report` states tris, draw calls, textures and size against the budget; a pixel-parity capture compares master and optimized GLB.

### Scroll-driven world in an existing Next app with Motion

> `/3d add a scroll-driven 3D section to /products; we use Motion`

- Detects the project's scroll owner and stack; the Canvas lives in a Client Component behind a lazy wrapper; no dev server is started (you give the URL).
- The conductor turns scroll into one normalized state; the Motion adapter feeds it; camera, world and assets read that state. If `scroll-animation` is installed it owns scroll authority and pin; otherwise the skill states its measured pin rule.
- Verification includes a device check for iPhone pin jumps; what could not be measured is reported.

### Optimize a heavy GLB

> `/3d hero.glb is 38 MB; get it web-ready`

- `glb-report` baselines it; explicit passes (meshopt by default, KTX2 or resize for textures) replace bare `optimize`, which has lossy defaults.
- Master is kept; the result is judged by `glb-report` and a pixel-parity diff; the size line goes into `3D.md`.

## Outputs and completion

| Output | Complete when |
|---|---|
| `.3d/brief.md`, `.3d/shots.json` | you approved the restated brief |
| `.3d/versions/vNNN/` and `.3d/evidence/vNNN/` | a capture exists for every shot |
| GLB or render | `glb-report` is within budget, or the overrun is recorded |
| `3D.md` | matches what shipped; version log updated |

Handoff is a receipt of at most 400 tokens: files changed, versions and status, evidence paths,
measured budgets, checks not run (real devices, Safari), open notes and proposals.
