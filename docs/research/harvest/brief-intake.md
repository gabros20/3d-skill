# R7 — Brief intake, grilling, production brief (front door of `/3d`)

Date 2026-10-16. Grades: [V] official/primary · [B] measured · [P] practitioner · [U] unverified.
Finalist community copies: `docs/research/community-scan/sources/brief/<owner>__<repo>__<skill>/` (SKILL.md + SOURCE.txt).

## 0. Verdict

Front door = a **frontier-round grill** (Pocock `grilling`, MIT) with **a recommended answer on every question**, preceded by a **hypothesis + confidence line** (Osmani `interview-me`, MIT) and capped by a **restate + explicit yes** gate. It emits a **Production Brief** (section 3). Facts (repo, machine, installed tools, existing assets, brand tokens) are looked up, never asked. A vague prompt gets at most ~2 rounds / ~12 questions; a mostly-specified prompt gets 0-1 round and a "brief with assumptions" to confirm.

## 1. Grilling protocol to adopt

### 1.1 Sources synthesized
| Source | Take | Licence |
|---|---|---|
| mattpocock/skills `productivity/grilling` (commit in SOURCE.txt; `grill-me` is a one-line redirect to it) [V] | Design tree; ask the whole **frontier** per round (every decision whose prerequisites are settled); numbered questions, `❓ Q` + `➡️` recommended answer, worded so "yes" accepts; facts via sub-agent, don't block on it; done when frontier empty and user confirms | MIT |
| local `~/.claude/skills/orchestrate/references/shared-prepare.md` P1 [V local] | Same technique as the house standard; adds: ungrillable (look/feel) questions -> propose a throwaway prototype/style frame; headless = record would-be questions as assumptions; a structured ask tool fits only a closing yes/no | local |
| local `grill-me` / `grill-with-docs` | One-at-a-time variant, glossary challenge, sharpen fuzzy terms, stress-test with concrete scenarios | local (Pocock-derived) |
| addyosmani/agent-skills `interview-me` [V] | Hypothesis + **confidence %** with reason; "want vs should-want" probe ("if you didn't have to justify this to anyone, what would you want?"); restate Outcome/User/Why/Success/Constraint/**Out of scope**; "whatever you think" is delegation, not yes; stop test = can I predict the next 3 answers; no tool calls on the confirm turn | MIT |
| calesthio/generative-media-skills `storyboard-previsualization` Intake checklist [P] | Intent, Delivery, Inputs, Production path, Review path, Constraints; "lowest fidelity that answers the open question" | MIT |
| local `brainstorming` | Scope check first: decompose multi-system asks before refining details | local |

Conflict resolved: Osmani says one question at a time/no batches; Pocock says full frontier per round. For a 3D brief most dimensions are independent (palette does not depend on lens), so **frontier rounds win**; fall back to one-at-a-time only if the user's own instructions say so (shared-prepare does the same).

### 1.2 Protocol (copy into skill as `brief/GRILL.md`)
0. **Triage the prompt** (no questions yet): extract what is already stated into the 14 dimensions of section 2. Score each dimension `given / inferable / open`. Detect target use (section 3.4) - it picks defaults and the pipeline.
1. **Look up facts first** (zero user cost): repo stack (`package.json`: next/r3f/three version), existing brand tokens/fonts/colours, existing 3D assets (`*.glb *.blend *.spline`), Figma links, `.orchestrate`/preflight capability report (blender, gltf-transform, toktx...), analytics/device hints if present. Facts found are stated as "I found X" in the brief, not asked.
2. **Hypothesis line** (1 sentence + confidence %, with reason if <70%): "You want a looping, scroll-pinned chip reveal on the homepage; confidence 45%, missing: scroll vs autoplay, art style, budget."
3. **Round 1 = the gating frontier** (<=6 Qs): target use, subject truth (real product vs invented; is there CAD/Figma/photo reference), audience + the one feeling/action wanted, style anchor (pick from 3 contrastive routes, section 2 Style), hard constraints (device floor, LCP/size budget, brand, deadline, reduced-motion), delivery format. Each with `➡️` default from the use-matrix.
4. **Round 2 = what round 1 unlocked** (<=6 Qs): camera/motion beats, lighting + colour, materials, set dressing, FX, interaction. Only dimensions still `open` after defaults. Skip any dimension where the user said "your call" AND the default is low-regret (record as assumption).
5. **Ungrillable -> prototype**: look/feel the user cannot articulate (style, "cool") -> do not keep asking. Offer 3 labelled style frames (generated stills via generate-image, or a 20-minute three.js greybox with 3 lookdev presets) and ask "A, B or C + one change". One-line answer returns to the tree.
6. **Challenge pass** (inside the rounds, not extra): call out contradictions (photoreal + 60 KB budget; parallax scroll + "calm"; 4K video + mobile data), vague words (see 1.3), and unsupported claims about the real product (pins, labels, numbers).
7. **Restate + gate**: write the brief (3.1) with every assumption tagged `[assumed]` and an `Out of scope` line. Ask for an explicit yes. "Sounds good / whatever you think" -> re-ask the 2-3 open assumptions as A/B. Stop the turn on yes; do not start building in the same message.
8. **Hard cap**: max 2 rounds, 12 questions for a vague prompt; max 1 round / 6 Qs if >=60% dimensions are given. After the cap, proceed with `[assumed]` defaults and list them for veto. Headless/non-interactive: write the brief with all assumptions and mark `needs-confirmation`; never silently build.
9. **Stop condition**: frontier empty OR cap hit, AND user "yes". Osmani test as a sanity check: can I predict their answer to the next 3 questions?
10. **Record**: save `BRIEF.md` (and `brief.json`, 3.5) at project root `docs/3d/` (or user's choice); later stages read it, and acceptance tests derive from it. Changes after approval = new dated version with a decision-log line (visual-style-direction "Decision and repair log" pattern).

### 1.3 Look-up vs ask
| Look up (never ask) | Ask (user's decision) |
|---|---|
| framework/version, package manager, existing three/r3f/gsap/motion deps | target use / where it lives |
| brand colours, fonts, logo SVG, Figma frames | what feeling/action the viewer must have |
| installed DCC/CLI tools | real vs stylised; how faithful to the actual product |
| existing 3D files, textures, HDRIs in repo | budget/device floor tradeoffs (quality vs weight) |
| viewport/DPR distribution if analytics exist | deadlines, who approves, legal/claims |
| current best-practice numbers (budgets) | which of 3 style routes |

Vague-word translator (probe each; from Osmani "want vs should-want"): "cool/premium/modern/futuristic/clean/cinematic/techy" -> ask for 2 reference URLs/images or pick-from-3; "smooth" -> easing + duration + frame-rate floor; "interactive" -> which input (scroll, pointer, click, drag), what changes; "realistic" -> photoreal vs stylised-PBR, what must be exact.

## 2. Question bank (by dimension, default by target use)

Target-use codes: **HERO** web hero (autoplay/loop, above fold) · **SCROLL** scroll-driven world/pinned story · **PROD** product render/stills/turntable · **AR** WebXR/Quick Look/USDZ · **GAME** game/real-time asset · **PRINT** stills >=300 dpi · **VIDEO** pre-rendered loop/MP4 · **SPLAT** captured scene. Defaults are heuristics [P] unless marked; budgets must be re-verified against `ground-truth-web3d.md`.

| # | Dimension | Question (always with `➡️` default) | Defaults by use |
|---|---|---|---|
| 1 | Subject | What exactly is the hero object, and is it a real product (needs fidelity/claims) or an invented shape? Do you have CAD/STEP/GLB/photos/Figma? | all: real product -> use supplied geometry, stylise only materials/light; invented -> abstract primitive language, no fake specs |
| 2 | Target use | Where does it live and how is it seen (autoplay, scrubbed by scroll, orbitable, still, AR)? | infer from words: "hero"->HERO; "scroll/section/story"->SCROLL; "render/image/ad"->PROD/VIDEO |
| 3 | Audience & goal | Who watches, and what should they think/do after 5 s? (one sentence) | HERO: understand product + click CTA; SCROLL: follow narrative of 3-5 beats; PROD: desire + material truth |
| 4 | Style | Pick a route: A) photoreal studio, B) stylised matte/clay, C) dark tech/neon glass, D) editorial flat-shaded/toon... + 2 references | HERO tech: C or A-lite; PROD: A; SCROLL: one coherent route, never mix |
| 5 | Scene / set | Void/seamless, abstract environment, architectural, or in-context place? What must be IN frame vs hinted? | HERO: seamless/void + 1-2 supporting forms; SCROLL: one environment that evolves per beat; PROD: seamless cyc/infinity sweep |
| 6 | Set dressing | Supporting props/particles/graphics; any text/logo in 3D (text needs real geometry/SDF, not generated)? | HERO: <=3 supporting elements; PROD: none or 1 scale cue; no AI-generated text/logos |
| 7 | Camera | Shot sizes, angle, lens, move per beat. | HERO: 1 shot, 35-50 mm eq, slow orbit/push <=8 deg or pointer parallax; SCROLL: 1 continuous dolly/crane + 3-5 held compositions; PROD: 3 stills (hero 3/4 at 50-85 mm, detail macro, top/front orthographic-like at long lens) + 360 turntable; AR: user-controlled |
| 8 | Lighting | Studio, HDRI, or practical-driven? Time of day? Key side/mood: high-key vs low-key? | HERO: soft key 45 deg + rim + dark/gradient bg; PROD: large softbox key, strip highlights for gloss; SCROLL: lighting change tied to beat (motivated) |
| 9 | Colour | Palette (<=3 + 1 accent), contrast target, tone mapping/grade, brand-locked colours? | use brand tokens (looked up); neutral white balance for product colour accuracy; AgX/Neutral tone-map, not ACES-by-default (R3F default trap, `ground-truth-web3d.md` l.66) |
| 10 | Materials | Hero finishes: metal/glass/plastic/matte/emissive; which must be exact? | glossy = needs good env map reflections; glass = costly (transmission) -> fake with gradient/refraction-lite on mobile; emissive for chips/LEDs |
| 11 | Motion | Beats, duration, loop?, easing character, what is idle vs triggered; motion-reduction alternative? | HERO: 6-10 s seamless loop or idle breathing; SCROLL: 1 viewport-height per beat, scrubbed 1:1, eased only at pins; always a static/reduced-motion fallback |
| 12 | FX / post | Particles, bloom, DoF, grain, chromatic aberration, light shafts? | each costs fill rate; HERO: bloom (subtle) + grain max; no DoF on mobile; PROD: full post OK (offline) |
| 13 | Interaction | Pointer/gyro/scroll/click response? | HERO: pointer parallax; SCROLL: scroll only; AR: gestures |
| 14 | Sound | Any audio? | web: none by default (autoplay policy); VIDEO: optional music bed |
| 15 | Deliverables | Formats + sizes: GLB, MP4/WebM, posters, sprite sheets, USDZ, Lottie fallback? Aspect ratios (16:9, 9:16, 1:1)? | HERO: live canvas + poster image + (optional) WebM fallback; PROD: PNG/EXR + sRGB JPG; AR: GLB + USDZ |
| 16 | Budgets | Device floor, first-load weight, fps floor, LCP | defaults [P]: mid-range phone floor, 60 fps target/30 floor, 3D asset <=1-2 MB compressed (Draco/Meshopt + KTX2) for HERO, hero <=100k tris, <=100 draw calls; poster must carry LCP; lazy-load canvas after first paint |
| 17 | Constraints | Brand rules, legal claims, deadline, who approves, accessibility, browser support | `prefers-reduced-motion` -> static; WCAG 2.2 no >3 flashes/s [V w3.org/TR/WCAG22 2.3] |
| 18 | Success | How will we know it is good (acceptance tests)? | derive: framing checks per shot, fps/size budget numbers, colour deltaE-ish eyeballed vs brand, reduced-motion path works |

Probing questions for stuck users: "Which 3 websites/films/products look like what you mean?" · "Which of these 3 stills is closest?" · "What must NOT happen?" · "What is the one frame you want screenshotted?"

## 3. Brief / spec template, storyboard, strategy matrix

### 3.1 Production Brief (sections, studio lingo)
```
# <Title> - 3D Production Brief  v1  <date>  owner  status: DRAFT|APPROVED
1  Logline & thesis      one sentence; what the viewer feels/does (direction thesis, ~12 words)
2  Target use & audience  use code, placement, viewing context (device, distance, autoplay?), audience
3  Subject & truth        asset source (CAD/GLB/none), fidelity rules, claims that must be true, do-not-invent list
4  Style & references     route chosen, reference ledger (mechanism adopted, not identity copied), anti-patterns
5  World / set            environment, set dressing list, scale cues, ground plane, backdrop
6  Camera                 aspect(s), sensor/FOV convention, per-shot size/angle/height/lens/move (see 3.2), safe areas, crop obligations
7  Lighting               setup per beat: key/fill/rim/bg, softness, direction, colour temp, contrast ratio (stops), HDRI or studio rig, time of day
8  Colour                 palette (hex), role of each, tone-mapping + grade, colour-management (sRGB web / ACEScg offline), brand-locked colours
9  Materials              per-asset PBR sheet: base colour, metalness, roughness, clearcoat/transmission/emissive, maps, finish notes
10 Motion                 beat sheet (3.3), timing table, easing character, loop rules, idle vs triggered, reduced-motion alt
11 FX & post              list with purpose + budget cost; post stack order
12 Interaction            inputs and responses; scroll map (scroll% -> state)
13 Audio                  none / bed / SFX cues
14 Deliverables           files, formats, resolutions, fps, durations, aspect variants, naming, posters/fallbacks
15 Technical budgets      tris, draw calls, texture memory, file size, fps floor, DPR cap, load strategy, device floor
16 Pipeline plan          strategy from matrix 3.4 + stage list + tools + owner per stage
17 Risks & assumptions    every [assumed] item, open risks, mitigations
18 Acceptance tests       binary + subjective checks (3.6)
19 Out of scope
20 Decision & change log
```
Industry anchor: motion-design briefs share background, goals, deliverables, references, creative direction, style guide; add runtime, aspect ratios, resolutions, platforms, formats, milestones; production order brief -> concept/script -> style frames + storyboard -> animatic -> animation draft -> sound -> revisions -> export (Milanote/Taskade/Hivo templates, web search 2026-10-16 [P]). "Style frame" = still of final look; animatic = timed boards; techvis = camera/lens/rig diagrams (calesthio storyboard skill, citing Autodesk/Toon Boom [P]).

### 3.2 Shot-list fields (one row per shot; one dominant subject action + one dominant camera idea per shot [P heuristic])
`Shot ID` (S01A) · `Beat / editorial function` · `Duration (s or frames @fps)` · `Frame` (size, subject placement, fg/mid/bg) · `Camera` (distance, **height**, **angle**, roll, lens mm FF-equiv, focus target, DoF) · `Move` (type, path, cue, speed profile/ease, end frame) · `Subject action / blocking` (start mark -> end mark) · `Lighting state` (key side, ratio, colour temp, change over shot) · `Materials/hero state` (which assets, finish, emissive on/off) · `FX` · `Continuity anchors` (axis side, screen direction, prop state, palette) · `Interaction/scroll range` · `Audio` · `Budget notes` · `Review target` (2-3 pass conditions) · `Status`.
Rules: specify height AND angle (low-angle is ambiguous); distance sets perspective, focal length sets framing; state lens as FF-equivalent; keep camera locked unless a move has a job; match-on-action across cuts; write notes with shot ID + timecode, never "feels off" (calesthio cinematic-shot-direction, citing ASC/Sony/Nikon/BBC [P, sources linked in file]).

### 3.3 Beat sheet / storyboard format
Beats (hook -> setup -> reveal/proof -> payoff/CTA), each with a **viewer question** ("Where are we? What changed? Why believe? What now?"), then shots. Board fidelity ladder (use lowest that answers the open question): beat board 6-12 panels -> shot board -> animatic (timed, scratch) -> 3D previs (greybox + camera) -> techvis. For web: **scroll map table** = `scroll range | beat | camera | object state | light | copy`, plus a **tempo map** (rests, accents, max simultaneous moving groups). For gen-AI-assisted stills: continuity bible (palette, lens language, product state, forbidden changes), per-shot prompt, pass/fail; regenerate only failed shots (calesthio storyboard-previsualization [P]).

### 3.4 Target use -> pipeline strategy matrix
| Use | Primary strategy | Why / when | Cost watch |
|---|---|---|---|
| HERO live | Real-time three.js/R3F scene, compressed GLB, poster image first | interactivity, resolution-independent, brand-reactive | mobile GPU; hero tris, transmission, shadows, DPR cap |
| HERO simple | Pre-rendered WebM/MP4 (AV1/HEVC fallback) or sprite/frame sequence | zero GPU risk, photoreal (Blender Cycles), loopable | file size (budget), no interactivity, art-direct once |
| SCROLL | Real-time scene driven by scroll progress (stack-agnostic), OR scrubbed pre-rendered frames/video when photoreal + no interactivity | scroll scrub of video needs keyframe-dense encode; real-time allows camera freedom | pin/scrub jank on iOS, memory, reduced-motion |
| PROD stills/turntable | Offline render (Blender Cycles/EEVEE) in sRGB/ACEScg, comp tweaks | highest fidelity, full post, no budget | render time; keep scene source for reshoots |
| Spline | Spline scene embed or `@splinetool/react-spline` | non-engineer-editable, fast prototype, designer-owned | runtime weight, limited perf control; flag as optional |
| SPLAT | Gaussian-splat viewer (capture -> clean -> compress) | real places/objects captured from photos/video, no modelling | file size, no relighting, no animation of rigid parts; static-camera-ish |
| AR | glTF/GLB -> USDZ (Quick Look) / WebXR | mobile try-in-space | tri/texture caps (tens of k tris, <~5-10 MB [U - verify]), true-scale units, PBR only |
| GAME | Engine-native pipeline (not this skill's core) | route out | -- |
| PRINT | Offline render at 300 dpi+, 16-bit, ICC | fidelity | -- |
Rule: choose pre-rendered when interactivity is not required AND budget/device risk is high; choose real-time when the viewer drives camera/state, when assets must be brand-reactive, or when resolution independence matters. Always state the **fallback ladder**: live -> poster/video -> static.

Production pipeline stages (shared vocabulary; sources differ on grouping): **brief -> previs -> asset build (model -> texture/lookdev -> rig) -> layout -> animation -> FX -> lighting -> render -> comp -> grade -> deliver** (Pixune, CGHeven, Frender VFX pipeline articles, 2026-10-16 [P]). For web 3D collapse to: brief -> style frames/lookdev -> greybox+camera previs -> asset prep (decimate, UV, bake, compress) -> scene assembly -> motion -> light/post tune -> perf pass -> QA vs acceptance tests.

### 3.5 Machine-readable twin (`brief.json`) - optional
Mirror the headline fields: `use, aspect[], fps, durationSec, palette{}, tonemap, shots[{id, beat, sizeAngle, lensMm, move, durSec, scrollRange}], budgets{tris, drawCalls, textureMB, fileMB, fpsFloor, dprMax}, fallbacks[], assumptions[]`. Prose is the source of truth; ids must match (visual-style-direction rule [P]).

### 3.6 Acceptance criteria patterns
Binary: file size <= N; 60 fps on device X for 10 s; reduced-motion path renders static composition; poster = first real frame; every shot frames hero per board; no pixel-exact text from generation; brand hex within tolerance. Subjective (named reviewer): thesis read in 5 s; silhouette readable; material reads as intended; one cut to check geography. Five review gates (visual-style-direction [P]): brief fidelity, originality/rights, system coherence, production resilience (all ratios, thumbnail size), accessibility/continuity.

## 4. Lexicon (only terms that change output)

**Shot size** (by information, not prestige): EWS/establishing (geography, scale) · wide/full · medium-wide · medium · MCU · CU (detail) · ECU/insert (one decisive feature). For objects name visible surfaces + scale cue.
**Angle/height/roll**: eye-level / low / high / overhead / worm's-eye; three-quarter (3/4 front, product hero default); profile; roll = horizon tilt (Dutch) keep level unless motivated. Height and angle are independent.
**Lens (FF-equiv)**: 14-24 ultrawide (distortion, drama, close approach) · 28-35 wide (environment) · 50 normal · 85-135 portrait/hero compression · 150+ tele flat. Perspective is set by camera POSITION; longer lens + farther camera flattens. Web: three.js FOV = vertical angle; convert from mm with sensor 36x24: `fov = 2*atan(12/f)`. Keep DoF off by default on mobile.
**Moves**: static/locked · pan/tilt (pivot) · dolly/push-in/pull-out (translate along axis, parallax) · truck/pedestal · crane/jib (arc + height) · orbit/turntable (around subject) · handheld (noise) · whip · rack focus · dolly zoom. Motivation first (ASC); speed profile = ease-in-out for moves, linear for turntable loops.
**Lighting**: key (main, shapes form) · fill (shadow lift; ratio in stops; negative fill = flag/black) · rim/back/kicker (edge separation) · background light · practicals (in-frame sources) · hard vs soft = source SIZE, not power · high-key vs low-key · colour temperature (3200 K tungsten warm; 5600 K daylight; mixed warm/cool = depth) · inverse-square falloff · three-point = starting point only; describe the visible result. Product: gloss needs controlled reflections (strip softboxes, black flags); transparent needs edge/backlight (Rosco/ARRI/Broncolor via calesthio lighting-direction [P]). Real-time: HDRI/IBL for ambient+reflection, one directional for shadow, baked AO.
**Colour**: palette roles (dominant 60 / support 30 / accent 10) · value structure (squint test) · tone mapping (AgX, Neutral/Khronos PBR Neutral for product accuracy, ACES = filmic punch/desaturates) · colour space (sRGB web, linear working, ACEScg offline) · grade (lift/gamma/gain, LUT) · bloom/glow only on emissive.
**Materials (PBR metal-rough)**: base colour · metalness (0/1 mostly) · roughness (gloss<->matte) · normal/bump · AO · emissive · clearcoat · transmission/IOR (glass; expensive) · sheen · anisotropy (brushed metal) · subsurface (skin/wax) · finishes: anodised, brushed, satin, polished, frosted, matte rubber.
**Animation principles** (Disney 12, the ones that matter for objects/camera): timing & spacing · slow-in/slow-out (ease) · arcs · anticipation · follow-through/overlap/drag · staging · secondary action · squash/stretch (rare for hard products) · exaggeration (dial). Web motion: duration scales with distance/complexity; stagger; rest beats; max simultaneous groups; loop seam (first=last frame, matched velocity).
**FX terms**: particles (instanced points/sprites), volumetrics/god-rays, fog/atmospherics, bloom, DoF/bokeh, motion blur, chromatic aberration, film grain, vignette, SSAO, SSR, depth-fog, dissolve/mask reveals, wireframe/scan lines, displacement/noise, caustics (fake).
**Production words**: style frame · storyboard · animatic · previs (greybox) · techvis · lookdev · layout · plate · pass/AOV · comp · handles · hero/proxy asset · LOD · bake · retopo.

## 5. Sources, community finalists, gaps

### 5.1 Finalists (saved)
| Skill | Use | Licence |
|---|---|---|
| mattpocock/skills `grilling`, `grill-me`, `to-spec` | round/frontier protocol; spec synthesis template (no interview) | MIT |
| addyosmani/agent-skills `interview-me` | confidence, restate, stop rule | MIT |
| calesthio/generative-media-skills `cinematic-shot-direction`, `lighting-direction`, `storyboard-previsualization`, `visual-style-direction`, `production-design-direction` | shot spec, lighting vocab, board fields + intake, visual-system handoff + gates, set/props bible. Best-in-class: cites ASC, ARRI, Rosco, Sony, BBC, WCAG. Gen-AI-video slant; strip model-specific bits | MIT |
| fal-ai-community/skills `cinematography` | SCLCAM prompt order; thin, genmedia-CLI specific | none stated (inspire only) |
| arjun988/blender-skills `camera-cinematography` | Blender camera naming (`CAM_[Shot]_[Angle]`), lens table, move table | MIT |
| 101-skills/superpowers `storyboard-creation`, `product-photography` | packshot/hero rules (80-85% frame fill, 15-30 deg angle), Amazon packshot spec; inference.sh-bound | none stated (inspire only) |
Commit hashes in each SOURCE.txt; fetched 2026-10-16. Searched skills.sh with 12 query families (grill, creative brief, storyboard, shot list, cinematography, camera shots, lighting, motion design, art direction, product visualization, video prompt, requirements interview). Not deep-read: heygen-com/hyperframes (Apache-2.0; video composition, motion-oriented), leonxlnx/taste-skill (UI taste, not 3D), mbfinotti `ad-creative-brief` (ad-specific), minimax h3 prompt skills.

### 5.2 Industry / public sources
- ASC "Tools for Camera Movement", "Fresh Perspectives" (theasc.com/articles/shot-craft-*) [V/P, via calesthio]
- BBC Academy "Five Essential Shots" PDF [V via calesthio]; Sony/Nikon focal-length & perspective pages [V via calesthio]
- ARRI lighting handbook; Rosco lighting ratio/inverse-square [V via calesthio]
- Kodak aspect-ratio targets [V via calesthio]
- WCAG 2.2 section 2.3 seizures [V] https://www.w3.org/TR/WCAG22/
- VFX pipeline: pixune.com/blog/vfx-pipeline, cgheven.com, frender.com (2026-10-16) [P]
- Motion brief conventions: milanote.com/templates/motion-design/motion-design-brief, taskade motion-graphics-brief, hivo.co animation-brief [P]
- Heer & Robertson 2007 animated transitions (motion clarifies correspondence) [V via calesthio]
I did not re-fetch the ASC/ARRI/Rosco primaries; claims are as relayed in calesthio's cited MIT skills (grade [P] until re-verified).

### 5.3 Gaps for the skill writers
1. **Numeric budgets** (tris, draw calls, MB, texture size per use) are practitioner heuristics here; need the R1/R3 truth lane to supply verified numbers, esp. AR (Quick Look limits) and splat sizes.
2. **Tone-mapping default** guidance (AgX vs Neutral vs ACES) should be reconciled with R1 before being hard-coded in defaults.
3. No community skill covers the **web-3D specific brief** (scroll map, fallback ladder, LCP/poster, reduced-motion); the template here is original synthesis.
4. **Style routes**: needs a small library of 3-5 named lookdev presets (light rig + palette + material set + post) so "pick A/B/C" is cheap; each should be a runnable three.js preset (R3/R4 lanes).
5. Pre-rendered strategy details (Cycles settings, video encode for scroll scrubbing: all-intra/short GOP, AV1/HEVC/WebM) belong to R5/R4; not researched here.
6. Spline and splat rows are thin: only route-selection logic, no workflow facts.
7. Hungarian-language users: question bank is English; if the skill should grill in the user's language, the defaults table is language-neutral but needs a note.
