# 3d

**Describe the 3D you want, or point at a reference. Get a measured spec, an approved brief, a build, and versioned previews you iterate on.**

`3d` is an agent skill for production 3D on the web and in Blender. It decomposes your intent and any image or video references into the most detailed spec it can measure, turns that into a brief and shot list, picks the pipeline, builds, shows you versions in a local preview, and iterates on your notes. Everything it decides is recorded in `3D.md`.

```text
intent + references → spec → brief + shots → approach → build → preview → iterate → record
```

Invoke as `/3d` or `$3d` (Codex) with a request, a reference file or URL, or a GLB or `.blend` path.

## Areas

| Area | What it covers |
|---|---|
| Front door | grilling rounds with recommended answers, reference extraction, `refspec.v1`, brief, storyboard, `shots.v1` |
| three.js and R3F | renderer, Next App Router, lighting and materials, loaders, post-processing, interaction |
| Shaders | custom GLSL on `WebGLRenderer`; TSL and `WebGPURenderer` when needed |
| Scroll-driven 3D | what is inside the pin: one conductor, adapters for native, Motion, GSAP, Lenis |
| Design | art direction, scene ledger, look-dev presets, one colour policy |
| Assets | stock and generative sourcing, the glTF pipeline (meshopt, KTX2), budgets |
| Blender | headless CLI and MCP channels, modeling, look-dev and render, GLB export, 5.x version traps |
| Optional | Spline, Gaussian splats, WebXR and AR, CAD routing |

It does not own 2D scroll or DOM animation (`scroll-animation`), layout scaling (`fluid-design`), image or video generation (`generate-image`, `generate-video`) or CAD-to-print (`manufacturing-workflow`). It recommends those, never invokes them, and works alone.

## Install

```bash
npx skills add gabros20/3d-skill -g -y
```

Or from a clone:

```bash
git clone https://github.com/gabros20/3d-skill.git
cd 3d-skill
./install.sh all        # Claude, Codex and the cross-agent path; or claude | codex | agents | cursor | …
```

Hosts and optional tools: [docs/installation.md](docs/installation.md).

## Quick start

```text
Use $3d to plan and build a scroll-driven 3D hero for my homepage from these references.
Use $3d to make this look like the attached screenshot.
Use $3d to optimize hero.glb for the web and tell me whether it fits the budget.
/3d export product.blend as a web-ready GLB and render a turntable
/3d my R3F scene renders black
```

A new request gets a few rounds of questions (each with a recommended answer), then a restated brief to approve. Nothing is built before that yes. Worked examples: [docs/usage.md](docs/usage.md). Copyable prompts: [docs/recipes.md](docs/recipes.md).

## The preview tool

`scripts/preview` serves a local viewer for `.3d/` (loopback only, its own port), records each change-set as a version, captures every shot with your installed Chrome, diffs versions and references (SSIM and PSNR), and reads your notes back from the viewer. It never touches your dev server. A fresh critic context judges the evidence before you see a version.

## Preflight and installs

On first use `scripts/capabilities` inventories the machine (node, Blender, gltf-transform, gltfpack, ktx, ffmpeg, Playwright and Chrome, your 3D stack, Blender and Spline MCP hints) into `.3d/capabilities.md`. Missing tools become one batched proposal with cost (free, free account, PAID). The skill never installs anything unasked; paid generative jobs need approval per job and are never resubmitted on timeout. Blender MCP servers execute arbitrary Python, so the skill asks for consent first.

## What it writes in your project

`3D.md` at the root (decisions, budgets, colour policy, scroll owner, scene ledger with a licence per asset, version log) and `.3d/` (`capabilities.md`, `brief.md`, `refs/`, `reference-spec.json`, `shots.json`, `versions/vNNN/`, `evidence/`, `feedback.jsonl`). Suggest gitignoring `.3d/versions` and `.3d/refs`.

## Repository map

```text
skills/3d/        the installed pack: SKILL.md router, references/, scripts/, assets/, agents/openai.yaml
docs/             installation, usage, recipes, research and design notes
evals/            activation, traversal, output and compression-ablation fixtures
tests/            executes every shipped script
scripts/          check-sync, lint-skill, count-skill-tokens (repo tooling)
site/ remotion/   documentation site and hero-video project
.codex-plugin/    package and release metadata
```

## Validate

```bash
./scripts/check-sync
```

Runs the structure lint (frontmatter, routing, header contract, no `/Users/` paths), compiles and tests the scripts, and type-checks `assets/web`.

## Versioning

Semantic versions live in `.codex-plugin/plugin.json`, [CHANGELOG.md](CHANGELOG.md), tags and GitHub Releases, never in `SKILL.md`. Current: 0.1.0.

## Credits

Written in this repository's own words after surveying community three.js, Blender and brief-intake skills; licences, commits and what was adapted versus inspired only are in [SOURCES.md](SOURCES.md).

## License

MIT. See [LICENSE](LICENSE).
