# Intake Grill

Purpose: Turn a 3D request into an approved brief by looking up facts, asking only the decisions that are the user's, and gating on an explicit yes.

Read when:
- A new 3D request arrives and `.3d/brief.md` is missing or not approved.
- The prompt is vague ("make it cool", "a 3D hero for the homepage") or has many open dimensions.

Skip when:
- An approved `.3d/brief.md` exists and the request fits it (→ [brief-approach](brief-approach.md) or the build area).
- The user supplied only a reference to decode: run [intake-references](intake-references.md) first, then return here with the spec. With any attached or linked reference, that pass always precedes the questions.
- A one-line fix to an existing scene (→ the area reference).

Inputs:
- The user prompt, any attached references, the project root (read-only look-ups).

Produces:
- A restated brief with `[assumed]` tags and an Out of scope line, then `.3d/brief.md` after an explicit yes ([brief-spec](brief-spec.md), template `<skill>/assets/templates/brief.md`).

## Contents

- Protocol · Look-up vs ask · Question bank · Traps

## Protocol

1. **Triage, no questions yet.** Sort the 18 dimensions below into `given` / `inferable` / `open`. Detect the target use (HERO, SCROLL, PROD, AR, GAME, PRINT, VIDEO, SPLAT): it sets defaults and the pipeline ([brief-approach](brief-approach.md)).
2. **Look up facts, then decompose references.** If any reference is attached or linked, run [intake-references](intake-references.md) first (`<skill>/scripts/ref-extract` plus vision passes) and mark the dimensions it fills `given`, evidence-tagged; ask only each reference's intent (match vs style) and the dimensions still `open`. Run `<skill>/scripts/capabilities` and read `.3d/capabilities.md`; read `package.json` (three, R3F, scroll libs, framework), brand tokens and fonts, existing `*.glb *.blend *.spline`, Figma links, `3D.md`, an existing `.3d/`. State what you found as "I found X"; never ask it.
3. **Hypothesis line**: one sentence plus confidence %, plus what is missing when under 70%. Example: "Scroll-pinned chip reveal on the homepage; 45%; unknown: scroll vs autoplay, style, budget."
4. **Round 1: the gating frontier, at most 6 questions.** Target use and placement, subject truth (real product or invented; CAD/photo/Figma available), the one feeling or action wanted, style anchor, hard constraints (device floor, weight, brand, deadline, reduced motion), deliverable formats. Pick from bank rows 1, 2, 3, 4, 15, 16/17; the bank never lets you exceed 6. Every question carries a recommended answer worded so "yes" accepts it.
5. **Round 2: what round 1 unlocked, at most 6 questions.** Camera and motion beats, lighting and colour, materials, set, FX, interaction. Only dimensions still `open` after defaults. If the user says "your call" and the default is low-regret, record `[assumed]` and move on.
6. **Cap.** Vague prompt: at most 2 rounds / 12 questions. At least 60% of dimensions `given`: 1 round / 6 questions. After the cap, proceed on `[assumed]` defaults and list them for veto.
7. **Open or ungrillable look.** When the look is open or the user cannot articulate it, stop asking. Offer THREE labelled directions that differ in direction (concept, light, palette, camera logic), never three polishes of one idea, and ask "A, B or C plus one change":
   - cheapest: three named presets from [design-lookdev-presets](design-lookdev-presets.md) on a greybox of the subject;
   - stills: if the `generate-image` skill is installed, recommend it for the 3 frames; the user runs it. Never invoke it.
8. **3D-specific items are asked or defaulted, never skipped**: device class, asset budget, scroll length (SCROLL), fallback and poster, reduced motion. Defaults resolve through `3D.md`, then [shared-performance](shared-performance.md).
   **Delegated gates**: ask once whether gates 2-4 ([brief-spec](brief-spec.md)) may be "approve on critic pass"; record the answer in `3D.md`; default no.
   **Facts file rule**: numbers (budgets, durations, sizes, prices, specs) live only in `3D.md` and the brief's facts; nothing else invents them. Label neutral defaults `[assumed]`.
9. **Challenge pass, inside the rounds.** Name contradictions (photoreal plus a 60 KB budget; parallax plus "calm"; 4K video plus mobile data), vague words (below), and claims about a real product the user has not evidenced (ports, labels, numbers).
10. **Restate and gate.** Write the brief: Outcome, Audience, Use, Style, Constraints, Deliverables, every guess tagged `[assumed]`, and `Out of scope`. Ask for an explicit yes. "Whatever you think" or "sounds good" is delegation, not approval: re-ask the 2-3 riskiest assumptions as A/B. A structured ask tool fits only this closing yes/no. End the turn on the question; start no build work in the same message.
11. **Headless (no live user).** Write the questions with recommended answers to `.3d/questions.md` and stop. Only if the user explicitly said to assume defaults: proceed on the recommended answers tagged `[assumed]`, record them in the brief, mark `status: needs-confirmation`.
12. **Record as you go.** When the user answers, mark each question resolved in `.3d/questions.md` (the answer, tagged "approved by user" or `[assumed]`) and clear its "Open questions" entry in `3D.md` in the same step. Choosing a direction A/B/C is a direction choice only; style-frame sign-off is gate 2 in [brief-spec](brief-spec.md).
13. **Save.** Save `.3d/brief.md`. After approval, changes are a new dated version plus a log line; never edit history silently.

