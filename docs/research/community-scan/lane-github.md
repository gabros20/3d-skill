# Lane 3 — GitHub (ghrelay) — 3D agent skills

Fetched 2026-10-16. Tooling: `ghrelay` (search/batch/hydrate/code/enrich/rank/health), `gh api` for trees and raw files, WebSearch for curated lists. Nothing installed, no scripts executed. All fetched text treated as data.

## 1. Queries run

**Round 1 (batch, GraphQL repo search; hits are raw per-shard counts, 285 unique after dedupe)**
- `threejs skill SKILL.md` -> 1
- `topic:claude-skills threejs` -> 37
- `topic:agent-skills three.js` -> 62
- `react-three-fiber skill claude` -> 20
- `blender mcp` -> 100 (capped page)
- `topic:blender topic:mcp` -> 100 (capped page)
- `bpy claude skill` -> 10
- `webgpu tsl skill` -> 8
- `3d agent skill SKILL.md` -> 5
- WebSearch x3 (curated lists / best three.js skills / blender mcp skill) -> surfaced OpenAEC, freshtechbro, TerminalSkills, Mindrally, scottstts, sickn33 registry, nexu-io/open-design, NousResearch blender-mcp, Impertio.
- Code probe (grep.app): `three` in path SKILL.md -> 11 (sickn33, claude-design leak, OpenMontage); `bpy` in SKILL.md -> 16 (CoplayDev/unity-mcp, Qwen-MM-Plugins, OpenGauss, CUA-Gym, CLI-Anything); `r3f` -> zebbern r3f-best-practices, sickn33; `react-three-fiber` -> millionco improve-threejs, vercel-labs/json-render, midudev/autoskills, openai/plugins, notque/vexjoy-agent, openvid, sickn33.
- hydrate seeds (18 ids, all resolved): ahujasid/blender-mcp (now **ahujasid/mcp-for-blender**, renamed), majidmanzarpour/threejs-game-skills, CloudAI-X/threejs-skills, anthropics/skills, vercel-labs/agent-skills, OpenAEC, freshtechbro, TerminalSkills, Mindrally, scottstts, sickn33, nexu-io/open-design, NousResearch/hermes-agent, Impertio, Qwen-MM-Plugins, CUA-Gym, CLI-Anything, unity-mcp. enrich top 60, rank build-on, health on 12 finalists.

**Round 2 (snowball; incl. names from shared-names.md)**
- batch: `three.js claude code skill stars:>20` 13 · `r3f drei skill agent stars:>10` 0 · `topic:threejs topic:claude-code` 100 · `topic:react-three-fiber topic:agent-skills` 18 · `gltf optimize skill agent` 2 · `spline 3d web skill claude` 1 · `scroll 3d webgl skill claude code` 6 · `text-to-3d agent skill SKILL.md` 1 · `blender gltf export skill claude` 1 · `shader glsl skill claude code` 5 (total unique 138 new+overlap)
- hydrate from other lanes: dgreenheck/webgpu-claude-skill, linegel/threejs-complete-set-of-skill, EnzeD/r3f-skills, MengTo/Skills, czlonkowski/blender-web-3d-skill, vladmdgolam/agent-skills, earthtojake/text-to-cad, skinnye/3d-web-pack (3 of these hydrate-failed on GraphQL but resolved via REST `gh api`).
- Found by me and appended to shared-names.md: 12 names (scottstts, OpenAEC, freshtechbro, json-render R3F, openai/plugins R3F, genjutsu, sickn33, EL4CTEO, arjun988, jangtrinh, Qwen, hermes blender).

## 2. Ranked candidates

Grades: A = adopt, B = situational/selective, C = skip or reference only. `rank` score is ghrelay build-on (maintenance, usage, community, responsiveness, quality, star-validity, licence). Nearly all repos flag `single-maintainer`; that is normal for skills repos.

