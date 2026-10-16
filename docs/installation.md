# Installation

Install the `3d` runtime skill, verify that your client discovers it, decide which optional tools to
approve, and keep repository docs, evals, tests and site assets outside the runtime context.

## Prerequisites

- An Agent Skills-compatible coding client.
- Python 3.9 or newer for the skill's scripts (standard library only).
- Everything else is optional, detected on first use, and proposed with a cost label; see
  [Tools](#tools).

## Install with skills.sh

```bash
npx skills add gabros20/3d-skill -g -y
```

Omit `-g` for a project-local installation.

## Install from a clone

```bash
git clone https://github.com/gabros20/3d-skill.git
cd 3d-skill
./install.sh codex
```

The installer accepts one target and transactionally replaces only the installed `3d` skill:

| Target | Destination |
|---|---|
| `codex` | `${CODEX_HOME:-$HOME/.codex}/skills/3d/` |
| `agents` | `~/.agents/skills/3d/` |
| `claude` | `~/.claude/skills/3d/` |
| `cursor` | `~/.cursor/skills/3d/` |
| `antigravity` | `~/.gemini/config/skills/3d/` and `~/.gemini/antigravity-cli/skills/3d/` |
| `opencode` | `~/.config/opencode/skills/3d/` |
| `grok` | `~/.grok/skills/3d/` |
| `hermes` | `~/.hermes/skills/3d/` |
| `all` | Claude, Codex and the cross-agent path |

The installer stages a complete copy before replacing an existing installation and restores the
previous copy on failure. It strips `__pycache__`. Repository-only docs, evals, tests, `site/` and
`remotion/` are not installed.

## Where scripts run

`<skill>` in the docs is the installed skill directory (for example `~/.claude/skills/3d`). **Run
scripts by path from your project root**: `<skill>/scripts/preview serve`, never from inside the skill
directory, so defaults such as `.3d` and `--root .` resolve against your project. The agent does this
for you; the rule matters when you run a script by hand.

## Tools

`<skill>/scripts/capabilities` detects these and writes `.3d/capabilities.md`. Missing ones become one
batched proposal. **The skill never installs anything without your explicit yes**; it proposes the
exact command and why, then runs it only after approval. Free, free-account and PAID are the only
cost labels, and the only PAID items are generative 3D services, approved per job and never
resubmitted on timeout.

| Tool | Used for | Cost | Install |
|---|---|---|---|
| node 20 or newer | project builds, gltf-transform, validator | free | `brew install node` |
| Blender 4.2 or newer | modeling, export, render | free | `brew install --cask blender` |
| gltf-transform | inspect, dedup, prune, meshopt, KTX2 | free | `npm i -g @gltf-transform/cli` (pin it per project: `npm i -D @gltf-transform/cli@4.5`) |
| gltfpack | meshopt alternative (optional) | free | `npm i -g gltfpack` (Homebrew has no formula) |
| KTX-Software `ktx` 4.4 or newer | KTX2 textures (not `toktx`) | free | official `.pkg` from KhronosGroup/KTX-Software releases; `sudo installer -pkg <file>.pkg -target /` **you run it** |
| ffmpeg and ffprobe | `ref-extract` frames, palette and luma; `preview diff` and `board` | free | `brew install ffmpeg` |
| Python `playwright` and Google Chrome | `<skill>/scripts/preview capture` (uses installed Chrome; no browser download) | free | `python3 -m pip install playwright` |
| uv / uvx | community Blender MCP | free | official installer from astral.sh |
| glTF validator | spec conformance (optional) | free | `npm i gltf-validator` |
| Spline desktop app | Spline MCP | free account | spline.design |
| Generative 3D services (for example Meshy) | model from text or image | PAID | per-job approval, never auto-retried |

Without `ffmpeg`, `ref-extract` says so and intake continues on vision only. Without Playwright or
Chrome, `preview capture` cannot produce evidence and says so rather than passing.

The preview viewer loads three.js from a pinned CDN (jsDelivr), so `preview serve` and `capture` need
network. There is no offline vendor mode.

## MCP setup (optional: Blender and Spline)

Headless Blender needs no MCP. Use one only to watch or steer a live scene. Both Blender servers
execute arbitrary Python, so the skill asks consent and recommends saving first. Run one at a time.

- **Community `mcp-for-blender`** (MIT, default; Blender 3.0 or newer):
  `claude mcp add --transport stdio blender -- uvx mcp-for-blender`, then
  `uvx mcp-for-blender install-addon`, enable it and start the server from the add-on panel. Raise the
  tool timeout.
- **Official Blender Lab MCP** (GPL-3.0, Blender 5.1 or newer): the add-on plus the server from
  `projects.blender.org/lab/blender_mcp`, pinned by commit SHA. PyPI `blender-mcp` is the community
  server, not this one.
- **Spline MCP**: ships inside the Spline desktop app (macOS and Windows) and registers itself; not
  available in the browser editor.

Details and troubleshooting:
[blender-channels](../skills/3d/references/blender-channels.md).

## The dev server

The skill never starts, kills or restarts your dev server. For a scene that lives in your page it
asks you to run it and give the URL. `preview serve` is separate: it serves `.3d/` only, loopback only,
on its own port (default 4173), and is stopped with `preview stop`.

## Verify

Start a new session, then invoke the client-native form:

```text
$3d plan a 3D hero for this page; I have no reference yet
```

Codex uses `$3d`; slash-command clients use `/3d`; others use an at-mention, a skill tool or natural
language. For Codex you can also check the file:

```bash
test -f "${CODEX_HOME:-$HOME/.codex}/skills/3d/SKILL.md"
```

## Update

```bash
cd 3d-skill && git pull --ff-only && ./install.sh codex
```

With skills.sh, re-run the `npx skills add` command. See [CHANGELOG.md](../CHANGELOG.md) and GitHub
Releases; versions stay out of the runtime `SKILL.md`.

## Uninstall

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/3d"
```

Repeat for each target you installed. Project files the skill wrote (`3D.md`, `.3d/`) are yours and
stay until you delete them.
