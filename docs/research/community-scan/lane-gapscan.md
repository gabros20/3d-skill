# Lane R6 — gap scan (Spline · splats/XR · generative 3D · CAD/print · R3F+Next · art direction · dissent)

Compiled 2026-10-16 via `npx skills find`, `ghrelay`, `xrelay` (read-only), plus `curl` on vendor docs. Nothing installed, no downloaded script run. Grades: [V] vendor/official · [B] measured · [P] practitioner/metadata · [U] unverified. Sources: `sources/gapscan/<owner>__<repo>__<skill>/` (each with SOURCE.txt: URL, commit, date, licence). Tool note: `ghrelay read` truncates at 6,000 chars unless `--max-chars` is set.

## 1. Queries and hits

- **skills.sh, 31 queries (6 first, 25 more).** Spline: only 3D-web-experience mirrors and `freshtechbro@spline-interactive` (2.6K installs, repo stale since 2025-11-20). Zero hits for "spline mcp". Splats: `playableintelligence@worldlabs` 788, `mintdotgg/mint-threejs-skills` 572, `shi3z/sparkjs-skill` 9. WebXR: `freshtechbro@aframe-webxr` 2.2K, `meta-quest/agentic-tools@hz-iwsdk-webxr` 212. Generative: `meshy-dev/meshy-3d-agent` 2.1K/1.5K/908, `majidmanzarpour@threejs-3d-generator` 3.2K, `layerai@layer-3d` 2.7K, `scenario-labs@scenario-{meshy,rodin}` 335/327. CAD: `earthtojake/text-to-cad` 13.1K (cad) to 8.4K (dxf), `mitsuhiko@openscad` 988, `flowful-ai/cad-skill` 191. Scroll/camera: `avnehsbhatia/ultraui` 2–7 each, `noklip-io@theatre-js` 97. Lookdev/light: `roble3@blender-lighting` 974, `scenario-labs@scenario-blender-lighting-rendering` 236.
- **ghrelay, 19 shards + 30 follow-ups, about 150 unique repos, hydrate of about 60 named ids.** Finds the prior scan missed: `agiwhitelist/auteur` (1,042★), `AirsupHQ/machine-skill` (262★), `jaccen/Awesome-Gaussian-Skills` (162★), `instruktlabs/kiln` (276★), `mdbritt/claudecad`, `heyixuan2/bambu-studio-ai` (224★), `ahmettasdemirusa/threejs-product-skills`.
- **xrelay, 37 queries, about 800 tweets (Top, plus Latest with `--min-faves`), 8 thread reads.** Spline V2 launch, Spark 2.0 launch, text-to-cad release stream, and the Blender+Tripo "Opus orchestrates, never models" workflow.

## 2. Ranked table (metadata first)

