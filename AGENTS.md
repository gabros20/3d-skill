# Agent guide — 3d-skill

This repository packages one independently versioned runtime skill: `3d`. The GitHub and plugin
package name is `3d-skill`; the runtime identifier and Codex invocation remain `3d` and `$3d`.

## Ownership boundary

`3d` owns a 3D piece end to end: a request or reference → measured spec → approved brief and shots →
pipeline → build → versioned previews the user reviews → the record in `3D.md`. It covers three.js
and R3F, shaders, scroll-driven 3D (what is inside the pin), art direction, the glTF pipeline,
Blender, Spline, splats, XR and CAD routing. It does not own 2D scroll or DOM motion
(`scroll-animation`), layout scaling (`fluid-design`), image or video generation (`generate-image`,
`generate-video`) or print orchestration (`manufacturing-workflow`); it recommends those and never
invokes them. It works alone, and project rules (CLAUDE.md, a motion doc, `3D.md`) win over its defaults.

## Repository contract

- `skills/3d/SKILL.md` is the activation-time router: lane table, area route tables, universal rules,
  workflow, artifact contract.
- `skills/3d/references/` is one flat layer of area-prefixed references (`intake-`, `brief-`,
  `refspec`, `shared-`, `threejs-`, `shader-`, `scroll-`, `design-`, `asset-`, `blender-`, optional
  `spline`, `splats-xr`, `cad-print`), each directly linked from `SKILL.md`.
- `skills/3d/scripts/` (`capabilities`, `glb-report`, `ref-extract`, `preview`) and `assets/`
  (`blender/`, `web/`, `preview/`, `templates/`) are the runtime tooling; scripts are Python 3 stdlib,
  run by path with the user's project root as cwd.
- `skills/3d/agents/openai.yaml` and `.codex-plugin/plugin.json` hold discovery and release metadata.
- `tests/`, `evals/`, `scripts/`, `docs/`, `site/`, `remotion/` stay outside the installed pack.
- Decisions that shape the pack: `.orchestrate/decisions.md` and `docs/research/`.

## Change rules

1. Preserve the boundary above. Keep `SKILL.md` a router; load only the files a lane names.
2. One canonical home per rule (budgets, colour policy, glTF CLI passes, scroll ownership). Link, never restate.
3. Runtime frontmatter is `name` and `description` only; versions live in `plugin.json`, `CHANGELOG.md`, tags.
4. Never install on the user's behalf: propose with cost (free, free account, PAID). Paid generative
   jobs need approval per job. The developer's dev server is theirs; the skill's preview server serves `.3d/` only.
5. Write in this repository's own words; unlicensed sources inspire only. Update both `SOURCES.md` files.
6. No `/Users/` paths in shipped files. Every shipped script has a test.
7. Claims need evidence: do not document a capability the pack does not ship.

## Validation and release

Run after every change:

```bash
./scripts/check-sync
./scripts/count-skill-tokens
```

Release: matching `plugin.json` version and `CHANGELOG.md` heading, tag `v<version>`, GitHub Release.
Never add the version to runtime `SKILL.md`.
