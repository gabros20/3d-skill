# R9 relay sweep: brief intake, reference analysis, preview loops (X + GitHub + skills.sh)

Run 2026-10-16. Tools: `xrelay` (X, read-only), `ghrelay` (GitHub), `npx skills find`. Nothing installed, no downloaded script run, no writes to X. Saved sources: `sources/relay2/<owner>__<repo>__<skill>/` (SKILL.md + key references + SOURCE.txt). Grades: [V] official, [B] measured, [P] practitioner, [U] unverified. Other lanes (R7 `harvest/brief-intake.md`, R8 `reference-analysis.md`, R10 `preview-iteration.md`) already hold the mattpocock, calesthio, fal and arjun988 material; this lane only adds what X and GitHub surfaced beyond them.

## 0. Verdict

- **Biggest add: a cluster of video/launch-film skills that solve the same loop the `/3d` skill needs** (brief, measured reference analysis, storyboard, build, fresh-critic loop). R7, R8 and R10 missed it because it lives in X roundups and GitHub topics, not on skills.sh. The best three are `video-sharingan` (measured camera language), `make-awesome-video` / `echris6/motion-video-kit` (gates plus independent critic loop), and the `everestchris6` prompt (all of it in one prompt).
- **Dissent worth keeping:** `mintdotgg/mint-threejs-skills` forbids opening a browser or taking screenshots without user approval. Most other sources say "always render and look". Make this a skill setting, not a hard rule.
- **X is mostly hype.** Of the 303 tweets in the corpus, about 15 had a transferable procedure. The roundup lists ("20 repos to turn Opus 5.5 into a motion studio") are Remotion/video-centred and not useful for interactive 3D. Treat them as discovery only.
- All the methods below are video-first. The part that carries to interactive scroll 3D is the **measure-then-brief** step and the **fresh critic** step. Camera speeds in %W/s need a scroll-progress analogue (see gaps).

## 1. Queries and hits

**X** (`xrelay batch`, `--product Top --limit 25`, 3.5 s gaps, 16 queries; 303 unique tweets, then 6 compact follow-up searches with `--min-faves 30 --since 2026-07-01`):

| Topic | Query themes | Useful hits |
|---|---|---|
| A brief/intake | 3d brief interview; grill-me; prompt enhancer 3D; storyboard three.js; creative brief motion; lighting vocabulary; brief agents for scroll 3D | 3 prompts with real structure (everestchris6 x2, twoclipping); roundups only otherwise |
| B reference analysis | style extraction; image to prompt; video shot breakdown; palette; recreate from video; frame-by-frame motion curve | kevin_t_ngo, hayashimon1, gkxspace, MengTo (Astra), rewind02 |
| C preview/iterate | agent screenshots three.js; visual diff; viewer/annotation; blender viewport loop; headless GPU | DanielLockyer (verify loop), rewind02 (480p preview first); headless-GPU query returned nothing |

**GitHub** (`ghrelay batch`, 30 query shards over 3 files, 12+10+8; `hydrate` of 14 finalists; `code` lane returned nothing: grep.app gave 504 and empty results for swiftshader/preserveDrawingBuffer probes). Free-text GitHub search is weak for long phrases; `topic:` shards worked best. `rank --profile ideas` then `skim`.

**skills.sh** (`npx skills find`, 12 queries): top hits `postplusai/postplus-skills@frame-extraction` (968 installs), `@shot-by-shot-analysis` (498), `calesthio/...@reference-media-analysis` (110), `software-mansion/argent@argent-screenshot-diff` (22.8K, mobile-oriented), `scottstts/...@threejs-visual-validation` (77), `majidmanzarpour/...@threejs-qa-release` (2.7K). The `3d preview viewer` query returned only DayZ modding junk. None deep-read here (R7/R8/R10 own skills.sh).

## 2. Ranked tables (metadata only, before deep read)

### A. Brief / intake / storyboard