| Area | Pick | Signals | Verdict |
|---|---|---|---|
| Spline | **Spline MCP Server + Spline Agent Skill** (vendor docs) | Spline V2 launch 2026-08-20, 1.4K likes/992 bookmarks, 112K-follower account [V][P] | **Adopt as an optional pack, only if the user has the desktop app** |
| Spline | `aydinfer/spline-mcp-server` | 85★, MIT, README says **archived, ~130 tools hit nonexistent endpoints** [V repo] | **Skip, dead** |
| Splats | `sparkjsdev/spark` (library) | 3.7K★, MIT, pushed 2026-10-15, Spark 2.0 LoD 2026-04-14 | **Adopt the library; its docs are the source** |
| Splats | `shi3z/sparkjs-skill` | 38★, no licence, 2026-04-14, 4 files | Reference only, inspire not copy |
| Splats | `ckorhonen/gsplat-optimizer` | MIT, **Metal/Apple-native, not web** | Skip for web |
| WebXR | `meta-quest/agentic-tools@hz-iwsdk-webxr` | Apache-2.0, Meta org, 219★ repo, pushed 2026-09-24 | Conditional, Quest-only; gotchas list is reusable |
| AR | `google/model-viewer` + `ahmettasdemirusa/threejs-product-skills` | 8.3K★ official; skills repo 0★, 8 days old, MIT | Library adopt; skill mine for the checklist only |
| Generative | `meshy-dev/meshy-3d-agent` | 101★, MIT, vendor, pushed 2026-10-15 | Conditional (paid key); good process rules |
| Generative | `majidmanzarpour@threejs-3d-generator` | 3.2K installs, MIT, game-oriented, needs Tripo key | Reference only (prior scan same) |
| Generative | Hunyuan3D, TRELLIS.2 | Hunyuan licence **excludes EU/UK/South Korea** [V]; TRELLIS.2 MIT, 12K★ | Licence gate item |
| CAD | `earthtojake/text-to-cad` | 20.9K★, MIT, pushed 2026-10-16, author 7.9K followers verified | **Adopt for the optional CAD pack** |
| CAD | `mdbritt/claudecad` | 1★, Apache-2.0, 2026-07 | Mine the "laws"; not a dependency |
| CAD/print | `mitsuhiko/openscad`, `flowful-ai/cad-skill`, `heyixuan2/bambu-studio-ai`, `santiagomoneta/orca-slicer` | 3.2K★ (agent-stuff), 674★ NOASSERTION, 224★ MIT, 5★ no licence | Reference; one idea each |
| R3F+Next | `oakoss/agent-skills@threejs` | 17★, no licence, 119 installs | **Warning: one snippet breaks on Next 16** |
| R3F+Next | drei `ScrollControls` docs | official [V] | Read before any drei scroll use |
| Scroll | `avnehsbhatia/ultraui@scroll-3d-camera-path-journey` | 0★, 8-day-old dump (9,185 md files), GSAP/Lenis | Numbers only, as unverified |
| Scroll | `noklip-io@theatre-js` | 1★, MIT, last push 2026-01-31 | Weak |
| Art direction | **`agiwhitelist/auteur`** | 1,042★, MIT, created 2026-07-11, pushed 2026-08-06 | **Adopt as method source** |
| Art direction | `AirsupHQ/machine-skill` | 262★, MIT, created 2026-10-12 | Mine the critic loop |
| Lookdev | `RobLe3/cc-blender-skill` lighting/cameras | 98★ MIT, pushed 2026-10-12 | Reference for recipes |

## 3. Finalist outlines

### 3.1 Spline MCP Server + Spline Agent Skill — official [V]
- **Link:** https://docs.spline.design/generate/spline-mcp-server · https://docs.spline.design/generate/spline-agent-skill (saved in `sources/gapscan/splinetool__docs__spline-mcp-and-skill/`). The SKILL.md itself sits in a **private repo** (`splinetool/spline-mono`, `packages/mcp/skill/SKILL.md`); GitHub returns 404, so it was not retrievable. The docs page describes it.
- **Install:** the MCP ships **inside the Spline desktop app** (macOS/Windows). The app auto-registers itself in `~/.claude.json`, Claude Desktop, Cursor, VS Code, Antigravity and ChatGPT's codex. No package. Tools appear as `mcp__Spline__3d_*` and `mcp__Spline__2d_*`. It does not work from the browser.
- **What:** the agent drives the live editor: create scenes, generate models, set camera, capture screenshots, write the Code-tab layer, plus Hana (2D) round-trip. Local over 127.0.0.1.
- **Skill outline:** when to use Spline vs hand-written three.js (framed by *who maintains it*), detect "not connected" and say so instead of silently falling back to code, route 3d_* vs 2d_*, **the `load_skill` calls each surface needs before its first edit**, and re-read the document before every edit because a human may have moved things.
- **Export practice [V, docs]:** Export > Code gives Vanilla JS (`@splinetool/runtime`), three.js (`@splinetool/loader`), React/Next.js (`react-spline`, 1.4K★ MIT, last push 2026-03-13), r3f (`r3f-spline`, 184★, **last push 2022-09, dead**). **Animations and events work only for Vanilla JS and React exports**, not three.js/r3f. Spline renders WebGPU with automatic WebGL fallback. GLB, GLTF, STL and USDZ are also export formats. Use drafts and promote one to Production. Optimize: parametric sides down, at most 3 subdivision levels, geometry compression "Performance", image compression (claimed up to 4× smaller), delete unused objects, use the Performance Panel.
- **+** The only source with an authoring contract for the tool. **−** Requires a closed desktop app and a human at the keyboard. The result is a `.splinecode` runtime scene, which cannot go through the project's gltf-transform pipeline unless exported as GLB. Launched 7 weeks ago.
- **Licence:** vendor docs, unlicensed for copying; do not copy.
- **Harvest:** (1) a decision rule for the 3D skill, "Spline when a designer will maintain the scene, three.js when engineers will"; (2) a connection check plus a "say so, don't fall back" rule; (3) the re-read-before-edit loop for any live-editor MCP (also true for Blender MCP).