## Look-up vs ask

| Look up, never ask | Ask, it is the user's call |
|---|---|
| framework, versions, installed tools, GPU/Blender | where it lives and how it is viewed |
| brand colours, fonts, logo SVG, Figma frames | the feeling or action wanted in 5 s |
| existing 3D files, textures, HDRIs | real vs stylised; fidelity to the actual product |
| budgets (project config in `3D.md`, else [shared-performance](shared-performance.md)) | quality vs weight trade-offs; deadline; approver; claims |

## Question bank

Default = what to recommend when the user does not care. Budgets always resolve through `3D.md` then [shared-performance](shared-performance.md); never invent numbers here.

| # | Dimension | Ask | Default by use |
|---|---|---|---|
| 1 | Subject | Hero object; real product or invented; CAD/GLB/photos? | Real: supplied geometry, stylise only light/material. Invented: abstract primitives, no fake specs |
| 2 | Target use | Where does it live; autoplay, scrubbed, orbitable, still, AR? | "hero" HERO; "scroll/story/section" SCROLL; "render/ad/image" PROD or VIDEO |
| 3 | Audience, goal | Who watches; what after 5 s? | HERO: grasp product, click; SCROLL: follow 3-5 beats; PROD: desire, material truth |
| 4 | Style | Pick A/B/C style frames; two references | One coherent route per piece; never mix |
| 5 | Scene | Void, abstract set, architecture, real place? | HERO/PROD: seamless void; SCROLL: one environment that evolves per beat |
| 6 | Set dressing | Props, particles, text or logo in 3D? | Few supporting elements; text as real geometry or HTML, never generated |
| 7 | Camera | Size, angle, height, lens, move per beat | HERO: lens per the defaults in [brief-spec](brief-spec.md), slow move or pointer parallax; SCROLL: one continuous move plus held frames; PROD: hero 3/4, detail, turntable |
| 8 | Lighting | Studio, HDRI, practical; key side; high/low key | Soft key, rim, dark or gradient ground; SCROLL: light change motivated by beat |
| 9 | Colour | Palette (≤3 plus accent), brand-locked hex, grade | Use looked-up brand tokens; policy in [design-lookdev-presets](design-lookdev-presets.md) |
| 10 | Materials | Finishes; which must be exact | Glossy needs env reflections; glass costs, fake on mobile; emissive for LEDs |
| 11 | Motion | Beats, duration, loop, easing, idle vs triggered | HERO: idle or short seamless loop; SCROLL: one viewport per beat, 1:1; always a static fallback |
| 12 | FX/post | Particles, bloom, DOF, grain, volumetrics | Subtle bloom or grain at most live; full post only offline |
| 13 | Interaction | Pointer, scroll, click, drag, gyro | HERO: pointer parallax; SCROLL: scroll only; AR: gestures |
| 14 | Audio | Any sound? | Web: none; VIDEO: optional bed |
| 15 | Deliverables | Formats, sizes, aspect ratios, posters | HERO: live canvas plus poster; PROD: PNG/EXR; AR: GLB plus USDZ |
| 16 | Budgets | Device floor, load weight, fps floor | Project config, else [shared-performance](shared-performance.md); poster carries first paint |
| 17 | Constraints | Brand rules, claims, deadline, accessibility, browsers | `prefers-reduced-motion` gets a static composition; no flashing over 3 per second |
| 18 | Success | How do we know it is good? | Per-shot framing, budget numbers, reduced-motion path works ([shared-verification](shared-verification.md)). Also set the iteration budget: critic rounds per gate (default 3, at most 2 versions per technique), optional token cap, fidelity exact / close / stylised; recorded in `3D.md` and `.3d/feasibility.json` ([realism-gate](realism-gate.md)) |

Stuck probes: "Which three sites, films or products look like it?" · "What must not happen?" · "Which one frame would you screenshot?" Vague words ("premium", "cinematic", "techy"): ask for two references or A/B/C. "Smooth": easing, duration, fps floor. "Interactive": which input, what changes. "Realistic": photoreal or stylised PBR, and what must be exact.

## Traps

- A rejected approach: see [SKILL.md](../SKILL.md) universal rule 7 (a rejected approach rejects its family).
- Asking facts you could read from the repo.
- Starting the build in the same turn as the restate.
