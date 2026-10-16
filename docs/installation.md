# Installation

Install the `3d` runtime pack from `gabros20/3d-skill`.

## Prerequisites

- An Agent Skills-compatible client.
- Python 3.9+ for the skill's scripts (standard library only). Everything else is optional and detected on first use; see [Tools](#tools).

## Install with skills.sh

```bash
npx skills add gabros20/3d-skill -g -y
```

## Clone and install

```bash
git clone https://github.com/gabros20/3d-skill.git
cd 3d-skill
./install.sh codex
```

| Argument | Destination |
|---|---|
| `codex` | `${CODEX_HOME:-$HOME/.codex}/skills/3d/` |
| `agents` | `~/.agents/skills/3d/` |
| `claude` | `~/.claude/skills/3d/` |
| `cursor` | `~/.cursor/skills/3d/` |
| `antigravity` | Gemini IDE and Antigravity CLI skill paths |
| `opencode` | `~/.config/opencode/skills/3d/` |
| `grok` | `~/.grok/skills/3d/` |
| `hermes` | `~/.hermes/skills/3d/` |
| `all` | Claude, Codex, and the cross-agent path |

The installer stages a complete copy before replacing an existing installation and restores the
previous copy on failure.

## Tools

The skill detects these (`<skill>/scripts/capabilities` writes `.3d/capabilities.md`) and proposes missing
ones with a cost label. It never installs for you. Free, free-account and PAID are the only labels;
the only PAID items are generative 3D services, approved per job.

| Tool | Used for | Cost | Install |
|---|---|---|---|
| node ≥ 20 | project builds, gltf-transform, Playwright | free | `brew install node` |
| Blender ≥ 4.2 | modeling, export, render | free | `brew install --cask blender` |
| gltf-transform | inspect, dedup, prune, meshopt, KTX2 | free | `npm i -g @gltf-transform/cli` |
| gltfpack | meshopt alternative (optional) | free | `npm i -g gltfpack` |
| KTX-Software `ktx` ≥ 4.4 | KTX2 textures (not `toktx`) | free | release `.pkg` from KhronosGroup/KTX-Software; needs `sudo` (you run it) |
| ffmpeg / ffprobe | reference frames, palette, diffs | free | `brew install ffmpeg` |
| Python `playwright` + Chrome | `<skill>/scripts/preview capture` (uses installed Chrome) | free | `python3 -m pip install playwright` |
| uv / uvx | community Blender MCP | free | astral.sh installer |
| glTF validator | spec conformance (optional) | free | `npm i gltf-validator` |
| Spline desktop app | Spline MCP | free account | spline.design |
| Generative 3D services (e.g. Meshy) | model from text or image | PAID | per-job approval, never auto-retried |

## MCP setup (optional, Blender and Spline)

Headless Blender needs no MCP. Use one only to watch or steer a live scene. Both Blender servers
execute arbitrary Python, so the skill asks for consent and recommends saving first. Run one at a time.

- **Community `mcp-for-blender`** (MIT, default; Blender 3.0+): `claude mcp add --transport stdio blender -- uvx mcp-for-blender`, then `uvx mcp-for-blender install-addon`, enable it and start the server from the add-on panel. Raise the tool timeout.
- **Official Blender Lab MCP** (GPL-3.0, Blender 5.1+): add-on plus the server from `projects.blender.org/lab/blender_mcp`, pinned by commit SHA. PyPI `blender-mcp` is the community server, not this one.
- **Spline MCP**: ships inside the Spline desktop app (macOS and Windows) and auto-registers; not available in the browser editor.

Details and troubleshooting: `skills/3d/references/blender-channels.md`.

## Verify

Start a new session and invoke `$3d` (Codex), `/3d` (slash-command clients) or ask in natural
language. For Codex:

```bash
test -f "${CODEX_HOME:-$HOME/.codex}/skills/3d/SKILL.md"
```

## Update

```bash
cd 3d-skill && git pull --ff-only && ./install.sh codex
```

See `CHANGELOG.md` and GitHub Releases. Versions stay out of runtime `SKILL.md`.

## Uninstall

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/3d"
```