| Rank | Repo | Stars | Licence | Why |
|---|---|---|---|---|
| 1 | NewTurn2017/make-awesome-video | 5 | MIT | intake, G1-G4 gates, 3-board options, critic loop; lineage to motion-video-kit |
| 2 | everestchris6 prompt (X, 2026-09-29 and 2026-10-13) | n/a | none stated | whole workflow as one prompt; brief block is a model intake list |
| 3 | charlie947/motion-graphics-skills | 300 | MIT | `motion-brief-writer`, `reference-to-motion`, `brand-intake`: ask-first rules |
| 4 | workspace-labs/frameflow | 0 | MIT | question protocol for client-approvable storyboards (UI, not 3D) |
| 5 | workerpro666-ctrl/aigc-director-five-lines | 2 | MIT | director-intent check before prompts; Chinese; low maturity |
| skip | AbubakrChan/product-launch-motion | 292 | MIT | strong "director stance" but 2D UI-morph film; read for technique only |

### B. Reference analysis

| Rank | Repo | Stars | Licence | Why |
|---|---|---|---|---|
| 1 | nikolasfaria/video-sharingan | 9 | MIT | measured camera/focus/look/audio, brief generator, compare gate; tests with ground truth |
| 2 | NewTurn2017/make-awesome-video `reference-analysis.md` | 5 | MIT | cuts, change peaks, contact sheet, palette, style-spec template |
| 3 | YanKaFei/art-aesthetic-vault `提示词拆解方法` | 14 | MIT | seven-layer style decomposition with word budgets |
| 4 | korovin-aa97/talkthrough-mcp | 31 | MIT | keyframes+OCR+transcript for screen recordings; not 3D-specific, not deep-read |
| licence-blocked | Technicalflight/image-prompt-reverse | 27 | AGPL-3.0 | forensic image-to-prompt contract; inspire only, do not copy |

### C. Preview / iterate

| Rank | Source | Licence | Why |
|---|---|---|---|
| 1 | echris6/motion-video-kit `gauntlet.md`, `critic-prompts.md`, `three-js-patterns.md` | MIT | independent critic rounds, frozen-time metric, ledger, lab-first components |
| 2 | SamG-Coder/ThreeBrowserStudio SKILL | MIT | render after every stage and read the image; `beautyDigest` probes, capture diff, `pixelForecast` |
| 3 | tallslab/threeforge (AGENTS.md) | MIT | `optimize --verify` pixel-parity gate (default 0.5 % changed pixels); `inspect` drives a running app |
| 4 | mintdotgg/mint-threejs-skills | MIT | opposite policy: approval-gated QA (dissent) |
| watch | cwolf-systems/playwright-perceptual (Apache-2.0, 1 star), instruktlabs/kiln (already in `sources/gapscan`) | | perceptual diff by CIEDE2000; not read |

## 3. Finalist outlines

### 3.1 video-sharingan (B1)
- **Link / install:** https://github.com/nikolasfaria/video-sharingan · commit c7c2458 (2026-10-09) · MIT · `npx skills add nikolasfaria/video-sharingan`. Needs ffmpeg + numpy + opencv-headless (so the preflight must detect ffmpeg and python deps).
- **What:** turns a reference video into numbers (cuts, camera moves with speed, easing, focus, grain/vignette/bloom, audio sync) and a recreation brief with testable do/don't rules, then compares a render against the reference with an exit-code gate. Ignores theme, palette and branding on purpose.
- **Section outline (SKILL.md):** pipeline one-liner · setup · 1 run full pipeline · 2 verify stage by stage · 3 write the brief · 4 hand to generator · 5 self-check compare · rules of thumb · files. `references/camera-language.md`: units, move vocabulary, easing fit, "never stops", pull-out detection, six traps.
- **Signals:** 9 stars, 5 days old at fetch, has tests with synthetic ground truth. Small but the only measured-analysis tool found. [P]
- **Hard-earned procedure to harvest:**
  - Order: probe, cuts, contact sheets, camera per shot, focus/look, audio, brief, render, compare. A wrong cut list poisons every per-shot number, so verify cuts on the contact sheet first.
  - Sign convention: content sliding left means camera trucks right; scale growing means push-in.
  - Compare speeds in %W/s (1080p: 19.2 px/s = 1 %W/s) or 1080p-equivalent, never raw px. A mobile reference at 21 px/s and a desktop one at 53 px/s can both be "slow".
  - Easing: integrate motion into a 0-1 curve and fit against linear, power1-3 in/out/inOut, sine; references cut mid-move, so a shot may be a slice of a longer ease (check relative speed in each third).
  - "Never stops" test: no frame under the stop threshold (2 px/s at 1080p) and slowest frame at least 25 % of the median.
  - Traps: UI reflow looks like a cut (fix: cut only if camera trajectory breaks) and like a pull-out (report windows overlapping UI events separately); per-frame scale over-reads push-ins by 5-10 % (measure over 0.5 s windows); cross-check with a second tracker (LK vs ORB agree within about 5 %); compression eats grain, dark UI edges fake a vignette.
  - Brief rules must be absolute and testable ("push-in +1.2 %/s", never "zoom a bit more"); log intentional deviations.