### 3.2 sparkjsdev/spark + shi3z/sparkjs-skill (splats)
- **Link:** https://github.com/sparkjsdev/spark (MIT) · https://github.com/shi3z/sparkjs-skill (no licence, 2026-04-14).
- **Spark 2.0 [V, 2026-04-14 tweet, 2K likes]:** streamable level-of-detail (LoD) for 100M+ splats on **WebGL2**: continuous LoD trees, progressive `.RAD` streaming, GPU virtual-memory paging. Built on three.js. A WebGPU backend is demoed in 2026-10-12/13 posts [P], not released.
- **Skill outline:** quick-start importmap, SparkRenderer/SplatMesh/PackedSplats/ExtSplats, SDF editing, procedural splats, controls, runtime vs pre-built LoD, performance tips, Dyno shader graph, key imports. Only 8.5 KB; the references hold Dyno API and renderer options.
- **Procedure to harvest [P]:** `antialias:false` on the renderer; **splat budgets: Quest 3 about 1M, phones 1–3M, desktop 1–20M**; VR `maxStdDev √5`; prefer pre-built LoD over runtime LoD; formats ply/spz/splat/ksplat/sog/rad (prefer spz/rad for web delivery).
- **−** The skill pins three 0.180 and Spark 2.0.0 from CDN importmaps. Verify versions before use. Not R3F-specific; no drei wrapper was found.
- **Optional-pack verdict:** write a short "splats" reference from the Spark docs, not from the skill. Add SuperSplat (PlayCanvas, 10.4K★, MIT) for inspect/edit/optimize (from a tweet list, not read).

### 3.3 model-viewer AR (`ahmettasdemirusa/threejs-product-skills`, MIT)
- **Outline:** `<model-viewer>` minimal embed, attributes, real-world scale, variants, custom AR button, platform notes, verify. Siblings: three.js product viewer, product configurator, 360 spin.
- **Harvest [P], not cross-checked against the official model-viewer docs:**
  - AR shows the glTF at its **size in metres**; a mug exported at 9.5 units is 9.5 m. Check with `gltf-transform inspect`; fix in the source, never with CSS.
  - Android uses WebXR or Scene Viewer; iOS uses Quick Look and needs a USDZ (provided or generated); no AR button on desktop; HTTPS; MIME types `model/gltf-binary` and `model/vnd.usdz+zip`.
  - Product-page budget: model under 2–3 MB, about 100k triangles, textures at most 2048² KTX2/WebP, about 50 draw calls, **idle GPU about 0 (render on demand)**.
  - Configurator rule: **material names are the contract**; colour by name, swap `map` with the same UVs, `KHR_materials_variants` for designed variants, never non-uniform scale.
  - Common mistakes: mixed three versions, no environment map, uncapped DPR, fixed camera (frame by bounding box), cm-vs-m units.
- **−** 0★, one week old, single author; a template skill. Mine the checklist.

