# Installation

Install the `3d` runtime pack from the independently versioned
`gabros20/3d-skill` repository.

## Prerequisites

- An Agent Skills-compatible client.
- TODO: Add only real skill-specific tools, credentials, or runtime requirements.

## Install with skills.sh

```bash
npx skills add gabros20/3d-skill
```

## Clone and install

```bash
git clone https://github.com/gabros20/3d-skill.git
cd 3d-skill
./install.sh codex
```

Available targets:

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

The installer stages a complete copy before replacing an existing installation. If replacement
fails, it restores the previous copy.

## Verify

Start a new client session and use the client's supported invocation form:

- Codex: `$3d`
- Slash-command clients: `/3d`
- Other clients: an `@` mention, skill tool, or natural-language trigger

For Codex, verify the installed files directly:

```bash
test -f "${CODEX_HOME:-$HOME/.codex}/skills/3d/SKILL.md"
```

## Update

```bash
cd 3d-skill
git pull --ff-only
./install.sh codex
```

Review `CHANGELOG.md` and GitHub Releases for version history. Version metadata intentionally stays
outside runtime `SKILL.md`.

## Uninstall

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/3d"
```