### 3.2 make-awesome-video + echris6/motion-video-kit (A1, C1)
- **Links:** https://github.com/NewTurn2017/make-awesome-video (f339689, 2026-10-08, MIT, Korean-language) · https://github.com/echris6/motion-video-kit (e4b1c00, 2026-10-14, MIT, 1,123 stars at fetch [P]). make-awesome-video credits the kit for the critic loop.
- **What:** gated production workflow (mode pick and intake, reference analysis G1, build setup, 3 storyboards or shot list G2, still frames per scene G3, animate and render, director-note loop G4) with an independent critic at each gate.
- **Section outline (make-awesome-video SKILL.md):** non-negotiable rules · modes · hard rule: gates · steps 0 to 6 · completion report · reference files (`critic-loop`, `reference-analysis`, `shot-decomposition`, `storyboard-template`, `three-d`, `quality-bar`, `gotchas`).
- **Procedure to harvest:**
  - Intake: collect the brief, assets and the user's raw brain-dump verbatim ("brain dump (user's own words)" section), then references.
  - Reference to **style spec** (not clone): pacing (total length, cuts, mean/min/max shot), structure by seconds, type (size as % of frame height, entry method), colour and background rules, transitions (share of hard cuts, banned types), camera/ease, UI treatment, sound, and an explicit "take / don't take" list. Name styles by vocabulary ("Swiss grid", "Apple keynote product", "Linear dark UI") because a name steers harder than a description.
  - Two references: split roles per axis (pace from A, type from B); if they collide on one axis, ask the user.
  - Storyboards: offer 3 that differ in **direction** (hero: UI vs message vs result; rhythm; hook), never three polishes of one idea. Each row: time, on-screen text, visual, beat's job, camera/motion, what carries into the next shot, block. Add "3 signature moments described without effect names", a density check (12-15 compositions per 30 s, main subject 60-85 % of frame, no hold over 0.6 s without motion), risks.
  - Critic rules: builder never judges; **new** sub-agent per judgement; give it only artifact path, brief, style spec, reference, previous report, never your reasoning or fixes; judge pixels and measurements; fix the biggest gap first; next round checks each old item FIXED / PARTLY / STILL PRESENT and hunts regressions; stop at the bar or at sub-frame polish, not at a round count (typically 2-4); keep a ledger (round, artifact, top finding, change, before/after number).
  - Measured evidence from the kit [P, one author]: a 36 s film whose builder checks all passed had about 10 s effectively frozen; frozen time went 10 s of 36 to 6.5 to 1.1 to 0.7 over four rounds; loudness range 0.6 LU to 3-4 LU. Critics said SHIP at v2, then the client found nine more issues, so keep a checklist of "checks critics missed".
  - Real defects critics caught that apply to 3D: one-frame pop when an ease-out started at full velocity (use smootherstep with tiny stagger); camera path near top-down turning a model into a flat slab with visible tiling (keep pitch 35-55 degrees and a minimum distance); wrong caption because one tween targeted two variants; overlay misaligned by about 12 px because its parent had a slow scale push.
  - three.js render contract: one seek clock where every pixel is a pure function of time, no RAF or free-running physics, `preserveDrawingBuffer`, pixel ratio 1, load textures and fonts before capture, `anchors(t)` projecting 3D points for HTML overlays; ACES tone mapping shifts background colour, so measure the rendered pixel and compensate.
  - Lab first: build each 3D component alone, render stills plus a 3-4 s proof, get a critic KEEP before integrating.