### 3.4 earthtojake/text-to-cad (CAD)
- **Link:** https://github.com/earthtojake/text-to-cad · installs via the Claude/Codex/Cursor/Gemini plugin marketplaces; many sub-skills (cad, step-parts, sdf, urdf, srdf, sendcutsend, cad-viewer, gcode, bambu-labs, dxf). 13.1K installs on `cad`.
- **Outline (`skills/cad/SKILL.md`, 11 KB):** start-with-the-task routing table, setup and paths, create/edit a model (build123d Python, decorated models), mesh exports (`@stl/@threemf/@glb`), prompt references and inspection (`read_scene`, `scene.resolve(ref)`), verify and hand off.
- **Harvest:** check from the *requested* dimensions, clearances and topology, not from "it built"; **report units, thresholds, untested requirements; a failed computation is not a pass**; render a snapshot of the real artifact (`cadgen step snapshot`) and read it yourself, never rely on the viewer; do not add STEP just to satisfy the workflow.
- **Signals [P]:** 20.9K★ in 6 months, MIT, releases every 1–3 weeks, author active; a 1,500-part "gauntlet loop" demo is promotional [U].
- **−** Heavy (2,932 files incl. an app and viewer); relevant only for the optional CAD/print pack. Telemetry section exists; read it.

### 3.5 mdbritt/claudecad + flowful-ai/cad-skill + mitsuhiko/openscad + bambu-studio-ai (CAD/print rules)
- **claudecad (Apache-2.0, 1★):** the best *verification laws*. Dimensions only in `params.py`; **never show renders of geometry that failed verification; verification is ground truth, renders are not evidence; fix the geometry, never the check**. OCCT construction laws, each backed by a dated spec: twisted tubes only as two overlapping half-loop lofts; cavities as subtracted blocks, never shell/thicken; avoid coincident faces and **overlap cuts about 0.5 mm** or you get non-manifold seams; `is_valid` is necessary, not sufficient. Mechanisms are proven with *constructed states*, not simulation.
- **flowful cad-skill (674★, NOASSERTION):** show-as-you-go phases (base shape, features, final); **research real-world dimensions on the web before writing geometry** (1–2 mm off makes a part unusable); CadQuery needs Python 3.10–3.12; baseline print recipe "PLA, 0.2 mm, 2 walls, 15% gyroid, no supports".
- **mitsuhiko openscad (Apache-2.0):** multi-angle preview (6 views), then *look at every image* before declaring done; `--export-stl`; parameter extraction.
- **bambu-studio-ai (MIT):** **the user starts the print, never the agent**; `analyze --repair` on every model including downloads (wrong units, floating parts, thin walls); preview before opening the slicer; a 60+ body warning is usually harmless.
- **orca-slicer (no licence):** never give settings without printer/firmware/filament; never write G-code without the firmware; 11-point model checklist.
- **Pattern for the 3D skill:** verify numerically, then look, then report; a physical-action approval gate.

### 3.6 agiwhitelist/auteur — art direction and scroll-video (best find of the scan)
- **Link / install:** https://github.com/agiwhitelist/auteur (MIT) · `skills.sh.json`, plugin marketplace.
- **Outline:** SKILL.md (20 KB): non-negotiables, 14 banned patterns, critical numbers, routing, commit-sheet before any code, phases, verification, weak-model note. References: `taste`, `assets`, `scroll-flight`, `scroll-cinema`, `motion`, `verify`, `recon`, `system`, templates (`CINEMA-QA`, `COMMIT-SHEET`, `STORYBOARD`), scripts `slopscan`, `shoot`, `motionqa`, `systemscan`.
- **Harvest [P]:**
  - **Commit art direction in writing before markup:** one hue, one type system, a motion budget, named anti-references.
  - **Fullscreen passes (bloom, grain, DoF) are priced per pixel, not per object.** A perf number only counts at **DPR 2 on a production build**. Its measured example: 6/20/20 fps headless vs 53/53/54 headed, so a headless number is a floor, never a verdict. The dev server costs about 2× per frame. Quote "minFps 57 @4× CPU, 1440×900@2x, production build".
  - **Scroll-scrubbed video, directly relevant to `ScrubStage`:** encode with a tiny GOP (`-g 8 -keyint_min 8 -sc_threshold 0 -crf 20 -an -movflags +faststart`), a mobile sibling at 720p `-g 4`, drop to `-g 1` (all-intra) for low-end phones. Load clips as Blobs, not byte-range. Prime muted videos on first touch (iOS paints no seeked frame otherwise). iOS Low Power Mode kills scrubbing, so fall back to stills with crossfades. Coalesce seeks. Tier by screen short side (≤600 px = phone), never UA. Ignore height-only resizes. Seam QA by SSIM between clip end and next start (≥0.90 pass, <0.75 fail, regenerate). **Image-to-video models barely move the camera; the scroll-dolly does the travelling.**
  - Motion budget: at most 3 scroll-trigger pattern families per page, one primary peak; `prefers-reduced-motion` is an alternative direction, not zero.
  - Source before you generate: CC0 meshes, a 512×256 HDRI is enough once PMREM blurs it, textures 1024 albedo/ARM and 512 normal, record licences in a ledger.
  - Verification: slop scanner exits 0, screenshots at 390/768/1440 *all looked at*, numeric rubric, QA sheet with PASS on every row.
