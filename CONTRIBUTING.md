# Contributing

Improve routing, the loop, area references, scripts, previews or portability without adding runtime
context that a lane does not need.

## Pull-request checklist

1. Update the smallest owning file. One canonical home per rule: link, never restate (budgets live
   in `shared-performance`, colour policy in `design-lookdev-presets`, CLI passes in `asset-pipeline`).
2. A reference keeps its header (Purpose / Read when / Skip when / Inputs / Produces), a `## Contents`
   list when over 100 lines, and stays within 300–1,500 tokens (hard ceiling 2,500; split by prefix).
3. Rewrite, never copy, outside material; add its row to `SOURCES.md` and
   `skills/3d/references/SOURCES.md`. Unlicensed or NOASSERTION sources inspire only.
4. Every shipped script is executed by a test in `tests/`; say plainly what could not be exercised.
5. Add or update activation, traversal, output and compression fixtures in `evals/` affected by the change.
6. Run:

   ```bash
   ./scripts/check-sync
   ./scripts/count-skill-tokens
   ```

7. Update README and `docs/` when the public workflow changes, `AGENTS.md`/`CLAUDE.md` when
   repository invariants change, and `CHANGELOG.md` for user-visible behavior.

## Releases

Semantic versioning. Update `.codex-plugin/plugin.json` and the newest released changelog heading to
the same version, run `./scripts/check-sync`, create tag `v<version>`, and publish the matching GitHub
Release. A site- or video-only refresh still cuts a patch bump. Runtime `SKILL.md` carries no version.
