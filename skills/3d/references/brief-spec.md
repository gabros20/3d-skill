# Brief Spec

Purpose: Define the production brief, storyboard, shot list, scroll map and the canonical `shots.json` that preview and render scripts read.

Read when:
- Writing or revising `.3d/brief.md` after intake is approved.
- Planning shots, a scroll map or a camera path, or producing `.3d/shots.json`.

Skip when:
- Still gathering requirements (→ [intake-grill](intake-grill.md)).
- Choosing the pipeline for a target use (→ [brief-approach](brief-approach.md)).
- Term definitions (→ [brief-lexicon](brief-lexicon.md)).

Inputs:
- The approved restated brief, `.3d/reference-spec.json` if any, `.3d/capabilities.md`, project budgets from `3D.md`.

Produces:
- `.3d/brief.md` (template `assets/templates/brief.md`), `.3d/shots.json` (example `assets/templates/shots.json`).

## Contents

- Brief sections · Storyboard ladder · Shot fields · Scroll map · Acceptance tests · shots.json · Versioning

## Brief sections

Use `assets/templates/brief.md`. Prose is the source of truth; every section either holds a decision or says `[assumed]`.

1. Logline and thesis (about 12 words: what the viewer feels or does)
2. Use and audience (use code, placement, device, distance, autoplay or driven)
3. Subject and truth (asset source, fidelity rules, claims that must be true, do-not-invent list)
4. Style and references (chosen route, reference ledger by mechanism adopted, anti-patterns)
5. World (environment, set dressing, scale cues, ground, backdrop)
6. Camera (aspects, lens convention, per-shot size/angle/height/lens/move, safe areas)
7. Light and colour (setup per beat, palette with roles, tone mapping, brand-locked hex)
8. Materials (per-asset PBR sheet, exact-finish list)
9. Motion (beats, timing, easing character, loop rule, idle vs triggered, reduced-motion alternative)
10. FX and interaction (effects with purpose; inputs and responses)
11. Deliverables and budgets (files, formats, sizes, fps; budgets resolve to [shared-performance](shared-performance.md) defaults unless 3D.md overrides)
12. Pipeline (strategy from [brief-approach](brief-approach.md), stages, owner, fallback ladder)
13. Acceptance tests (below)
14. Assumptions, risks, Out of scope, decision log

## Storyboard ladder

Use the lowest fidelity that answers the open question: beat board (6-12 panels) → shot board → animatic (timed) → greybox previs with the real camera → techvis (lens, rig, path diagrams). For web, greybox previs is usually the right rung: build `shots.json` first and capture it ([shared-preview](shared-preview.md)).

Beats run hook → setup → reveal or proof → payoff or call to action. Give each a viewer question ("Where are we? What changed? Why believe it? What now?"), then shots. One dominant subject action and one dominant camera idea per shot.

## Shot fields

One row per shot in the brief: ID · beat · duration (seconds, or scroll range) · frame (size, subject placement, fg/mid/bg) · camera (distance, height, angle, roll, lens mm FF-equivalent, focus target) · move (type, path, easing, end frame) · subject action · light state · hero material state · FX · continuity anchors (screen direction, prop state, palette) · audio · review target (2-3 pass conditions).

Rules: state height and angle separately; lens as full-frame equivalent; keep the camera locked unless the move has a job; write review notes against a shot ID and time, never "feels off".

## Scroll map

For SCROLL work add a table, ranges as progress 0-1 of the pinned scene:

| range | beat | camera (shot id) | object state | light | copy |
|---|---|---|---|---|---|

Plus a tempo map: rests, accents, and the maximum number of groups moving at once. Ownership of scroll, pin and normalisation is in [scroll-conductor](scroll-conductor.md); the map only says what state exists at each progress value.

## Acceptance tests

Binary: file size within budget; target fps on the named device for 10 s; reduced-motion path renders a static composition; poster equals the first real frame; every shot frames the hero per the board; brand hex within tolerance; no generated text. Subjective, with a named reviewer: thesis reads in 5 s; silhouette readable; materials read as specified. Verification mechanics: [shared-verification](shared-verification.md).

## shots.json

Canonical, schema `shots.v1`. Read by `scripts/preview capture --shots .3d/shots.json` and `assets/blender/render_shots.py --shots`. Example: `assets/templates/shots.json`.

```json
{ "schema": "shots.v1", "aspect": "16:9", "fps": 30,
  "shots": [ { "id": "S01", "purpose": "establish product", "focal_mm": 50,
    "position": [2.2, 1.2, 3.4], "target": [0, 0.4, 0], "roll_deg": 0,
    "duration_s": 3, "scroll": [0, 0.25], "ease": "inOut",
    "to": { "position": [1.4, 1.0, 2.6] }, "notes": "slow push-in" } ] }
```

| Field | Rule |
|---|---|
| `schema` | `"shots.v1"` |
| `aspect` | `"W:H"` string, shared by all shots; `fps` integer (video renders only) |
| `id` | unique, matches `^[A-Za-z0-9_-]+$`; used for filenames (`<id>.png`) |
| `purpose` | one line, beat-linked |
| `focal_mm` xor `fov` | exactly one. `focal_mm` is full-frame equivalent (36×24 sensor); `fov` is vertical degrees. See [refspec-mapping](refspec-mapping.md) |
| `position`, `target` | `[x, y, z]` metres, **three.js and glTF axes: Y up, camera looks down -Z by default**. Blender scripts convert to Z-up; never pre-convert |
| `roll_deg` | optional, default 0 |
| `duration_s` | optional; required for video renders |
| `scroll` | optional `[start, end]` progress 0-1; ranges ordered and non-overlapping |
| `ease` | `linear` \| `in` \| `out` \| `inOut`; default `inOut` |
| `to` | optional end pose: any of `position`, `target`, `focal_mm`/`fov`, `roll_deg`; omitted keys hold. Without `to` the shot is a held frame |
| `notes` | free text, never parsed |

Validate: `python3 -m json.tool .3d/shots.json`; every shot has one lens key, 3-number vectors, and a `scroll` or `duration_s` when the use is SCROLL or VIDEO. Orthographic shots add `ortho_height` (world units) in place of the lens key.

## Versioning

After approval, edits are a new brief version (`v2`, date) with a decision-log line and, when shots change, a `preview new-version --note`. Never rewrite an approved brief in place.

## Traps

- Specifying "low angle" without a height.
- Camera positions in Blender axes inside `shots.json`.
- A scroll map that never states the reduced-motion composition.