- **Signals:** 1,042★, MIT, 49 files; **three months old**, one maintainer [P].
- **−** It is GSAP/ScrollTrigger-centric (its banned list names GSAP as an acceptable scroll API), so override with `docs/MOTION-DESIGN-SYSTEM.md`. Heavy toolchain (codex/grok/agy CLIs, MiniMax). Several scripts call external image/video services; review `Network access` section before any use.

### 3.7 AirsupHQ/machine-skill and RobLe3 lighting/cameras (lookdev)
- **machine-skill (MIT, 4 days old):** "the bar" list of failures (missing expected part, floating or clipping, one grey, typed-in numbers, hollow cutaway, ugly first frame); every part a closed solid; metres, Y-up; material presets with measured reflectance ("never one grey"); **at least four review rounds** (whole, cutaway, exploded, two joint close-ups, film stills) judged against real product photography.
- **RobLe3 (MIT, 98★):** focal cheat sheet (24 mm spectacle, 50 mm neutral, 85 mm intimacy, 100–135 mm hero product, 200+ mm compressed); lighting decision tree (studio: three-point plus HDRI fill 0.3; "unsure": three-point with HDRI grounding); bbox-aware hero camera; **camera guard before every render**; EEVEE engine name differs by version (≤4.1 `BLENDER_EEVEE`, 4.2 `BLENDER_EEVEE_NEXT`, ≥5.0 `BLENDER_EEVEE`). Blender-side only; the numbers need translating to three.js.

### 3.8 Generative 3D: meshy-3d-agent and the workflow evidence
- **meshy-dev/meshy-3d-agent (MIT, vendor):** 3 skills (generation, printing, openclaw), a CLI with `--output-schema v1 --format json`. Rules worth keeping: **submit once with `create --async`, keep the task ID, `wait` on it; a timeout or unknown submission does not authorise another paid create**; propose paid reruns before spending; inspect a preview, but "a rendered image does not establish topology quality".
- **Workflow evidence [P] (@rewind02, 2026-10-15, 492 likes):** Tripo makes the model, **Opus checks and fixes it; never let Opus model from scratch**. Steps: 4-view A-pose sheet, generate parts separately (up to 25k quads each), auto-rig, export GLB with animation, **ask Opus to inspect only ("don't fix anything yet")**, then fix the findings, decimate under 40k triangles, compare rest pose to the original. @shion_takk (2026-10-16): requirements first; classify each object as bpy-built / Tripo HD / Tripo SM; physics-sanity pass (no floating or interpenetrating objects); "stop improvising, follow the catalogue".
- **Licence gate:** Hunyuan3D 2.1 community licence **does not apply in the EU, UK or South Korea** [V, LICENSE text read; 2.0 not checked]. TRELLIS and TRELLIS.2 are MIT. `stable-fast-3d` is NOASSERTION. Check before recommending to an EU-based client.
- **Gap:** no independent, unsponsored comparison. The one measured-looking X ranking (100+ runs) contradicts itself across its own posts and ends with a Meshy referral link, so treat it as an ad [U].