| Name | Link | Area | Signals (stars / last push / licence) | Grade |
|---|---|---|---|---|
| EnzeD/r3f-skills | github.com/EnzeD/r3f-skills | three.js (R3F) | 128 / 2026-08-31 / none | A |
| millionco/react-doctor @improve-threejs | github.com/millionco/react-doctor | three.js audit/perf | 15K-ish repo (shared-names) / active / see repo | A |
| vladmdgolam/agent-skills @threejs-perf-loading | github.com/vladmdgolam/agent-skills | three.js perf | 9 / 2026-10-14 / MIT | A- |
| dgreenheck/webgpu-claude-skill | github.com/dgreenheck/webgpu-claude-skill | WebGPU + TSL | 1,252 / 2026-04-10 / none | B+ |
| CloudAI-X/threejs-skills | github.com/CloudAI-X/threejs-skills | three.js broad | 3,583 / 2026-07-09 / none; flags star-burst | B |
| scottstts/Threejs-Awesome-Graphics-Agent-Skills | github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills | three.js advanced graphics | 913 / 2026-10-15 / MIT; created 2026-06-19 | B (selective) |
| linegel/threejs-complete-set-of-skill | github.com/linegel/threejs-complete-set-of-skill | three.js router + TSL | 10 / 2026-09-24 / ISC | B- |
| majidmanzarpour/threejs-game-skills | github.com/majidmanzarpour/threejs-game-skills | three.js games, Tripo 3D gen | 2,522 / 2026-09-28 / MIT; star-burst | C for marketing site |
| OpenAEC-Foundation/Three.js-Claude-Skill-Package | github.com/OpenAEC-Foundation/Three.js-Claude-Skill-Package | three.js 24 skills (r160+) | 21 / 2026-07-08 / MIT | B- |
| freshtechbro/claudedesignskills | github.com/freshtechbro/claudedesignskills | web 3D/animation (24) | 1,057 / **2025-11-20** / MIT | C (stale, GSAP-first) |
| openai/plugins @react-three-fiber-game | github.com/openai/plugins | R3F architecture (games) | 7,458 / 2026-10-08 / none | B- |
| vercel-labs/json-render @react-three-fiber | github.com/vercel-labs/json-render | R3F JSON renderer | vendor | C (only if using json-render) |
| MengTo/Skills @build-threejs-scroll-worlds | github.com/MengTo/Skills | 3D design / scroll scenes | 6,792 / 2026-10-06 / MIT | A- (method) |
| skinnye/3d-web-pack | github.com/skinnye/3d-web-pack | 3D design / asset pipeline (4 skills) | 5 / 2026-06-14 / MIT | B+ (optimize-3d-assets only) |
| czlonkowski/blender-web-3d-skill | github.com/czlonkowski/blender-web-3d-skill | Blender -> Next.js/Three | 3 / 2026-09-23 / MIT; created 2026-08 | B+ (new, unproven) |
| sickn33/agentic-awesome-skills @3d-web-experience, premium-3d-website | github.com/sickn33/agentic-awesome-skills | 3D design generalist | 47,709 (registry) / daily / MIT | C+ |
| jangtrinh/design-os-3d-blender @img2threejs | github.com/jangtrinh/design-os-3d-blender | image -> procedural three.js | 96 / 2026-10-15 / Apache-2.0; likely-viral flag | B- |
| earthtojake/text-to-cad @cad | github.com/earthtojake/text-to-cad | CAD -> GLB | 20,869 / 2026-10-16 / MIT | B (outside my deep read) |
| NousResearch/hermes-official-plugins @blender | github.com/NousResearch/hermes-official-plugins | Blender (official Blender Lab MCP + skill) | 298 / 2026-10-16 / MIT | A (Blender) |
| ahujasid/mcp-for-blender (ex blender-mcp) | github.com/ahujasid/mcp-for-blender | Blender MCP engine | 31,079 / 2026-10-06 / MIT | A (MCP) |
| vladmdgolam/agent-skills @blender-mcp | same repo as above | Blender -> glTF gotchas | 9 / 2026-10-14 / MIT | A- |
| EL4CTEO/blender-skills | github.com/EL4CTEO/blender-skills | Blender 5.x (20 skills) | 43 / 2026-10-15 / MIT; **created 2026-10-14** | B+ |
| RobLe3/cc-blender-skill | github.com/RobLe3/cc-blender-skill | Blender (30 skills, MCP orchestrator) | 98 / 2026-10-12 / see repo | B |
| arjun988/blender-skills | github.com/arjun988/blender-skills | Blender (188 SKILL.md, style packs) | 315 / 2026-07-10 | C+ (bloat, game/film styles) |
| QwenLM/Qwen-MM-Plugins @blender | github.com/QwenLM/Qwen-MM-Plugins | Blender skill+MCP | 3,136 / 2026-10-11 / Apache-2.0 | C+ (single 12KB file) |
| scenario-labs/skills @scenario-3d, scenario-blender-* | github.com/scenario-labs/skills | 3D gen API / Blender router | 1,031 / 2026-10-16 | C (vendor-API tied) |
| thrixel/build-world | github.com/thrixel/build-world | 3D worlds, vendor assets | 104 / 2026-10-15 / Apache-2.0 | C (vendor-tied, game/Unreal) |

