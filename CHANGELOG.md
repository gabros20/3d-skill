# Changelog

All notable changes to the **3d** skill are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [SemVer](https://semver.org/) — **MAJOR** = artifact-contract or invocation breaks
(`3D.md`, `.3d/` layout, `refspec.v1`, `shots.v1`), **MINOR** = new areas or reference material that
changes behavior, **PATCH** = fixes, doc corrections, wording with unchanged behavior.

The release procedure synchronizes `.codex-plugin/plugin.json`, this changelog, git tag
`v<version>`, and the matching GitHub Release. Runtime `SKILL.md` contains no version metadata.

## [Unreleased]

## [0.8.0] - 2026-10-17

### Changed

- **Framing: reference → 3D reproduction → where it lives.** The skill is presented as turning a
  prompt, a photo or a clip into a 3D reproduction shipped as an interactive element on a page, a
  Blender asset, a render or a web-ready GLB; scroll-driven 3D is one placement among these. The
  `SKILL.md` description leads with it and adds the trigger "recreate this in 3D"; plugin metadata,
  README, docs, site and `llms.txt` follow, with one canonical example (a speaker in a clip rebuilt
  as a model visitors spin on a product page).
- **brief-approach:** new **OBJECT live** pipeline row — a real-time GLB the visitor spins, zooms
  or configures, poster first — routing to `threejs-interaction`, `threejs-lookdev`,
  `threejs-loading`, `asset-pipeline`.
- **Explainer video (4:46):** act one follows the canonical example and adds a "Know the ceiling"
  scene (the feasibility gate); act two replaces the scroll-conductor scene with "Know when to
  stop" (S1–S4, MAX REACHED). Counts updated (48 references, six scripts plus eight Blender tools).
- **Stale public counts fixed:** README, `docs/areas.md`, the site and `llms.txt` now list 48
  references in eleven packs (Engine and realism; Blender 13), eight universal rules, the current
  `preview` subcommands and `capabilities` rows.

### Added

- Activation eval: reference clip → interactive model on a product page.

## [0.7.0] — 2026-10-17

Blender for agents, verified on Blender 5.2.2 headless: about 130 API names checked, plus headless proofs for
the texture chain, Rigify, NLA bake, physics, compositing and the shadow catcher.

### Added
- `blender-scripting`: the canonical home for agentic bpy. It covers data-API first, `temp_override`, depsgraph
  evaluation, the 5.x layered and slotted Action API, Geometry Nodes inputs plus `update_tag` and
  `view_layer.update`, idempotent scripts, verification after every change, headless limits (no timers, no undo),
  `--python-exit-code` and the JSON result contract, batch and farm rendering, and file hygiene.
- New references: `blender-shading`, `blender-uv-bake`, `blender-texturing` (CC0 first, then generate-image,
  then seam gate, de-light, PBR maps, material, bake; licence gates for CHORD, Hunyuan3D in EU/UK/KR and
  TRELLIS NC; paid texture APIs per job), `blender-geometry-nodes`, `blender-rigging` (Rigify headless,
  weights, web export of deform bones), `blender-animation` (layered Actions, NLA as one glTF clip per action,
  drivers, Grease Pencil, VSE), `blender-physics` (rigid body, cloth, soft body, Mantaflow, hair curves,
  simulation nodes and XPBD, simulations to the web).
- New bpy tools, each tested headless: `bake_maps.py`, `material_from_maps.py`, `texture_prep.py`
  (seam test and fix, de-light, derive normal/roughness/height), `uv_check.py`, `rig_check.py`.
- `capabilities` reports the Blender version and official-MCP readiness, Rigify, the Cycles device hint, and
  ComfyUI and Material Maker presence. For paid generative-3D keys it shows set or not, never the value.

### Changed
- `blender-channels`: the official Blender Lab MCP v1.0.3, with its tool map, online-access gate, lack of
  undo and sandbox, headless serving, and an evidence rule (MCP screenshot vs headless render).
- `blender-modeling`: modifier stack order, sculpt, retopology, decimate for the web, cleanup of generated
  meshes. `blender-lookdev-render` now holds render settings, passes, compositing and the shadow catcher.
- `blender-version-traps`:
  - VSE strips; `world.use_nodes`.
  - Rigify needs `default_set=True`; OIDN is the only denoiser on Apple.
  - Resample Curve mode is a socket; `remove_doubles`; `shade_smooth_by_angle`.
- `shared-debug` gains rows for Blender's silent failures: a bake CANCELLED with no image node, a stale
  Geometry Nodes result, `-a` flag order, F-curve modifiers not exporting, `rigidbody.bake_to_keyframes`
  failing headless.

### Fixed
- `export_web.py` and `render_shots.py` `--help` exit 0.

## [0.6.0] — 2026-10-16

Engine choice and a measured Blender → web export path (a test scene rendered in Cycles, EEVEE,
three.js r186 and Babylon.js 9.31).

### Added
- `engine-choice` reference: an engine gate at the approach step. The default is three.js + R3F + drei.
  It recommends Babylon.js, PlayCanvas, Needle, model-viewer or Spline when the project fits, using
  measured bundle sizes, download numbers and glTF extension coverage. It also covers Babylon notes
  (env rotation, lightmaps in code, Inspector, plain Babylon in a Next client component; react-babylonjs
  is not recommended). The engine decision is recorded in `3D.md`.
- `blender-export`: a per-goal strategy table and a pre-export checklist.

### Changed
- `export_web.py` defaults: COMPAT light units, lights and cameras on, Geometry Nodes meshes on,
  `--gn-instances`; warns when volume or thin-film materials lack the glTF Material Output group and
  when an instance source would export as its own node.
- Export knowledge from measurement:
  - Volume, thickness, dispersion and iridescence need the Material Output group; the default light
    mode blows HDR-lit scenes out.
  - Shadows are not in glTF; materials export double-sided by default.
  - Blender's built-in gltfpack needs its binary set in the add-on preferences; diffuse transmission is
    not exported; the .babylon exporter is frozen; KHR_gaussian_splatting is ratified.
  - Judge compression by VRAM, not file size.
- `threejs-loading`: after loading a Blender glTF, add shadows, assign lightmaps in code, fix the
  double-sided default.

## [0.5.0] — 2026-10-16

Realism know-how, a feasibility gate and a stop mechanism, built from a live test where real-time
three.js could not match an AI-generated, path-traced-looking reference, and from mining that
session's transcript.

### Added
- `realism-gap` (22 features in five tiers: live-native, live-with-technique, bake-only,
  offline-only, reference artefact), `realism-toolbox` (18 ranked techniques, WebGL vs WebGPU r186,
  realism stacks within the post-pass budget, in-browser path tracing as refine-when-idle) and
  `realism-gate` (provenance → tiers → ceiling per category → achievable ship bars → a ≤150-word
  statement before any build → `.3d/feasibility.json`).
- Defect labels FIXABLE(T#) / CEILING(G#) / ARTEFACT(R#); a path-traced twin
  (`preview capture --pathtrace`, three-gpu-pathtracer WebGPU, Cycles fallback via
  `render_shots.py --import --world`) splits design gap from real-time gap.
- Deterministic stop: `preview rounds` (S1 nothing fixable · S2 plateau · S3 small gain or pipeline
  change · S4 budget), per-technique cap, best-version-so-far, and a MAX REACHED report with a
  direction menu inside the brief's core.
- `preview match --json`, `preview sweep`, `preview compare --stack`, `new-version --technique`,
  params via `?p=` / `readParams` / `setParams`; `ref-extract --motion-json` (period, speed,
  amplitude per region and kymo line, oscillating vs travelling); `fit-camera` (camera solve from
  anchor points); `spec-check` for feasibility.v1 and rounds.v1.
- Bake-for-web and Matching Blender recipes; realism recipes in threejs-lookdev / threejs-postfx.

### Changed
- Ship bars are the achievable ceiling (per category min(2, ceiling); average min(2.3, mean − 0.2)).
- Numbers before images (≤ 4 image views per iteration, never the same path twice); checkpoint and
  hand off at user gates and past ~300k context; tunables live in one params block.
- Rule 7: a CEILING gap is reported, never faked.

## [0.4.0] — 2026-10-16

Rules from the live test's post-mortem, so the skill blocks the mistakes that test made.

### Changed
- The brief's core is binding (SKILL.md universal rule 7): no option, fallback or ladder step may drop
  it. For a live-3D "recreate a reference" brief the ladder is rebuild geometry + contrasty studio
  environment → baked lighting; plate, light-only, warp and pre-rendered routes appear only as an
  explicit brief change the user approves.
- A rejected approach rejects its whole family, and the user's direct words outrank relayed or earlier
  instructions; rejections are recorded in `3D.md`.
- Projection mapping only onto locked geometry or motion smaller than the plate-to-geometry fit error.
- Intake checks whether a reference is physically consistent (AI-generated references often are not)
  and agrees a stylised target when it isn't; geometry is fitted to measured anchors plus
  `preview diff --edges`, never to colour masks; motion is measured as geometry, not highlights.
- Plateau = 2 rounds with no score change in a failing category → stop and ask; the anchored rubric
  applies from round 1.
- Look-dev: bloom only on emissive sources; tone curve settled against reference luma before material
  work; contrasty environments for polished metals; no fog that hides geometry.

### Fixed
- `preview capture` (and `--clip`) refuses to overwrite an evaluated version's evidence unless `--force`.
- `preview stop` recovers a server whose pid file is missing or stale (by port, verified as
  `preview serve`), and never kills an unrelated process.

## [0.3.1] — 2026-10-16

### Fixed
- `preview new-version` is atomic: it builds in a temp dir and renames into place only after the
  snapshot and manifest succeed. Failures and interrupts leave no empty `vNNN`, and numbering counts
  only complete versions.

## [0.3.0] — 2026-10-16

Fixes and features from a live end-to-end test (recreating a generated video loop in three.js).

### Added
- `shots.v1` optional `t` (seconds) for time-driven scenes and loops; the bridge `setTime(t)` hook,
  viewer, `preview capture` and `render_shots.py` honour it.
- `preview serve --app DIR` (static pages at `/app/`), `preview new-version --snapshot PATH...`,
  `preview diff --edges` (structure-only comparison), `preview capture --clip SECONDS` (deterministic
  frame sequence + mp4 of the render).
- `ref-extract --regions N` (per-cell motion energy + dominant period) and `--kymo` (time-slice images).
- "Recreating a reference" ladder in `brief-approach`: light-only over the plate → 2D warp → projection
  mapping (clean plates only) → rebuild geometry → baked lighting → pre-rendered video; intake asks for
  clean plates and source stills.

### Changed
- Fresh-critic gate: the same anchored rubric (pass criteria derived from refspec measurements) every
  round; the render is measured like the reference before any critic round; the loop is bounded
  (3 non-converging rounds → stop and ask) and a category stuck at 1 for 3 rounds is a plateau →
  change approach.
- Gates 2–4 can be pre-approved at intake as "approve on critic pass".
- Explainer video re-timed for reading: every hold is computed from its on-screen text
  (2 s + words/3 + 1 s per visual group); scenes trimmed to their key lines (4:04).

## [0.2.0] — 2026-10-16

### Added
- Explainer video "How 3d works" (Remotion 4.0.536, two acts, 2:18, light + dark) and the
  orchestrate-style player on the site: controls hidden while playing, chapters, keyboard,
  fullscreen, reduced-motion and missing-file fallback to the static loop diagram.
- `docs/loop.md` and `docs/areas.md`; README and docs rebuilt (worked examples, 16 recipes).

### Changed
- Fresh-critic gate: a failing critic round is fixed as a new version and re-captured; only a
  passing version is shown to the user.
- Gate 2 (style frames) passes only on rendered style frames plus the user's yes; picking A/B/C in
  the grill is a direction choice.
- Intake answers are marked resolved in `.3d/questions.md` and `3D.md` as they come in; `3D.md` is
  updated at every gate, not only at the end.
- `scroll-conductor` ownership: pre-rendered scrub video is owned via `scroll-video` when
  `scroll-animation` is absent.
- Remotion authoring skills refreshed from the official source (`npx skills add remotion-dev/skills`).

### Removed
- The 29 s hero animation (replaced by the explainer).

## [0.1.0] — 2026-10-16

### Added
- Initial release: one routed skill, `3d` (`/3d`, `$3d`), for production 3D on the web and in
  Blender. The loop: intake (intent plus references decomposed into a measured spec) → brief and
  shots → approach (target use → pipeline) → build → versioned preview → iterate with the user →
  record in `3D.md`.
- Front door: grilling rounds with recommended answers, reference extraction (`scripts/ref-extract`,
  `refspec.v1`), brief, storyboard and `shots.v1`, a lexicon that turns vague terms into checkable ones.
- Areas: three.js and R3F (renderer, Next integration, look-dev, loading, post, interaction),
  GLSL and TSL shaders, stack-agnostic scroll-driven 3D (one conductor; native, Motion, GSAP, Lenis; scroll-scrubbed video via `scroll-video`
  adapters), art direction and look-dev presets, the glTF asset pipeline, Blender (headless and MCP
  channels, modeling, look-dev and render, export, version traps), Spline, splats and XR, CAD routing.
- Tooling (run as `<skill>/scripts/<x>` from the project root): `scripts/capabilities` (detect, propose installs with cost, never install),
  `scripts/spec-check` (validates `refspec.v1`, `shots.v1`, `look.v1`), `scripts/glb-report` (budgets, PASS/WARN/FAIL), `scripts/ref-extract`, `scripts/preview` (`--dir`; serve,
  versions, shot capture, SSIM/PSNR diff, storyboard `board`, feedback, `stop`), Blender scripts, web blocks (`conductor.ts`,
  adapters, `SceneCanvas.tsx`, `bridge.ts`), `.3d/look.json` viewer look, a fresh-critic gate and per-stage sign-off, templates for `3D.md`, brief, shots and refspec.
- Repository: README, docs, evals (activation, traversal, output, compression ablation), tests,
  `scripts/check-sync`, a documentation site and hero-video project, `SOURCES.md` provenance.

[Unreleased]: https://github.com/gabros20/3d-skill/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gabros20/3d-skill/releases/tag/v0.1.0
