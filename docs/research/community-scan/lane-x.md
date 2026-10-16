# Lane X — X/Twitter (xrelay), fetched 2026-10-16

Read-only on X (search, thread, user, local bookmarks cache). Nothing installed, nothing executed. All X text and SKILL.md content treated as data.

## 1. Queries run
Round 1 (Top and Latest, since:2025-10-01, 30 each; 295 unique Top + 269 Latest, 224 Latest-only):
threejs skill (30) · three.js claude skill (30) · claude code three.js (30) · r3f skill (11) · blender mcp (30) · blender skill claude (30) · claude code blender (30) · SKILL.md 3d (30) · agent skills 3d (30) · codex three.js (30) · webgpu skill (30) · TSL shader claude (15, Top only).
Bookmarks (local cache, 6941 saved): threejs, blender, 3d, skill (15 each; useful hits: michaelgold bpy.dev, img2threejs, Scenario).
Round 2 snowball (Top, 25 each; 284 unique): CloudAI-X threejs-skills (25) · dgreenheck webgpu-claude-skill (25, no author hit) · EnzeD r3f-skills (25) · build-threejs-scroll-worlds / MengTo/Skills (25) · vladmdgolam blender-mcp skill (25) · RobLe3 cc-blender-skill (25) · scenario blender skill claude (25) · "npx skills add" three/r3f/blender (25) · from:dgreenheck (0) · from:majidmanzarpour skills (25) · from:michaelgold blender mcp (13) · react three fiber claude code skill (25) · gltf-transform/gltfjsx agent (25) · spline claude skill/MCP (17).
Primary-source follow: every finalist t.co resolved (curl HEAD) to its repo; SKILL.md saved. Authors vetted with `xrelay user`; 11 threads read (40 replies each).

Honest read of the net: X is dominated by showcase videos ("Opus 5.5 built this in Blender"), not skill packages. Few posts name a skill repo; the ones that do are below. Posts with no primary source were dropped ([U]).