## 3. Finalists

Install syntax for the open ecosystem: `npx skills add <owner>/<repo> --skill <name>` (not run). Manual alternative: copy the folder into `.claude/skills/`.

### 3.1 EnzeD/r3f-skills (three.js / R3F) — grade A
- Link/install: https://github.com/EnzeD/r3f-skills · `npx skills add EnzeD/r3f-skills`
- 11 small skills: fundamentals, animation, geometry, interaction, lighting, loaders, materials, physics, postprocessing, shaders, textures. Each 80-ish lines, each ends in `Verify` and `Sources` linking pinned upstream docs.
- Outline (r3f-fundamentals): Choose the right baseline (read manifest/lockfile first; Fiber 9 / React 19 vs Fiber 8 / React 18) · Minimal scene · Scene and type boundaries · Render-loop decisions · Renderer and ownership pitfalls (`dispose={null}`, Strict Mode) · Verify · Sources. Physics skill: Rapier 2 targets Fiber 9/React 19.
- Signals: 128 stars, created 2026-01-20, last push 2026-08-31, 1.8K installs/skill on skills.sh (other lane). No licence file [red flag for redistribution, not for local use].
- Strengths: the only R3F set I read that is explicitly React 19 / Fiber 9 aware and tells the agent to check installed versions; terse; links to primary docs. Weakness: thin (no recipes); no licence.
- Fit: **high** (Next 16 / React 19, R3F). Local: `sources/github/EnzeD__r3f-skills__r3f-skills/`. Grade [P].

### 3.2 millionco/react-doctor @improve-threejs (three.js / R3F audit) — A
- https://github.com/millionco/react-doctor · `npx skills add millionco/react-doctor --skill improve-threejs`
- Audit-and-fix workflow: Recon (map every `useFrame`/RAF hot path) -> Scan (`npx react-doctor@latest --verbose`, read-only) -> Triage by frame-loop leverage -> Visual audit -> Fix -> Validate -> "Checks the scanner always misses" (z-fighting, shadow acne, colour space, resize, GPU disposal).
- Signals: health shows star-burst flag, C 0.27 D 0.62 (responsive issues). Active org repo.
- Strengths: process skill (not an API cheat sheet) so it does not go stale; severity-by-render-loop principle is right. Weakness: depends on running `npx react-doctor@latest` (network fetch of a tool at run time; review before allowing).
- Fit: **high** once scenes exist. Local: `sources/github/millionco__react-doctor__improve-threejs/`. [P]

### 3.3 vladmdgolam/agent-skills @threejs-perf-loading (three.js perf) — A-
- https://github.com/vladmdgolam/agent-skills · `--skill threejs-perf-loading`
- 565 lines: Loading and warmup (hide shader compile/decode behind the preloader) · Render-loop cost discipline · Adaptive quality · Scroll/input smoothing (cap the step, not the value) · Transmission/glass render target ownership · Frame attribution tooling.
- Signals: 9 stars, created 2026-02-16, pushed 2026-10-14, MIT, single maintainer. Mentions GSAP once (incidental).
- Strengths: concrete studio-grade practices for marketing-style scenes (preloader, adaptive DPR). Weakness: small, unproven repo; long single file.
- Fit: **high**. Local: `sources/github/vladmdgolam__agent-skills__threejs-perf-loading/`. [P]

