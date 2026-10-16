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
- `.3d/brief.md` (template `<skill>/assets/templates/brief.md`), `.3d/shots.json` (example `<skill>/assets/templates/shots.json`).

## Contents

- Brief sections · Storyboard ladder · Shot fields · Scroll map · Acceptance tests · shots.json · Versioning

## Brief sections

This file is the only place shots and the storyboard are written. It consumes the camera language and shot intent from [design-art-direction](design-art-direction.md) and turns them into rows and `.3d/shots.json`; other references link here instead of defining shots.

Use `<skill>/assets/templates/brief.md`. Prose is the source of truth; every section either holds a decision or says `[assumed]`. Numbers (budgets, durations, sizes) appear once, in section 11 and `3D.md`; other sections point there. When the look was open, record the three directions offered and the one chosen in section 4.

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
12. Pipeline (strategy from [brief-approach](brief-approach.md), stages, owner, fallback ladder, feasibility statement)
13. Acceptance tests (below)
14. Assumptions, risks, Out of scope, decision log

The brief's core (section 1 thesis and section 2 use) is binding: options, fallbacks and ladders never drop it. Changing it is a brief change the user must approve.

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

## Lens defaults by shot type

The one home for lens defaults (full-frame equivalent, vertical-24 convention). Override only with a reason in the brief.

| Shot type | Default lens |
|---|---|
| Environment, establishing, section hero in a world | 28-35 mm |
| General hero view of an object in a scene | 35-50 mm |
| Product packshot, hero 3/4 | 85-135 mm (compressed, low distortion) |
| Detail or macro insert | 85-135 mm, camera close |
| Wide drama, close approach | 14-24 mm, deliberate |
| Isometric or technical | orthographic (`ortho_height`) |

Position sets perspective, lens sets framing ([brief-lexicon](brief-lexicon.md)).

## Acceptance tests

Binary: file size within budget; target fps on the named device for 10 s; reduced-motion path renders a static composition; poster equals the first real frame; every shot frames the hero per the board; brand hex within tolerance; no generated text. Subjective, with a named reviewer: thesis reads in 5 s; silhouette readable; materials read as specified. Verification mechanics: [shared-verification](shared-verification.md).

## shots.json

Canonical, schema `shots.v1`. Read by `<skill>/scripts/preview capture --shots .3d/shots.json` and `<skill>/assets/blender/render_shots.py --shots`. Example: `<skill>/assets/templates/shots.json`.

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
| `focal_mm` \| `fov` \| `ortho_height` | exactly one. `ortho_height` is the world-unit frame height for orthographic shots. `focal_mm` is defined by a 24 mm sensor height at any aspect (`fov = 2·atan(12/f)`); `fov` is vertical degrees. See [refspec-mapping](refspec-mapping.md) |
| `position`, `target` | `[x, y, z]` metres, **three.js and glTF axes: Y up, camera looks down -Z by default**. Blender scripts convert to Z-up; never pre-convert |
| `roll_deg` | optional, default 0 |
| `duration_s` | optional; required for video renders |
| `scroll` | optional `[start, end]` progress 0-1; ranges ordered and non-overlapping |
| `t` | optional seconds, for time-driven scenes and loops; the app exposes `setTime(t)` and capture and render honour it. Use it instead of inventing scroll ranges |
| `ease` | `linear` \| `in` \| `out` \| `inOut`; default `inOut` |
| `to` | optional end pose: any of `position`, `target`, `focal_mm`/`fov`, `roll_deg`; omitted keys hold. Without `to` the shot is a held frame |
| `notes` | free text, never parsed |

Validate: `<skill>/scripts/spec-check .3d/shots.json` (exit 1 names the bad fields). Rules: every shot has one lens key, 3-number vectors, and a `scroll` or `duration_s` when the use is SCROLL or VIDEO.

## Sign-off gates

Stop for the user's explicit approval at each gate; work past a gate only on a yes. Each gate shows evidence ([shared-preview](shared-preview.md)), never a description.

| Gate | Evidence shown | Approves |
|---|---|---|
| 1 Brief | restated brief | scope, assumptions, Out of scope |
| 2 Style frames | rendered style frames of the chosen direction | the look. Picking A/B/C in the grill is a direction choice, not this gate; it passes only when rendered frames are shown and the user says yes |
| 3 Blockout | greybox captures of every `shots.json` shot | framing, beats, timing |
| 4 Lookdev | hero shots with final light and materials | light, colour, materials |
| 5 Final | full captures or render, performance numbers, fallback path | delivery |

A change that crosses an approved gate re-opens that gate. At intake the user may pre-approve gates 2-4 as "approve on critic pass"; record it in `3D.md`. Without that, a run with no live user stops at each gate.

## Video deliverable spec

For VIDEO, HERO simple and scrub uses, section 11 states:
- container and codec (H.264 with pix_fmt `yuv420p` as the safe default; AV1/VP9 WebM or HEVC as size-saving variants), resolution, fps, duration, quality target;
- colour: tagged `bt709` primaries, transfer and matrix, limited (tv) range, matching the web tone-mapping intent;
- alpha, only when the clip sits over live content: ProRes 4444 as master, VP9 WebM with alpha for Chrome/Firefox, HEVC with alpha for Safari; always a poster and a non-alpha fallback;
- loop points: first frame equals last with matched velocity, loop time in `shots.json` `notes`;
- Encode commands (including how the colour tags are actually written) live only in [scroll-video](scroll-video.md); this list states requirements, not flags. Verify the result with `ffprobe` against it before delivery.

## Versioning

After approval, edits are a new brief version (`v2`, date) with a decision-log line and, when shots change, a `preview new-version --note`. Never rewrite an approved brief in place.

## Traps

- Specifying "low angle" without a height.
- Camera positions in Blender axes inside `shots.json`.
- A scroll map that never states the reduced-motion composition.