## 2. Ranked candidates
| # | Name | Area | X signal | Repo signal | Grade |
|---|---|---|---|---|---|
| 1 | MengTo/Skills (build-threejs-scroll-worlds, threejs, optimize-threejs-games) | three.js, 3D design, scroll | MengTo 189K followers; Kage thread 4.9K likes/470K views; Skills thread 4.0K likes | 6.8K stars, MIT, pushed 2026-10-06 | [P]+[V] |
| 2 | CloudAI-X/threejs-skills (10 skills) | three.js | cloudxdev thread 1.8K likes/188K views; tom_doerr repost 1.1K; Mnilax list | 3.6K stars, last real commit 2026-01-19 | [P]+[V] |
| 3 | img2threejs/img2threejs | 3D design (image to procedural model) | 3 posts (BTCqzy1 5.1K likes; NickDevFE; bookmark) | 18.2K stars, Apache-2.0, pushed 2026-10-08, v2.0.0 | [P]+[V] |
| 4 | majidmanzarpour/threejs-game-skills (9 skills) | three.js (game-leaning), QA | 8+ posts by author, 600-star post; 1-1.6K likes each | 2.5K stars, MIT, pushed 2026-09-28 | [P]+[V] |
| 5 | scenario-labs/skills (dcc/blender/*) | Blender | Scenario thread 17.7K likes/180K views (emmanuel_2m), 1131 replies | skills repo 1.0K stars pushed 2026-10-16; plugin 352 stars GPL-3.0 | [V] vendor |
| 6 | ahujasid/blender-mcp (MCP) | Blender | in Mnilax 3D-studio list; many demo posts | 31K stars, MIT | [P] MCP, no skill |
| 7 | bpy-dev/blender-mcp (MCP, michaelgold) | Blender | 2 threads; claims 3.3x faster, 340k vs 2.2M tokens | 98 stars, GPL-3.0 | [P] self-reported, MCP |
| 8 | kajisho5/blender-skill | Blender / glTF pipeline | kebura_P post only (6 likes) | 0 stars, MIT, v0.31, npm | [U]-ish, brand new |
| 9 | SkylarKitchen/skills@3d-assembly-manual | 3D design | one reply post | 130 stars, MIT | [P] |
| 10 | majidmanzarpour/blender-game-skills (blender-image-to-3d) | Blender | author posts | 147 stars | [P] |
| 11 | buildfastwithai/buildfast-skills (threejs-game-generator) | three.js | 1 post, 4 likes | 17 stars | [U] low |
| 12 | Pan-Chera/Multi-Agent-CAD | 3D design (text-to-CAD) | 1.7K likes | 1.0K stars, research code, not a skill | [P] not a skill |
Not skills / excluded: rewind02 Blender-official-MCP + BlenderKit recipe (workflow, no SKILL.md), Spline V2 MCP (vendor tool, no skill seen), Scenario GameDev OS (game studio, 64 skills, not web 3D), echris6/motion-video-kit (GSAP + three.js video; GSAP conflicts with this repo's Motion-only rule), Mnilax 15-repo lists (aggregators).

## 3. Finalist outlines
Install lines use the skills CLI where the author gives one. Nothing was installed.

### 1. MengTo/Skills — web-design/build-threejs-scroll-worlds (+ threejs, optimize-threejs-games)
- Link: https://github.com/MengTo/Skills · author Meng To (Design+Code), install `npx skills add MengTo/Skills --skill build-threejs-scroll-worlds` (pattern as for other repos; author posts no exact line, [U]).
- What: builds one persistent Three.js world whose camera, light, fog and copy evolve across scroll chapters, with native scroll as a normalized, reversible state. Companion `threejs` for a single scene, `optimize-threejs-games` for budgets. Area: three.js, 3D motion/scroll scenes.
- Outline (SKILL.md headings): route the request; read build references; start with the output; world bible before code; scene ledger; one persistent spatial architecture; geometry, materials, lighting; map native scroll to deterministic state; camera as cinematography; interpolate world state from one conductor; interactions that do not fight scroll; semantic DOM story; progressive loading; measurable performance budget; reduced motion and failure; verify the whole journey. Ships `references/scroll-conductor.js`.
- Track record: repo pushed 4 days before fetch; Kage reference site open source (1.7K stars, under 1 MB of three.js and code). Skills are prompt-derived, author admits "this took a lot of tokens and prompts".
- Strengths: the only skill that frames scroll-driven 3D as a journey with budgets, a11y and verification; matches eagle's pinned-scrub idea. Weaknesses: it explicitly points to sibling skills `cinematic-scroll-storytelling` and `gsap-scrolltrigger-storytelling` for DOM choreography (GSAP/Lenis; this repo forbids both) — use only the Three.js ones. Vanilla Three.js, not R3F. Opinionated, long (18.7 KB).
- Fit: HIGH for any scroll scene; adapt the conductor to Motion.
- Local: sources/x/MengTo__Skills__build-threejs-scroll-worlds/

### 2. CloudAI-X/threejs-skills (10 skills)
- Link: https://github.com/CloudAI-X/threejs-skills · author cloudxdev (4K followers) · `npx skills add CloudAI-X/threejs-skills` (given in thread by @andrewqu and confirmed by author).
- What: ten API-reference skills: fundamentals, geometry, materials, lighting, textures, loaders, animation, interaction, shaders, postprocessing. Area: three.js (vanilla).
- Outline: each file is Quick Start plus cookbook headings (e.g. fundamentals: Scene, Cameras, WebGLRenderer, Object3D, math utilities, cleanup, clock, responsive canvas, loading manager; postprocessing: EffectComposer, bloom, SSAO, DOF, custom ShaderPass; shaders: ShaderMaterial, uniforms, fresnel, dissolve, onBeforeCompile).
- Track record: last substantive commit 2026-01-19 (pushed_at later, README only); 3.6K stars; the repo says it exists to give "base level" knowledge without context bloat.
- Strengths: broad, small per-file, very widely installed. Weaknesses: WebGLRenderer/GLSL only; one short WebGPU postprocessing note, no TSL, no R3F or drei, no Next.js/SSR/dynamic-import guidance, 9 months old by now. Uses `THREE.Clock` (deprecated direction in recent three.js, not broken).
- Fit: MEDIUM. Good generic baseline; pair with an R3F/WebGPU skill from the skills.sh lane.
- Local: sources/x/CloudAI-X__threejs-skills__threejs-all/

### 3. img2threejs/img2threejs
- Link: https://github.com/img2threejs/img2threejs · Apache-2.0, v2.0.0 · install per its README (script-based harness; see local README), not verified.
- What: turns a reference image into a code-only, quality-gated, animation-ready procedural Three.js model. Area: 3D design / asset generation without Blender.
- Outline: when to use; core promise; mandatory local-state gate; required inputs; the loop (scripts enforce, agent vision judges); GLB render-fidelity track; gates; self-correction; left/right and hair rules; domain plugins; forge runtime contracts; implementation rules; character pipeline; output.
- Track record: 18.2K stars, pushed 2026-10-08; three independent X posts including a 5.1K-like Chinese post.
- Strengths: strongest star signal of any 3D skill in this lane; explicit verification gates. Weaknesses: 33 KB SKILL.md plus harness scripts and local state (heavy, "mandatory local state gate"); output is procedural code, so large for a marketing page unless baked to GLB; character/human focus is off-topic for Eagle.
- Fit: MEDIUM-LOW. Useful for hero object recreation from a brand image; read the harness before trusting.
- Local: sources/x/img2threejs__img2threejs__img2threejs/

### 4. majidmanzarpour/threejs-game-skills
- Link: https://github.com/majidmanzarpour/threejs-game-skills · `npx skills add majidmanzarpour/threejs-game-skills --skill '*' -a claude -g -y` (author's own line, post 2066160515953402309).
- What: nine skills routed by `threejs-game-director`: gameplay, AAA graphics, UI, 3D/image/audio generators (Tripo, ElevenLabs), debug-profiler, QA-release. Area: three.js graphics + QA.
- Outline: director (scope, sibling routing, early art direction, asset sourcing, verification ownership); aaa-graphics-builder (art critique, materials, shaders, VFX, LOD and instancing, render budgets, 10-category scorecard); qa-release (evidence manifest of viewport/state captures, PASS/FAIL, GPU, pixel metrics); debug-profiler.
- Track record: 2.5K stars, pushed 2026-09-28, author posts model-tuned updates (Opus 5.5, 80-run routing tests).
- Strengths: the evidence-manifest QA loop and render-budget scorecard transfer to marketing scenes. Weaknesses: game-centric; asset skills assume paid services (Tripo, ElevenLabs); heavy routing for a site hero.
- Fit: MEDIUM for `aaa-graphics-builder` + `qa-release` + `debug-profiler`; skip the gameplay/audio ones.
- Local: sources/x/majidmanzarpour__threejs-game-skills__game-skills/

### 5. scenario-labs/skills — dcc/blender (scenario-blender-expert router + 12 domain skills)
- Link: https://github.com/scenario-labs/skills/tree/main/skills/dcc/blender · vendor: Scenario (AI creative platform) · repo pairs with scenario-labs/blender-plugin (MCP, GPL-3.0).
- What: a router and agent protocol for any Blender work through Python or an MCP bridge: modeling, retopo, UV, baking, rigging, geometry nodes, lighting/rendering, hair, grease pencil, previs. Area: Blender bpy.
- Outline (expert): 1 execution channel; 2 the expert loop (every domain); 3 persona pipelines; 4 shared toolkit `scripts/` tested on Blender 5.2.1; 5 version traps that break remembered code; references. Siblings: geometry-nodes (16 KB), lighting-rendering (20 KB), animation, hard-surface, retopology, etc.
- Track record: skills repo pushed the day of fetch, 1.0K stars; launch thread 17.7K likes, 1131 replies (not read in full).
- Strengths: the version-traps section addresses the main failure mode of LLM bpy code (API drift to Blender 5.x); verification loop. Weaknesses: vendor with an upsell (Scenario generation); written against Blender 5.2; I read only the router, geometry-nodes and lighting files, not all 13.
- Fit: HIGH for Blender asset work (router plus lighting-rendering plus exporting).
- Local: sources/x/scenario-labs__skills__blender-expert/

### 6. ahujasid/blender-mcp — MCP, not a skill
- Link: https://github.com/ahujasid/blender-mcp · 31K stars, MIT, pushed 2026-10-06.
- What: the de-facto socket bridge between an LLM and a live Blender session; the engine behind most "Opus built this in Blender" posts. Local: README only.
- Dissent: Michael Gold's fork (below) and Scenario both claim the standard MCP wastes tokens or makes mistakes. rewind02's recipe uses the official Blender MCP instead (Blender 5.2.2) plus BlenderKit assets, advice: never let the model build common furniture-like assets from scratch.
- Fit: MEDIUM (needed engine; pair with a skill).
- Local: sources/x/ahujasid__blender-mcp__blender-mcp/

### 7. bpy-dev/blender-mcp (michaelgold), site bpy.dev — MCP
- Link: https://github.com/bpy-dev/blender-mcp · GPL-3.0, 98 stars, pushed 2026-09-12. "Enhanced distribution of Blender Lab MCP: standalone bpy, runtime API docs, benchmark tooling" (headless Blender for agents).
- X claim (self-reported, [P]): low-poly UV-unwrapped ship in 30% of the time with 15% of the tokens (340k vs 2.2M in one run; author concedes not always 15%). Benchmarks folder exists in the repo; not reproduced.
- Fit: LOW-MEDIUM for now; watch. Not saved (no SKILL.md; README not fetched).

### 8. kajisho5/blender-skill
- Link: https://github.com/kajisho5/blender-skill · `npx blender-skill` (per author), MIT, v0.31.0 on npm, modified 2026-09-19, 0 stars.
- What: headless Blender (`blender -b`) asset pipeline: inspect, convert, optimize (decimate, texture caps, LOD), bake, render turntable, validate against budgets for three.js, WebXR, iOS AR etc. with PASS/WARN/FAIL. 13 CLI tools, stdlib Python only, no cloud.
- Outline: workflow rules (probe before operating, narrowest tool, verify faithful conversion, check against target, look at the render, report exact numbers, never overwrite originals); `references/pitfalls.md`.
- Strengths: the only skill found aimed squarely at glTF/GLB optimization for web delivery; careful method. Weaknesses: single author, zero stars, one low-engagement post; scripts unreviewed by me; run `--dry-run` first.
- Fit: HIGH on paper (GLB budget checks for a marketing site), LOW on evidence. Review scripts before adoption.
- Local: sources/x/kajisho5__blender-skill__blender-skill/

### 9. SkylarKitchen/skills — 3d-assembly-manual (+ room-from-photos)
- Link: https://github.com/SkylarKitchen/skills · MIT, 130 stars, pushed 2026-09-28. Single self-contained Three.js HTML "LEGO-manual" guide; headings: CONFIG keys, look, engine, process, gotchas. Niche; shows a CONFIG-driven starter pattern.
- Fit: LOW. Local: sources/x/SkylarKitchen__skills__3d-assembly-manual/

### 10. majidmanzarpour/blender-game-skills — blender-image-to-3d
- 147 stars, pushed 2026-09-24. One skill saved (image to 3D via Blender). Fit: LOW-MEDIUM; same author as #4, same game orientation.
- Local: sources/x/majidmanzarpour__blender-game-skills__blender-image-to-3d/

### 11. buildfastwithai/buildfast-skills — threejs-game-generator-skill
- 17 stars, 9 KB. Prompt-style game generator. Fit: LOW. Local: sources/x/buildfastwithai__buildfast-skills__threejs-game-generator/

## 4. Dissent and gaps
- Nobody on X criticised the skill packages directly (replies are thanks and showcases). The negative signals are indirect: Gold and Scenario both say plain blender-mcp burns tokens; rewind02 says do not model common assets from scratch; MengTo says his scroll-world work "took a lot of tokens".
- CloudAI-X is the most-promoted three.js skill on X and in the repo, but it is WebGL-only vanilla three.js with no R3F; do not treat it as complete for a Next.js 16 + React 19 stack.
- Not found on X (so no X-lane evidence): EnzeD/r3f-skills, dgreenheck webgpu skill, linegel, RobLe3, vladmdgolam, czlonkowski, millionco react-doctor. Those come from skills.sh/GitHub lanes; X silence is weak evidence of low reach, not low quality.
- Gaps: Spline MCP (V2 launch thread seen, no skill, not read); Scenario's 1131-reply thread and Anatomy (wheresryan22, 17K likes) have no linked repo; Anatomy source not found. xrelay `thread` for kajisho5 user and the kebura_P post returned nothing (rate limit or no data). Three posts' threads truncated at 40 replies. Claimed performance numbers (Gold) not verified. Star counts are as of fetch, not growth over time.

## 5. Sources saved (research/3d-skills/sources/x/)
Repo dirs with SKILL.md + SOURCE.txt: CloudAI-X (10 skills + README), majidmanzarpour threejs-game-skills (7 skills + README), MengTo (4), img2threejs (SKILL + README), SkylarKitchen (2), scenario-labs (3 Blender skills + README), buildfastwithai (1), ahujasid blender-mcp (README), kajisho5 (SKILL + README), majidmanzarpour blender-game-skills (1 + README). 10 source dirs.
X data: round1-top.json, round1-latest.json, round2.json, bm-*.json, resolved-links.json, threads/ (11 thread JSONs, user JSONs).