### 3.3 everestchris6 prompt (A2) [P, X]
- **Link:** https://x.com/everestchris6/status/2110426116288827709 (2026-10-13) and `/2104965415164399895` (2026-09-29, 2,849 bookmarks). Prompt text only, no licence stated; do not copy verbatim.
- **Shape:** role, brief (product plus 3-5 facts "verbatim, nothing invented", reference to beat, length/aspect/resolution, "never show" list), study (read reference frame by frame, turn into numbers: cut rhythm, camera speeds, hero motion curve, type size, stage colour; "measure it, never copy it"), build (storyboard table first; frame 0 is already the money shot; build each element in its own lab), loop (builder and critic separate, fresh each round, critic names the single biggest gap; blind test mixing own frames with the reference; "wow gate" per 3 s window), QA at 60 fps measuring frozen frames, pops, black frames. The 2026-09-29 version adds a **facts file** as the only source of numbers, "i'm away; make the calls yourself" autonomy, and a numeric pass flagging cuts via frame-to-frame change, brightness and edge detail, plus a dense 16-20 fps sheet around each transition.

### 3.4 charlie947/motion-graphics-skills (A3)
- https://github.com/charlie947/motion-graphics-skills · MIT · 300 stars · commit date 2026-10-11 (SOURCE.txt in `sources/relay2/charlie947__...`). Targets "Claude Motion", so output rules are product-specific.
- **Harvest (ask-first rules):** `motion-brief-writer`: ask at most 5 questions in one batch, only for what is essential (exact words and numbers, size, length, brand), never invent a number, label neutral defaults "Neutral default, replace with your brand", keep measured results, targets and sample data apart; output is a 3-sentence summary plus one build prompt with four states (start, change, hold, return), fixed text, `window.seek(seconds)` and reduced-motion frame, then "capture named frames, check overlap and cut-off, fix real ones, keep the earlier version". `reference-to-motion`: classify references as MOVES (pace, scene change, one idea) or LOOK (colours, fonts, feel); five-line breakdown (pace, change, type, colour/light, the one idea); precedence for look: user reference, then brief, then neutral default; prompt under 300 words, one visual idea per scene, timings sum to exact length.

### 3.5 ThreeBrowserStudio SKILL (C2)
- https://github.com/SamG-Coder/ThreeBrowserStudio · MIT · 24 stars · created 2026-08-28. Tied to a specific native app with nine `three_studio_*` MCP tools, so adopt the **discipline**, not the tool.
- **Harvest:** build in visible semantic stages (composition, primary forms, secondary, materials, lighting, dressing, animation, final camera); after every visually meaningful stage render and **look at the image**, then state the concrete observation that motivates the next stage; schema validation or successful compile is not visual verification; check a status/capabilities call before promising features; dry-run before destructive or large changes, and use a predicted-pixel-change flag so an unchanged PNG is not read as a failed patch; capture digest with luma clip/black/mean, exact pixel probes and capture-to-capture diff; an object-id pass lets probes name the entity under a pixel and reports visible/occluded/background; do not retry the same idempotency key after a timeout without re-reading the revision.

### 3.6 threeforge (C3)
- https://github.com/tallslab/threeforge · MIT · 19 stars. `optimize --verify` renders original and optimized GLB and fails if more than 0.5 % of pixels change (threshold configurable) or a clip/skin/morph is lost; `inspect <url>` drives the user's running dev server and returns a verdict by exit code. Useful as a model for a "parity gate" after glTF optimization; version-pinned to three r186, so check currency.

### 3.7 Others read
- **YanKaFei/art-aesthetic-vault** (MIT): decomposes a reference image into seven independently swappable layers (subject, style, lighting, colour, composition, medium, mood) with word budgets (lighting 4-8 words is "the best value layer"); lock layers in order: subject, style, lighting, colour, medium last; a genre name alone gives a mediocre result; negative prompts should name the genre's typical failures, not a generic junk list. Chinese-language; transferable only as a checklist.
- **product-launch-motion** (MIT): "you are the director" stance; make creative calls, log each as a DECISION and list them at the end so any can be overturned in one reply; closed-form damped-spring step response (`1-e^(-zwt)(...)`), log-zoom camera; leading/trailing edges on different springs. Conflicts with the repo's rule that transition curves are frame-fitted, not springs, so read only.
- **image-prompt-reverse** (AGPL, skip copying): observe-only rule ("only visible facts; never invent brand, logo, exact text, artist, lens model, engine, location, hidden objects"), source/alt-text/pixel-size/aspect context block, and a stdlib validator. Cite the principle only.