### 3.4 dgreenheck/webgpu-claude-skill @webgpu-threejs-tsl (WebGPU/TSL) — B+
- https://github.com/dgreenheck/webgpu-claude-skill · `--skill webgpu-threejs-tsl`
- SKILL.md is an index: Quick Start, Skill Contents (docs, 9 files incl. examples, templates, reference), Key Concepts (import pattern `three/webgpu` + `three/tsl`, node materials, method chaining, custom functions), When to use.
- Signals: 1,252 stars, created 2026-01-23, **last push 2026-04-10**, no licence. Also mirrored via JetBrains/skills (other lane).
- Strengths: author is a known three.js educator; covers compute and post. Weakness: 6 months without a push on a fast-moving API (TSL changes per release); no licence; WebGPU renderer on a marketing site needs a WebGL2 fallback decision.
- Fit: **medium** (adopt only if choosing WebGPU/TSL shaders). Local: `sources/github/dgreenheck__webgpu-claude-skill__webgpu-threejs-tsl/`. [P]

### 3.5 CloudAI-X/threejs-skills (three.js broad) — B
- https://github.com/CloudAI-X/threejs-skills · `npx skills add CloudAI-X/threejs-skills`
- 10 skills: fundamentals, geometry, materials, lighting, textures, animation, loaders, shaders, postprocessing, interaction. Fundamentals outline: Quick Start · Core Classes (Scene, Cameras, WebGLRenderer, Object3D) · Coordinate system · Math · Common Patterns (cleanup, Clock, responsive canvas, loading manager) · Performance tips.
- Signals: 3,583 stars (the skills.sh install leader per other lane), created 2026-01-19, last push 2026-07-09, **no licence**, ghrelay flags star-burst + single-maintainer; responsiveness D=0 (issues unanswered).
- Strengths: broad vanilla three.js reference, short files. Weakness: vanilla (not R3F/React 19), WebGLRenderer-centric, no versioning discipline, no maintenance.
- Fit: **medium** as a baseline vanilla reference. Local: `sources/github/CloudAI-X__threejs-skills__threejs-skills/`. [P]

### 3.6 scottstts/Threejs-Awesome-Graphics-Agent-Skills (advanced graphics) — B selective
- https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills · `npx skills add scottstts/Threejs-Awesome-Graphics-Agent-Skills`
- 24 skills with a router (`threejs-skill-router`) mapping a desired visual to the smallest skill set: bloom, image-pipeline (GTAO, tone mapping, LUT), exposure/colour grading, camera-direction, procedural geometry/materials/planets/vegetation, water optics, volumetric clouds, shadow systems, visual-validation. Each has `references/` with working examples (78 files, 676KB).
- Signals: 913 stars, created 2026-06-19, pushed 2026-10-15, MIT, single maintainer. References are TSL/WebGL2-oriented (17 TSL mentions).
- Strengths: deep and current; visual-validation skill is useful for agent self-checking. Weakness: oversized for a marketing site; context cost if everything loads; many skills are showpiece effects (planets, oceans).
- Fit: **medium**: install only `threejs-skill-router`, `threejs-bloom`, `threejs-image-pipeline`, `threejs-exposure-color-grading`, `threejs-visual-validation`. Local: `sources/github/scottstts__...__threejs-awesome-graphics/`. [P]

