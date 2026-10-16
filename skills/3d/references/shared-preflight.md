# Preflight

Purpose: A read-only detection pass that settles tools, stack, defaults and one batched install proposal before any 3D work, and records them in `3D.md`.

Read when:
- Starting 3D work in a project that has no `3D.md`, or a task would change a recorded decision (new renderer, new scroll owner, new tool).
- A script or step fails with "command not found" or a missing MCP server.

Skip when:
- `3D.md` exists and the task fits its decisions (→ the area reference).
- Debugging one symptom (→ [shared-debug](shared-debug.md)).

Inputs:
- The project root, `<skill>/scripts/capabilities` output, the agent's own MCP tool list.

Produces:
- `.3d/capabilities.md`, a filled `3D.md` (decisions, budgets, colour, scroll owner), and at most one batched question to the user.

## Contents

- Procedure
- The proposal round
- Tools
- Traps

## Procedure

1. Run `<skill>/scripts/capabilities` with the project root as the working directory (`--root DIR` is the project root, if elsewhere; never from the skill directory). Read `.3d/capabilities.md`; grep it, do not paste it. It never installs.
2. List your own MCP tools. Scripts cannot see MCP servers: a `blender` or `Spline` tool namespace is evidence, a config file mentioning one is only a hint.
3. Read the project, about two minutes, inspect before asking:

| Look at | Tells you |
|---|---|
| `package.json` | framework and version (`next`, `vite`, `astro`), `three`, `@react-three/*`, `@splinetool/*`, `@sparkjsdev/spark`, `motion`/`framer-motion`, `gsap`, `lenis`, package manager |
| `next.config.*`, `app/` vs `pages/` | App Router means the Canvas needs a Client Component |
| existing 3D: `*.glb`, `*.gltf`, `<Canvas`, `new WebGLRenderer` | brownfield: keep and adapt before replacing |
| scroll stack: `ScrollTrigger`, `new Lenis`, `ScrollControls`, `position: sticky`, `animation-timeline` | who owns scroll today (→ [scroll-conductor](scroll-conductor.md)) |
| project rules: `CLAUDE.md`, `AGENTS.md`, a MOTION or ANIMATION doc, a fluid-scale doc | rules that outrank this skill's defaults |
| `public/`, asset sizes | existing budgets already paid |

4. Decide defaults (ask only when detection is inconclusive AND the answer changes output):
   - Renderer: `WebGLRenderer`; WebGPU only if TSL or compute is needed.
   - Budgets: by target use, from [shared-performance](shared-performance.md); record the numbers.
   - Colour: view transform per [design-lookdev-presets](design-lookdev-presets.md); record it.
   - Scroll owner: the project's existing one; else per [scroll-conductor](scroll-conductor.md).
   - Preview mode: A (standalone) by default, B (live app) when the user wants it in-page ([shared-preview](shared-preview.md)).
5. Propose missing tools in ONE round (see below). Never install without explicit approval.
6. Write `3D.md` from `assets/templates/3D.md`. Record what you proposed and what the user answered.

## The proposal round

For every gap that matters to the chosen route, one line: tool, why, cost, exact command, and the fallback if declined.

```
Q1 gltf-transform (free): compress and inspect GLBs. npm i -g @gltf-transform/cli
   No: ship the Blender export uncompressed and flag the size.
Q2 ktx >= 4.4 (free): KTX2 textures. Release .pkg from KhronosGroup/KTX-Software (user runs the sudo installer)
   No: WebP/JPEG textures, larger download.
```

Cost labels: **free**, **free-account** (needs a login), **PAID**. Batch all questions; one round. `sudo`, logins and system-wide installs stay with the user (suggest `! <command>`). After a yes: run the one command, verify with `<tool> --version`, re-run `<skill>/scripts/capabilities`, note it in `3D.md`.

## Tools

| Tool | Needed for | Install hint | Cost |
|---|---|---|---|
| `node` ≥ 20 | gltf-transform, gltfpack, validator, project builds | `brew install node` or nodejs.org | free |
| `blender` ≥ 4.2 (5.2 LTS current) | modeling, headless export/render | `brew install --cask blender`; also found at `/Applications/Blender.app/Contents/MacOS/Blender` | free |
| `uv` / `uvx` | community Blender MCP | official installer from astral.sh (not `pip install uv`) | free |
| `gltf-transform` | inspect, dedup, prune, meshopt/draco, KTX2 | `npm i -g @gltf-transform/cli` | free |
| `gltfpack` | meshopt alternative | `npm i -g gltfpack` (official wasm build; no texture compression; Homebrew has no formula) | free |
| `ktx` ≥ 4.4.0 (KTX-Software; not `toktx`) | KTX2 via `gltf-transform etc1s`/`uastc` | official latest 4.x release .pkg from github.com/KhronosGroup/KTX-Software/releases: `sudo installer -pkg <file>.pkg -target /` (user runs it; not in Homebrew); confirm `ktx --version` | free |
| `ffmpeg` / `ffprobe` | `<skill>/scripts/ref-extract`, `<skill>/scripts/preview diff`, contact sheets | `brew install ffmpeg` | free |
| python `playwright` + Chrome | `preview capture` (uses the installed Chrome channel, no browser download) | `python3 -m pip install playwright` | free |
| `gltf-validator` | spec conformance | `npm i gltf-validator` (Node API, project-local; stale since 2024) | free |

MCP servers (agent checks its own tool list):

| Server | Use | Setup | Cost / caveat |
|---|---|---|---|
| Community `mcp-for-blender` (MIT) | interactive Blender building with viewport screenshots | `claude mcp add --transport stdio blender -- uvx mcp-for-blender`, then `uvx mcp-for-blender install-addon` and start it from the add-on panel. Raise the tool timeout (`timeout` in `.mcp.json`, ms) | free; executes arbitrary Python, no auth, localhost only: get consent |
| Official Blender Lab MCP (GPL-3.0) | first-party Blender control, Blender ≥ 5.1 | add-on zip plus the `blender-mcp` server from its git repo, pinned by commit SHA; follow its README | free; same consent; run only ONE Blender MCP at a time |
| Spline MCP | drive the live Spline editor | ships inside the Spline desktop app (macOS/Windows), auto-registers; not available from the browser | free-account; "not connected" means say so, never silently fall back to code |

Paid generative 3D is never part of preflight: it needs per-job approval ([asset-acquire](asset-acquire.md)).

## Traps

- Reading a config file that mentions Blender and calling the MCP "available": only a tool in your own list counts.
- Starting or restarting the user's dev server to test something: ask them ([shared-preview](shared-preview.md)).
- Proposing installs one at a time across the session instead of one round.
- Treating `toktx` as satisfying the KTX2 requirement.