## 4. Practitioner threads deep-read (X, grade [P])

| Author / id | Date | Takeaway |
|---|---|---|
| hayashimon1 `2108913484805406859` (4.9K likes) | 2026-10-10 | Blender MCP scene from a 2D concept image: generate the finished-look 2D image first; blockout of boxes, then detail; procedural wear as one node group at varying strength on all materials; signs built as 2D designs rendered top-down into textures; fix by giving critique ("signage has too much margin, floor closer to the reference") and let the agent inspect close-ups; list motion details (rotation, flicker, rain angle, slow dolly) before render. Reply thread has the steps; read counts: 25 of 74 replies returned. |
| rewind02 `2109661035036635291`, `2109953507801313440` | 2026-10-12/13 | Reference image plus plain prompt "like a junior designer"; render a **480p preview first** (1080p took 1-2 h); never let the model build a chair from scratch, pull a library asset and arrange it; check animation step by step because a missed glitch costs 2 h; two fix rounds ("more detail, better materials") and "the model that handles 'add more detail' best wins". |
| kevin_t_ngo `2108582192481992922` | 2026-10-09 | Make the choreography as **code in 2D first**, then give that 2D as the reference for the 3D build, which reuses the exact timing. |
| gkxspace `2108743836348694659` | 2026-10-10 | Concept image to 32^3 sparse voxel grid plus vertex AO (the model fails at complex meshes but succeeds on voxels); animation as a function of timestamp t; Playwright frame-by-frame capture; a reply suggests stepping fixed t in-page and `toBlob` instead of screenshots to cut render time (unverified). |
| MengTo `2096510126244999366` | 2026-09-06 | Prompt pattern: "Recreate this in a single HTML file with three.js. Keep comparing it against the reference and fix any differences." Gives video, URL or code as reference and tells the agent to loop. |
| DanielLockyer `2109726478154015111` | 2026-10-12 | About 75 % of issues vanish when the agent can verify its own work; make a verification skill (Playwright open/screenshot) so it does not relearn the app each iteration. |

## 5. Dissent and conflicts

- **Verify scope:** motion-video-kit and ThreeBrowserStudio say render and look after every stage; mint-threejs-skills says the automatic minimum is build/typecheck/asset-exists and any browser, Playwright, screenshot or profiling needs explicit user approval, and desktop approval does not cover mobile. For `/3d`, offer both: default to render-and-look because the user asks for art-directed work, but expose "no-browser" mode.
- **Critic value:** critic loops are one author's measurement; the same author reports clients still found nine issues after SHIP. Critics measure only what they are asked to.
- **Springs vs fitted curves:** several skills teach spring animation; this repo's `docs/MOTION-DESIGN-SYSTEM.md` says frame-fitted curves, not springs, for the shared transitions. Do not import spring guidance.
- **Library vs scratch:** rewind02 says pull library assets, "never let the model build a chair"; gkxspace and MengTo show procedural-from-code works for stylized scenes. Choose by style target, not dogma.

## 6. Gaps

1. **No scroll-3D reference analysis exists.** Every analyser works on video of a finished piece. Nothing maps measured camera speed (%W/s) onto scroll progress, or extracts a camera path from a reference site recording. The skill will need its own mapping: speed per scroll-viewport, easing per section.
2. **No intake skill for 3D specifics** (target device, asset budget, scroll length, fallback, reduced-motion). Only generic grilling and video-brief intake.
3. **Headless WebGL capture recipe** not found on GitHub (grep.app down); R10's recipe stands untested here.
4. **`talkthrough-mcp`, `playwright-perceptual`, `postplus frame-extraction` not deep-read.** Fetch if the skill needs keyframe/OCR or CIEDE2000 diffs.
5. **Language:** make-awesome-video and art-aesthetic-vault are Korean/Chinese; harvest from my paraphrase above, not by copying.
6. **Stars are very young** (all repos created 2026-07 to 2026-10, most with under 300 stars). Re-check currency before citing, and prefer principles over file layouts.
