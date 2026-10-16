# Changelog

All notable changes to the **3d** skill are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [SemVer](https://semver.org/) — **MAJOR** = artifact-contract or invocation breaks
(`3D.md`, `.3d/` layout, `refspec.v1`, `shots.v1`), **MINOR** = new areas or reference material that
changes behavior, **PATCH** = fixes, doc corrections, wording with unchanged behavior.

The release procedure synchronizes `.codex-plugin/plugin.json`, this changelog, git tag
`v<version>`, and the matching GitHub Release. Runtime `SKILL.md` contains no version metadata.

## [Unreleased]

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