### 3.9 R3F + Next.js, scroll camera paths
- **oakoss `r3f-patterns` (no licence):** covers `'use client'`, PPR with `<Suspense>`, and a `dynamic(..., {ssr:false})` snippet **written without a client boundary**. Next's lazy-loading docs say [V] "`ssr: false` option will only work for Client Components"; in a Server Component page this errors on Next 15+/16. Rule: wrap `dynamic` in a `'use client'` file.
- **drei ScrollControls [V]:** it creates **its own HTML scroll container in front of the canvas** (props `pages`, `distance`, `damping` default 0.2 s, `maxSpeed`, `prepend`); `useScroll()` gives `offset`, `range`, `curve`, `visible`. This is a second scroll owner, so it conflicts with a page that has native scroll plus Motion `useScroll`. For this repo, prefer native scroll driving a progress value and let the canvas read it.
- **pmndrs/react-three-next** (2.9K★): last push 2024-06-21, pages-router era; stale.
- **UltraUI camera-path skill (MIT, 0★):** CatmullRomCurve3 with a *separate look-at path* (never lookAt your own position), 1,000 pre-sampled points (500 minimum), FOV 60, DPR cap 2, fog 0.005–0.02 (never above 0.03), at least 5 control points and one lateral or vertical curve, test the path against geometry, waypoint text needs a backdrop. All numbers are unmeasured taste [U]. It claims "three.js core about 45 KB gzipped", which is wrong by a large factor [U]. It uses `gsap.ticker` as the render loop and 5000vh of scroll.
- **Theatre.js (noklip, MIT, stale since 2026-01):** studio only in dev; ship exported state JSON; unique object keys; add the R3F extension. Its dev guard uses `import.meta.env.DEV` (Vite); under Next use `process.env.NODE_ENV`. No scroll-binding guidance.

## 4. Dissent on X (practitioners, read-only)

- **@VoxelKei (28K followers, 2026-04-29, 673 likes):** Claude Code driving Blender on their own model, great plan, then "90 minutes and garbage" in the modelling phase. Replies agree ("had a feeling"). A reply says only top-tier models work on CAD, "Sonnet isn't enough".
- **@Kizuno18 (2026-10-09):** text models lack spatial mesh intuition and emit disconnected primitives rather than continuous topology in `bpy`. Low reach [U], but matches the "inspect and fix, don't model from scratch" workflow above.
- **@vladkrutenyuk (2026-09-19):** the problem with AI three.js is output you cannot modify; remedy is an editable scene behind an MCP. Same logic as Spline MCP.
- **@Alex_Vainshtein (2026-10-12):** getting a model is easy; fixing geometry, materials, animation and integration is the hard part; asks for a generate, inspect, repair pipeline.
- **@jessedeansquire (2026-10-15):** AI-looking 3D video with flicker and mesh persistence. About a video, not code.
- **@bleak_freq (2026-10-16):** "a few months ago Claude struggled to draw primitives with the Blender MCP" — capability moved fast, so date any failure claim.
- **No measured dissent found** on "AI slop 3D" topology or perf for web scenes. The strongest dissent is workflow-shaped. Everything above is [P].

## 5. Gaps

1. No official Spline SKILL.md retrievable (private repo); only docs descriptions.
2. No agent skill for R3F+Next.js App Router that is verified against Next 16; no skill for drei `View`, scroll-bound camera with Motion, or Next 16 `'use client'` boundaries.
3. No Spark/R3F bridge skill; no splat-to-web compression guidance beyond Spark's own docs.
4. No independent generative-3D benchmark; the retopology "ranking" is sponsored.
5. Not read: `scenario-labs@scenario-{meshy,rodin,sparc3d}`, `calesthio@tripo-3d`, `layerai@layer-3d`, `kevinbadi@blender-product-polish`, `instruktlabs/kiln` beyond README, `playcanvas/editor-mcp-server`, `jaccen/Awesome-Gaussian-Skills` router.
6. `xrelay` Round-2 Latest queries with `--min-faves 5` returned only 16 tweets; X coverage of dissent is thin.
