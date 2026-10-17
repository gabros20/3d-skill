# Docs index

Six documents cover using `3d`; the research folder (linked at the bottom) covers why the pack is
built the way it is. Each doc has one job. Read in this order the first time, then jump to whichever
answers your question.

| Doc | Type | Answers |
|---|---|---|
| [installation.md](installation.md) | How-to | How do I install it, which tools does it want, and how do I verify, update and remove it? |
| [loop.md](loop.md) | Explanation / reference | What are the seven stages, which artifacts and schemas does each write, and where are the gates? |
| [areas.md](areas.md) | Reference | What are the 48 references, what does each produce, and when does each route? |
| [usage.md](usage.md) | Reference / worked examples | How do I invoke it, which lane does a request take, and what does it look like on real jobs? |
| [recipes.md](recipes.md) | How-to | What is the exact prompt for `<scenario>`? |

## Reading order

1. **[installation.md](installation.md)**: install, confirm the client-native invocation responds,
   decide which optional tools to approve.
2. **[loop.md](loop.md)**: the control surface. Read it once, fully; everything else builds on it.
3. **[areas.md](areas.md)**: one area at a time, as a request routes there, or browse to see what the
   pack can do.
4. **[usage.md](usage.md)**: invocation, lanes and five worked examples end to end.
5. **[recipes.md](recipes.md)**: copy-paste prompts. Keep it open while you work.

If you only read one page, read **loop.md**.

## How the runtime and the docs relate

The runtime router is [`skills/3d/SKILL.md`](../skills/3d/SKILL.md): it picks a lane and links the
exact references to read. These docs link to the router and the references rather than restating
them, so a rule has one canonical home. Provenance and licences: [../SOURCES.md](../SOURCES.md).
Release history: [../CHANGELOG.md](../CHANGELOG.md).

## Background (not needed to use the skill)

- **[research/](research/)**: the evidence gathered before and during the build: a community scan
  ([community-scan/REPORT.md](research/community-scan/REPORT.md)), harvests per area
  ([harvest/](research/harvest/): three.js, scroll and design, Blender, brief intake, reference
  analysis, preview iteration), and the ground-truth checks
  ([web 3D](research/ground-truth-web3d.md), [Blender pipeline](research/ground-truth-blender-pipeline.md)).
- **designs/**: reserved for per-release implementation designs; none yet.

Maintainers: [../AGENTS.md](../AGENTS.md) for repository invariants,
[../CONTRIBUTING.md](../CONTRIBUTING.md) for validation and release steps,
[../evals/README.md](../evals/README.md) for the activation, traversal, output and compression
fixtures.