### 3.7 MengTo/Skills @build-threejs-scroll-worlds (3D design / scroll scenes) — A- as method
- https://github.com/MengTo/Skills (path `agent-skills/web-design/build-threejs-scroll-worlds`) · `--skill build-threejs-scroll-worlds`
- Outline: Route the request · Read build references · Start with the output, not the template · World bible · Scene ledger · One persistent spatial architecture · Geometry/materials/lighting · Map native scroll to deterministic state · Camera as cinematography · Interpolate world state from one conductor · Interactions without fighting scroll · Semantic DOM story · Progressive loading · Measurable performance budget · Motion/access/failure · Verify the whole journey · Deliver. 6 files with references.
- Signals: 6,792 stars (repo-wide, 265-style design pack), created 2026-02-03, pushed 2026-10-06, MIT.
- Strengths: scroll-to-state "single conductor" model matches the `ScrubStage` philosophy in this repo; accessibility and budget sections. Weakness: routes DOM-first scroll work to a sibling `cinematic-scroll-storytelling` skill that assumes GSAP/Lenis (not in this repo's stack); repo is broad so star count says little about this skill.
- Fit: **high** for the planning method; ignore GSAP/Lenis routing. Local: `sources/github/MengTo__Skills__build-threejs-scroll-worlds/`. [P]

### 3.8 skinnye/3d-web-pack (asset pipeline + scaffolding) — B+ (one skill)
- https://github.com/skinnye/3d-web-pack · skills: `optimize-3d-assets`, `add-postprocessing`, `scaffold-3d-site`, `scroll-3d-scene`.
- optimize-3d-assets outline (60 lines): Step 0 inspect · Step 1 one-shot optimize (gltf-transform / gltfpack) · Step 2 targeted passes (meshopt, Draco, KTX2) · Step 3 gltfjsx to R3F component · Step 4 runtime decoders in drei · Step 5 verify and report · Targets.
- Signals: 5 stars, created 2026-06-14, MIT. Tiny and new.
- Red flag for this repo: `scroll-3d-scene` is Lenis + GSAP ScrollTrigger (or drei ScrollControls): conflicts with the "Motion only, no GSAP, no Lenis" rule. `scaffold-3d-site` is Vite-first.
- Fit: **high for optimize-3d-assets**, low for the rest. Local: `sources/github/skinnye__3d-web-pack__3d-web-pack/`. [U]

### 3.9 czlonkowski/blender-web-3d-skill (Blender -> Next.js/three) — B+
- https://github.com/czlonkowski/blender-web-3d-skill · `--skill blender-web-3d`
- 8 files, 113-line SKILL.md: Start from the assets · MCP vs headless CLI · iteration loop (change -> export -> optimise -> view) · reference files per phase (gltf-transform meshopt/KTX2, AgX colour, GLSL material patches, procedural sky, bloom, adaptive quality, batching, baked lightmaps, Vercel deploy) · design lessons · "when the user reports a visual bug from a screenshot". Requires Blender 4/5, Node 20+.
- Signals: **3 stars**, created 2026-08-03, MIT, 4 installs (other lane). Single author.
- Strengths: the closest thing to exactly our use case (Blender asset -> Next.js three viewer). Weakness: unproven; read it before trusting its templates.
- Fit: **high on paper, treat as a draft to vet**. Local: `sources/github/czlonkowski__blender-web-3d-skill__blender-web-3d/`. [U]

### 3.10 jangtrinh/design-os-3d-blender @img2threejs, blender-image-to-3d — B-
- https://github.com/jangtrinh/design-os-3d-blender
- img2threejs (324 lines + 43 files): image-reference to quality-gated procedural three.js model; layered contract, gates, self-correction loop; scripts enforce, agent vision judges.
- Signals: 96 stars, pushed 2026-10-15, Apache-2.0; ghrelay flag `likely-viral`. Other lane reports a separate `img2threejs/img2threejs` repo at 18K stars (not verified by me).
- Fit: **low-medium** (hero objects built in code rather than glTF; heavy process). Local: `sources/github/jangtrinh__design-os-3d-blender__img2threejs/`, `..._blender-image-to-3d/`. [U]

### 3.11 NousResearch/hermes-official-plugins @blender (official Blender Lab MCP + skill) — A (Blender)
- https://github.com/NousResearch/hermes-official-plugins/tree/main/blender (catalog entry in NousResearch/hermes-agent `plugin-catalog/blender.yaml`; the earlier `optional-skills/creative/blender-mcp` path is gone from hermes-agent, a copy survives in math-inc/OpenGauss, also saved).
- 44-line SKILL.md: First run on a new computer · Before working (check add-on connection) · Scene workflow (read scene first, verify edits) · Security and setup boundaries. Wraps the **official Blender Lab MCP server pinned to v1.0.3**, needs Blender 5.1+, `uv`, Git. Catalog disclosure: tools execute arbitrary Python in Blender with the user's privileges.
- Signals: org repo 298 stars, pushed 2026-10-16, MIT. Tessl review of the older skill: 78% (via WebSearch, [B]).
- Strengths: official engine, minimal skill, honest security note. Weakness: skill is a thin wrapper; modelling craft must come from another skill.
- Fit: **high** for the Blender connection. Local: `sources/github/NousResearch__hermes-official-plugins__blender-mcp-official/`, `math-inc__OpenGauss__blender-mcp/`. [V/P]

### 3.12 ahujasid/mcp-for-blender (formerly blender-mcp) — MCP, A
- https://github.com/ahujasid/mcp-for-blender · README saved. "Formerly blender-mcp; PyPI package now mcp-for-blender; existing setups keep working. Third-party, not made by Blender."
- 31,079 stars, pushed 2026-10-06, MIT; ghrelay: star-burst, single-maintainer, C 0.49 D 0.35. De-facto community engine behind most Blender skills (vladmdgolam, czlonkowski, RobLe3 all target it).
- Two MCP candidates now exist: this community one (Poly Haven / Sketchfab / Hyper3D integrations) and the official Blender Lab MCP. Pick one to avoid duplicate tool names; the skills above mostly work with either.
- Fit: **high** (the only Blender path that lets an agent see the viewport). Local: `sources/github/ahujasid__mcp-for-blender__README/`. [P]

### 3.13 vladmdgolam/agent-skills @blender-mcp (Blender -> glTF for web) — A-
- https://github.com/vladmdgolam/agent-skills · `--skill blender-mcp`
- 675 lines + 3 refs: Tool selection · Health check first · Complete export workflow (health check, inspect, verify materials, export via **headless CLI**, optimise with gltf-transform, validate) · Critical rules (MCP times out on exports; do not apply modifiers on export; export without Draco first; procedural textures do not export; never use `gltf-transform optimize`; quote paths) · material/animation extraction · known errors.
- Signals: 9 stars, pushed 2026-10-14, MIT; 2.2K installs (other lane).
- Strengths: hard-won, specific failure modes for the Blender -> three.js hand-off; pairs with Section 3.8. Weakness: long, tiny repo, opinionated.
- Fit: **high**. Local: `sources/github/vladmdgolam__agent-skills__blender-mcp/`. [P]

### 3.14 EL4CTEO/blender-skills (Blender 5.x) — B+
- https://github.com/EL4CTEO/blender-skills · 20 skills: blender-core (router; 5.x API breakages that break LLM memory), export-pipelines (glTF/GLB web preset with meshopt/Draco/WebP), asset-qa, game-optimization, pbr-materials, geometry-nodes, lighting-lookdev, rendering, etc.
- Signals: 43 stars, **created 2026-10-14 (2 days old)**, MIT. Not yet track-recorded.
- Strengths: Blender 5.2-specific, tidy router + verify-before-done rule. Weakness: no history; game-engine slant.
- Fit: **medium-high**: `blender-core` + `blender-export-pipelines` + `blender-asset-qa`. Local: `sources/github/EL4CTEO__blender-skills__*/`. [U]

### 3.15 RobLe3/cc-blender-skill (Blender orchestrator) — B
- https://github.com/RobLe3/cc-blender-skill · plugin with 30 skills (modeling, materials, lighting, cameras, export, UV, reference-to-3D, quality autoloops). `blender-export` is 354 lines with 10 recipes and a polycount table; allowed-tools reference both community and official Blender MCP.
- Signals: 98 stars, pushed 2026-10-12, ~1K installs per skill (other lane).
- Weakness: very broad (mascot/UV/fit-repair skills irrelevant to us). Fit: **medium**, take `blender-export`, `blender-pro-workflow`. Local: `sources/github/RobLe3__cc-blender-skill__*/`. [P]

### 3.16 Others read but not recommended
- freshtechbro/claudedesignskills: 24 web-3D/animation skills incl. `react-three-fiber`, `threejs-webgl`, `blender-web-pipeline`, `spline-interactive`. Last push 2025-11-20, GSAP/Lenis woven through, R3F skill references R3F 8 + drei 9. **Stale and wrong animation stack.** [P]
- OpenAEC Three.js package: 24 skills in a methodical core/syntax/impl/errors/agents split with ALWAYS/NEVER wording. MIT, 21 stars; mixed `WebGLRenderer`/WebGPU, not React 19-specific. Possible reference; low adoption. [P]
- sickn33/agentic-awesome-skills: mirror/registry (47K stars, daily commits). `3d-web-experience` (422 lines: stack selection, Spline vs R3F, model pipeline, scroll-driven 3D) and `premium-3d-website` are generic; duplicates exist under three plugin paths. Fine as a decision-tree reference, not authoritative. [P]
- majidmanzarpour/threejs-game-skills: 9 well-made game skills (Tripo API for 3D generation, QA, game director); game-oriented and needs a Tripo key. Not for a marketing site. [P]
- openai/plugins react-three-fiber-game and vercel-labs/json-render react-three-fiber: first is architecture guidance for R3F games (shared React state, 3D HUD); second is only for json-render users. [V]
- AThevon/genjutsu threejs-r3f: 495 stars, 2026-09-08 version stamp (admirably explicit), but bundled inside a creative-coding pack whose motion skills are GSAP/framer-motion. Reference only. [P]
- earthtojake/text-to-cad @cad: 20.9K stars, MIT; saved (14 files); not deep-read by me, defer to the skills.sh lane.
- scenario-labs/skills, thrixel/build-world: tied to vendor generation APIs/assets. Skip.
- arjun988/blender-skills: 188 SKILL.md with style packs (horror, anime, chibi); a 358-line `blender-director` router. Context bloat for our needs. Skip unless film/game styles wanted.
- Impertio Blender/Bonsai skills (73): BIM/IFC focus, skip. nexu-io/open-design `threejs`: points to CloudAI-X.
- Not skills (noted): CoplayDev/unity-mcp, HKUDS/CLI-Anything, anthropics/skills, vercel-labs/agent-skills have no relevant 3D skill in the paths I probed; asgeirtj/system_prompts_leaks contains a leaked Anthropic claude-design `3d-object` prompt; not used as a source.

## 4. Dissent, red flags, gaps

- **Licences:** CloudAI-X, dgreenheck, EnzeD and openai/plugins have no licence file at repo level. For local use this is fine; do not vendor into the repo.
- **Star validity:** ghrelay flagged `star-burst` on CloudAI-X, majidmanzarpour, json-render, react-doctor, ahujasid (the last is plausible organic virality). Treat 3K-star counts as install-driven (skills.sh) rather than quality proof. `starredAt` API is restricted so the star-history sample was unavailable; flags rely on ClickHouse only.
- **Motion vs GSAP:** every scroll-3D skill I found (skinnye scroll-3d-scene, freshtechbro, MengTo sibling skill, genjutsu, sickn33) defaults to GSAP ScrollTrigger and/or Lenis. None teaches Motion (`motion/react`). Adopting any of them means overriding the scroll section. `docs/MOTION-DESIGN-SYSTEM.md` remains the authority.
- **Recency risk:** several of the best-fitting Blender/Next.js skills are weeks old (czlonkowski created 2026-08-03, EL4CTEO 2026-10-14). No track record.
- **Vanilla vs R3F:** the popular vanilla three.js sets (CloudAI-X) are not React 19 / Fiber 9 aware; only EnzeD states that.
- **Two Blender MCP engines** (community mcp-for-blender vs official Blender Lab MCP via Hermes catalog). Tool names differ; choose one per project.
- **Gaps:** I did not run any skill or check three.js API currency line by line (only grep for renderer/version signals); did not deep-read the text-to-cad, Spline, TerminalSkills or Mindrally copies; TerminalSkills/Mindrally three.js skills seen only via aggregator pages. Health (`D` responsiveness) is null for repos with few issues. skills.sh install counts and X sentiment are in the other lanes.

## 5. Sources saved

52 source folders (392 files incl. SOURCE.txt) under `research/3d-skills/sources/github/` (each with SOURCE.txt: URL, commit SHA and date, fetch date). Total files listed in the final summary.
