# Lane 1 — skills.sh / `npx skills find`

Fetched 2026-10-16. Install counts are from `npx skills find` output (skills.sh). Repo stats from `gh api`.
Raw query output: `sources/skills-sh/_queries/` (round 1) and `_queries2/` (round 2). Repo stats: `sources/skills-sh/_repos.txt`.

## 1. Queries run

Each query returns a capped list of 20 skills.

**Round 1 (22 queries, 20 hits each):** threejs, three.js, react-three-fiber, r3f, webgpu, tsl shader, glsl shader, 3d, 3d design, 3d model, gltf, spline, blender, bpy, blender mcp, babylon, webgl, shader, product visualization, text to 3d, 3d printing, cad.

**Round 2 (24 snowball queries, 20 hits each):** drei, postprocessing, webgpu threejs, threejs performance, scroll 3d, glb optimize, gltf-transform, blender python, blender addon, blender export gltf, react three fiber nextjs, pmndrs, 3d hero website, threejs tsl, r3f performance, product configurator 3d, blender render, blender geometry nodes, three.js scroll animation, 3d web design, threejs motion, gaussian splat, 3d asset pipeline, threejs official.

Round 2 added about 90 new names, mostly small publishers. The snowball names were the `linegel`, `MengTo`, `czlonkowski`, `skinnye` and `millionco` skills, plus the glTF and scroll-3D skills.

**Search-quality caveats**
- skills.sh keyword search is noisy. "3d" and "cad" surface unrelated mega-installed skills (`anthropics/skills@frontend-design` 992K, `mattpocock/skills@domain-modeling` 829K, `heygen-com/hyperframes@figma` 287K). Install counts do not imply relevance.
- Several publishers are bulk or mirror farms with near-identical skills: `101-skills`/`magentosh`/`qu-skills`/`skills-shell` `superpowers`, `avabillions2040/claudedesignskills-02-02-2026` (a copy of `freshtechbro`), `emmraan`, `raptoravis/threejs-game-skills` (a Babylon rename of `majidmanzarpour`), and `sickn33/*`. I did not rank any of them.
- There is no pmndrs, mrdoob, Three.js-org or Blender-org skill on skills.sh. The queries `pmndrs` and `threejs official` returned none. All three.js and R3F skills are community-authored.

## 2. Ranked candidates

Grade key: A = adopt, B = useful and selective, C = niche or caution, D = skip. Installs are per skill.

| Rank | Name | Area | Signals | Grade |
|---|---|---|---|---|
| 1 | [JetBrains/skills@webgpu-threejs-tsl](https://skills.sh/dgreenheck/webgpu-claude-skill/webgpu-threejs-tsl) (author Dgreenheck) | three.js WebGPU/TSL | Original repo 1.2K stars, 1.3K installs; JetBrains mirror 370 stars, 22 installs, last push 2026-06-29. Contains docs/, examples/, and a compute and post-processing guide. | A |
| 2 | [EnzeD/r3f-skills](https://github.com/EnzeD/r3f-skills) (fundamentals, shaders, animation, postprocessing, ...) | R3F / drei | 128 stars, about 1.8-1.9K installs per skill, pushed 2026-08-31. Targets Fiber 9 and React 19. | A |
| 3 | [CloudAI-X/threejs-skills](https://skills.sh/cloudai-x/threejs-skills/threejs-fundamentals) (10 skills) | three.js vanilla (WebGL) | 3.6K stars, 11-18K installs each (highest of any 3D skill), pushed 2026-07-09. | B |
| 4 | [MengTo/Skills@build-threejs-scroll-worlds](https://github.com/MengTo/Skills) | 3D motion/scroll | 6.8K-star repo, 1.3K installs, pushed 2026-10-06. Has `references/` and a demo. | B |
| 5 | [millionco/react-doctor@improve-threejs](https://github.com/millionco/react-doctor) | R3F perf/audit | 15K-star repo, 299 installs, pushed 2026-10-16. | B |
| 6 | [czlonkowski/blender-web-3d-skill@blender-web-3d](https://github.com/czlonkowski/blender-web-3d-skill) | Blender to Next.js/Three | 3 stars, 4 installs, created 2026-08-03. Highest fit but near zero track record. | B (verify) |
| 7 | [vladmdgolam/agent-skills@blender-mcp](https://github.com/vladmdgolam/agent-skills) | Blender MCP + glTF export | 9 stars, 2.2K installs, pushed 2026-10-14. Uses `ahujasid/blender-mcp` (31K stars) as the engine. | A- |
| 8 | [RobLe3/cc-blender-skill](https://github.com/RobLe3/cc-blender-skill) (pro-workflow, text-to-blender, lighting, cameras, uv-texturing) | Blender | 98 stars, about 1K installs each, pushed 2026-10-12. | B |
| 9 | [ifBars/blender-agent-studio@blender-rendering-workflow](https://github.com/ifBars/blender-agent-studio) | Blender render | 84 stars, 82 installs, pushed 2026-10-16. | B |
| 10 | [scenario-labs/skills@scenario-blender-expert](https://github.com/scenario-labs/skills) | Blender router | 1.0K-star repo, 328 installs, created 2026-08-12. Claims scripts tested on Blender 5.2.1. | B |
| 11 | [linegel/threejs-complete-set-of-skill](https://github.com/linegel/threejs-complete-set-of-skill) (choose-skills, visual-validation, bloom, ...) | three.js WebGPU/TSL | 10 stars, about 125 installs each, pushed 2026-09-24. | C |
| 12 | [cazala/webgpu-skill@webgpu](https://github.com/cazala/webgpu-skill) | raw WebGPU/WGSL | 34 stars, 830 installs. Not three.js. | C |
| 13 | [skinnye/3d-web-pack@optimize-3d-assets](https://github.com/skinnye/3d-web-pack) | glTF pipeline | 5 stars, 40 installs. Short, but correct tool choices. | C+ |
| 14 | [gamedev-skills/awesome-gamedev-agent-skills@threejs-gltf-loading](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) | glTF loading | 1.5K-star repo, 3.9K installs. Game-oriented. | C+ |
| 15 | [MengTo/Skills@3d-paper-material](https://github.com/MengTo/Skills) | 3D design (materials) | 182 installs, shares the 6.8K-star repo. | C |
| 16 | [freshtechbro/claudedesignskills](https://github.com/freshtechbro/claudedesignskills) (react-three-fiber, blender-web-pipeline, spline-interactive) | R3F / Blender / Spline | 1.1K stars, 3.2-4.3K installs, last push 2025-11-20 (stale). | C |
| 17 | [earthtojake/text-to-cad@cad](https://github.com/earthtojake/text-to-cad) | CAD (STEP/STL/GLB) | 20.9K stars, 13K installs, pushed 2026-10-16. Mechanical CAD, not web. | C |
| 18 | [skinnye/3d-web-pack@scroll-3d-scene](https://github.com/skinnye/3d-web-pack) | scroll 3D | 35 installs. Depends on GSAP and Lenis, which this repo bans. | D for this repo |
| 19 | [gabremoku/immersive-3d-web](https://github.com/gabremoku/immersive-3d-web) | 3D web design | 1 star, 53 installs, built on GSAP ScrollTrigger. | D |
| 20 | [heygen-com/hyperframes@three](https://skills.sh/heygen-com/hyperframes/three) | video-render adapter | 69.3K installs, 64.9K-star repo. It is a deterministic-frame adapter for HyperFrames video, not a general three.js skill. | D (inflated by the host repo) |

Not fetched or not ranked: `meshy-dev/meshy-3d-agent` (text-to-3D via a paid Meshy API; 908 installs, 101 stars; SKILL.md path not resolvable by my script, so it was not read), `nexu-io/open-design@threejs` (a 43-line pointer to upstream), `arjun988/blender-skills` (315-star repo, about 250-300 installs per skill, game-art focus: FBX/Unreal/Unity), `ra100/blender-claude-plugin`, `HKUDS/CLI-Anything@cli-anything-blender` (a different CLI harness), `affaan-m/ECC@blender-motion-state-inspection` (6.3K installs, character rigs; irrelevant here), `SFKislev/Flue@Blender` (21-line stub), `mitsuhiko/agent-stuff@openscad` (988 installs).

## 3. Finalists

Claim grades are on each assessment. Signals are [P] practitioner or metadata unless noted. I read the SKILL.md headings and frontmatter and spot-checked bodies. I did not run any code.

### 3.1 JetBrains/skills@webgpu-threejs-tsl (author Dgreenheck) — three.js WebGPU/TSL
- Link: https://skills.sh/dgreenheck/webgpu-claude-skill/webgpu-threejs-tsl. Install: `npx skills add dgreenheck/webgpu-claude-skill@webgpu-threejs-tsl` (original) or `npx skills add JetBrains/skills@webgpu-threejs-tsl` (mirror).
- What: Quick start for `three/webgpu` plus `three/tsl` imports, `WebGPURenderer` with `await renderer.init()`, node materials, compute shaders, post-processing, WGSL integration.
- Outline: SKILL.md (96 lines) is an index. `docs/` has core-concepts, materials, compute-shaders, post-processing, wgsl-integration, device-loss, limits-and-features. `examples/` has basic-setup, particle-system, earth-shader, custom-material. `REFERENCE.md` is the TSL cheatsheet.
- Signals: original 1.2K stars, 1.3K installs, last push 2026-04-10. JetBrains mirror pushed 2026-06-29. [P]
- Strengths: current three.js idiom (`three/webgpu`, not `examples/jsm`). Good for the TSL gap that the CloudAI-X set leaves. The JetBrains mirror gives an org-trust signal.
- Weaknesses: no R3F coverage. `WebGPURenderer` still needs a WebGL2 fallback decision. Pushed April 2026, so check whether it has kept up with three.js releases.
- Fit: **High** if any scene uses TSL or WebGPU. Medium otherwise.
- Source: `sources/skills-sh/JetBrains__skills__webgpu-threejs-tsl/`

### 3.2 EnzeD/r3f-skills — React Three Fiber
- Link: https://github.com/EnzeD/r3f-skills. Install: `npx skills add EnzeD/r3f-skills@r3f-fundamentals` (and `r3f-shaders`, `r3f-animation`, `r3f-postprocessing`, `r3f-loaders`, `r3f-physics`, ...).
- What: About 10 short skills for R3F and drei. The fundamentals skill states a Fiber 9 and React 19 baseline.
- Outline: fundamentals (82 lines): choose the baseline, minimal scene, scene and type boundaries, render-loop decisions, renderer and ownership pitfalls, verify, sources. Shaders (88 lines): select the shader path (GLSL vs TSL), animated material, uniforms and compilation, patching built-in materials.
- Signals: 128 stars, 1.7-1.9K installs per skill, pushed 2026-08-31. [P]
- Strengths: tells the agent to inspect the lockfile before choosing APIs and not to upgrade the project. Matches Next 16 and React 19 (Fiber 9). Has a "Sources" section and a "Verify" step in each skill.
- Weaknesses: terse. The skills are routing notes with a few references, not full tutorials.
- Fit: **High**. Best R3F baseline for this stack.
- Source: `sources/skills-sh/EnzeD__r3f-skills__r3f-fundamentals/`, `...__r3f-shaders/`

### 3.3 CloudAI-X/threejs-skills — vanilla three.js
- Link: https://skills.sh/cloudai-x/threejs-skills/threejs-fundamentals. Install: `npx skills add CloudAI-X/threejs-skills@threejs-fundamentals` (also `-shaders`, `-postprocessing`, `-animation`, `-geometry`, `-materials`, `-lighting`, `-loaders`, `-textures`, `-interaction`).
- What: Ten tutorial-style skills of 400-640 lines each covering core three.js.
- Outline: fundamentals (scene, cameras, `WebGLRenderer`, Object3D, coordinate system, math utilities, cleanup, responsive canvas, loading manager). Shaders (ShaderMaterial vs RawShaderMaterial, uniforms, fresnel, dissolve, `onBeforeCompile`, GLSL built-ins). Postprocessing (EffectComposer, bloom, SSAO, DOF, custom ShaderPass).
- Signals: 3.6K stars, 11-18K installs each, created 2026-01-19, pushed 2026-07-09. Most installed 3D skill on the registry. [P]
- Strengths: broad, correct basics. Uses `three/addons/...` in the post-processing skill.
- Weaknesses: WebGL-only. No TSL, no `WebGPURenderer`, no R3F or drei (0 matches). The fundamentals skill still has a `three/examples/jsm` import. Imperative vanilla code needs translating to R3F components.
- Fit: **Medium**. Good as a reference for three.js concepts that R3F wraps, but it is the wrong idiom for a React site.
- Source: `sources/skills-sh/CloudAI-X__threejs-skills__threejs-fundamentals/`, `...-shaders/`, `...-postprocessing/`

### 3.4 MengTo/Skills@build-threejs-scroll-worlds — 3D scroll motion
- Link: https://github.com/MengTo/Skills. Install: `npx skills add MengTo/Skills@build-threejs-scroll-worlds`.
- What: Method for building one persistent 3D world driven by native scroll, with authored chapters, a scene ledger and camera as cinematography.
- Outline (309 lines): route the request, read build references, output-first, world bible, scene ledger, persistent spatial architecture, geometry/materials/lighting, map native scroll to deterministic state, camera as cinematography, interpolate from one conductor, interactions, semantic DOM story, progressive loading. References: `realtime-architecture.md`, `world-bible.md`, `quality-and-qa.md`, `kage-anatomy.md`; `demo/PROMPT.md`.
- Signals: repo 6.8K stars, pushed 2026-10-06, 1.3K installs. [P]
- Strengths: scroll mapped to deterministic state aligns with the repo's stance of one scroll-driven scene. Its only GSAP/Lenis mention is a pointer to a separate skill.
- Weaknesses: aimed at immersive worlds and microsites, not a marketing page with one hero. Vanilla three.js, no R3F. Large and prescriptive; may over-produce for small scenes. Other `MengTo` skills (`build-awwwards-quality-sites`, 2.6K installs) are adjacent but I did not read them.
- Fit: **Medium**. Use the architecture and QA references, not the whole workflow.
- Source: `sources/skills-sh/MengTo__Skills__build-threejs-scroll-worlds/`, `...__optimize-threejs-games/`, `...__3d-paper-material/`

### 3.5 millionco/react-doctor@improve-threejs — R3F audit
- Link: https://github.com/millionco/react-doctor. Install: `npx skills add millionco/react-doctor@improve-threejs`.
- What: Audit workflow for Three.js and R3F: recon, scan, triage by frame-loop leverage, visual audit, fix, validate.
- Outline (102 lines): covers frame-loop performance, GPU memory leaks, scene-graph correctness, z-fighting, shadow acne, colour space, resize handling; ends with "checks the scanner always misses".
- Signals: 15K-star repo, 299 installs. [P]
- Strengths: concentrated on the failures that actually hit R3F in production (disposal, colour space, resize). Strong maintainer.
- Weaknesses: depends on the React Doctor scanner (not checked for installability here). Audit-only, so it needs a build skill beside it.
- Fit: **Medium-High** as a review pass once scenes exist.
- Source: `sources/skills-sh/millionco__react-doctor__improve-threejs/`

### 3.6 czlonkowski/blender-web-3d-skill@blender-web-3d — Blender to web pipeline
- Link: https://github.com/czlonkowski/blender-web-3d-skill. Install: `npx skills add czlonkowski/blender-web-3d-skill@blender-web-3d`.
- What: Headless Blender CLI or Blender MCP, through a gltf-transform (meshopt, KTX2) export, into a Three.js/Next.js viewer with Vercel deploy.
- Outline (113 lines): start from assets, MCP vs headless CLI, the one-change iteration loop, reference files (`blender-scripting`, `threejs-viewer`, `performance`, `export-pipeline`, `baked-lighting`, `lookdev-and-shaders`), design lessons, and a screenshot-driven bug flow. Ships `assets/viewer/` template.
- Signals: 3 stars, 4 installs, created 2026-08-03. MIT, `compatibility` field lists Blender 4.x/5.x. [U] for quality beyond its own text.
- Strengths: the only skill I found that covers Blender through to a Next.js deployment, with measured-performance and baked-lighting references.
- Weaknesses: effectively no track record. Because the viewer template is in-repo it needs reading before use. Custom GLSL and a vanilla viewer, not R3F.
- Fit: **High on topic, low on trust.** Read before adopting; likely worth cherry-picking the references.
- Source: `sources/skills-sh/czlonkowski__blender-web-3d-skill__blender-web-3d/`

### 3.7 vladmdgolam/agent-skills@blender-mcp — Blender MCP + glTF export
- Link: https://github.com/vladmdgolam/agent-skills. Install: `npx skills add vladmdgolam/agent-skills@blender-mcp`. **MCP engine:** `ahujasid/blender-mcp` (31K stars, pushed 2026-10-06).
- What: How to use the Blender MCP tools (`get_scene_info`, `execute_python`, screenshot), export gotchas, and a glTF optimization path.
- Outline (675 lines): tool selection, health check, complete export workflow (inspect scene, verify materials, headless export, gltf-transform optimize). References: `asset-integrations.md` (PolyHaven, Sketchfab, Hyper3D, Hunyuan3D), `errors.md`, `texture-optimization.md`.
- Signals: 9 stars, 2.2K installs, pushed 2026-10-14. [P]
- Strengths: concrete about what is lost in glTF export (material mapping, textures). The install count is much higher than the star count suggests.
- Weaknesses: 675 lines is long for a skill body. Single maintainer.
- Fit: **High** for Blender asset work that ends in R3F.
- Source: `sources/skills-sh/vladmdgolam__agent-skills__blender-mcp/`

### 3.8 RobLe3/cc-blender-skill — Blender orchestration
- Link: https://github.com/RobLe3/cc-blender-skill. Install: `npx skills add RobLe3/cc-blender-skill@blender-pro-workflow` (plus `text-to-blender`, `blender-lighting`, `blender-cameras`, `blender-uv-texturing`).
- What: A set of Blender MCP skills with a routing orchestrator and an 11-step assembly order (block-out, camera, light, forms, materials, detail, render, composite, export).
- Outline: pro-workflow (213 lines) with recipes and critique protocol. text-to-blender (262 lines): world reset, visual validation checkpoint, intent-to-sub-skill routing, code-execution rules.
- Signals: 98 stars, about 1K installs each, pushed 2026-10-12. [P]
- Strengths: forces a visual validation step. Wide coverage (lighting, cameras, UV).
- Weaknesses: aimed at renders and illustration, not web delivery. Pro-workflow and text-to-blender are large. Cross-skill "harmonization" adds overhead.
- Fit: **Medium** for hero stills or turntables, not for web-ready assets.
- Source: `sources/skills-sh/RobLe3__cc-blender-skill__blender-pro-workflow/`, `...__text-to-blender/`

### 3.9 ifBars/blender-agent-studio@blender-rendering-workflow — Blender render
- Link: https://github.com/ifBars/blender-agent-studio. Install: `npx skills add ifBars/blender-agent-studio@blender-rendering-workflow`.
- What: Reproducible still, turntable and sequence renders: render contract, denoising choice, compositor, and a completion gate.
- Signals: 84 stars, 82 installs, pushed 2026-10-16. [P]
- Strengths: product-visualization focus (turntables), contract-style discipline.
- Weaknesses: small install base. Overlaps RobLe3 for scene setup.
- Fit: **Medium**, for producing marketing stills or video loops from Blender.
- Source: `sources/skills-sh/ifBars__blender-agent-studio__blender-rendering-workflow/`

### 3.10 scenario-labs/skills@scenario-blender-expert — Blender router
- Link: https://github.com/scenario-labs/skills. Install: `npx skills add scenario-labs/skills@scenario-blender-expert`.
- What: Router and agent protocol for any Blender work via Python or MCP, with a "version traps" section and shared scripts.
- Outline (83 lines): execution channel, the expert loop, persona pipelines, shared toolkit (`scripts/`, tested on 5.2.1), version traps.
- Signals: repo 1.0K stars, created 2026-08-12, 328 installs on this skill. [P]
- Strengths: compact. Version traps address the common Blender 4/5 API breakage, which most older skills ignore.
- Weaknesses: the repo is a broad multi-DCC collection from one vendor (check for product ties). Domain sub-skills not read.
- Fit: **Medium**.
- Source: `sources/skills-sh/scenario-labs__skills__scenario-blender-expert/`

### 3.11 linegel/threejs-complete-set-of-skill — WebGPU/TSL set
- Link: https://github.com/linegel/threejs-complete-set-of-skill. Install: `npx skills add linegel/threejs-complete-set-of-skill@threejs-choose-skills`.
- What: About 15 WebGPU/TSL skills (bloom, particles, procedural materials, sky, camera rigs, debugging, visual validation) behind a router skill.
- Outline: choose-skills (179 lines): fix the contract, select causal owners, close handoffs, prove the composed route. visual-validation (141 lines): predeclare claims, freeze the run, capture the mechanism, measure, exercise state, claim-scoped verdicts.
- Signals: 10 stars, about 125 installs each, created 2026-07-04, pushed 2026-09-24. [U]
- Strengths: the visual-validation method is rigorous and reusable.
- Weaknesses: WebGPU/TSL only. Heavy process language. Little adoption.
- Fit: **Low-Medium**. The validation skill may be worth borrowing.
- Source: `sources/skills-sh/linegel__threejs-complete-set-of-skill__threejs-choose-skills/`, `...__threejs-visual-validation/`

### 3.12 skinnye/3d-web-pack@optimize-3d-assets — glTF pipeline
- Link: https://github.com/skinnye/3d-web-pack. Install: `npx skills add skinnye/3d-web-pack@optimize-3d-assets`.
- What: inspect, then one-shot optimize with gltf-transform, gltfpack/meshopt, Draco and KTX2, optionally convert to an R3F component with gltfjsx, then wire runtime decoders in drei.
- Signals: 5 stars, 40 installs, created 2026-06-14. [U]
- Strengths: 60 lines, the correct tool chain, and the R3F decoder step.
- Weaknesses: tiny repo. Its sibling `scroll-3d-scene` uses Lenis and GSAP ScrollTrigger.
- Fit: **Medium** (the short checklist is easy to verify yourself).
- Source: `sources/skills-sh/skinnye__3d-web-pack__optimize-3d-assets/`, `...__scroll-3d-scene/`

### 3.13 gamedev-skills/awesome-gamedev-agent-skills@threejs-gltf-loading
- Link: https://github.com/gamedev-skills/awesome-gamedev-agent-skills. Install: `npx skills add gamedev-skills/awesome-gamedev-agent-skills@threejs-gltf-loading`.
- What: Vanilla three.js GLTFLoader recipes: load and frame, AnimationMixer, cross-fade, DRACO, find a named part.
- Signals: 1.5K-star repo, 3.9K installs, created 2026-06-24. [P]
- Weaknesses: vanilla, game framing, no R3F `useGLTF`.
- Fit: **Low-Medium**.
- Source: `sources/skills-sh/gamedev-skills__awesome-gamedev-agent-skills__threejs-gltf-loading/`

### 3.14 freshtechbro/claudedesignskills (react-three-fiber, blender-web-pipeline) — older, broad
- Link: https://github.com/freshtechbro/claudedesignskills. Install: `npx skills add freshtechbro/claudedesignskills@react-three-fiber`.
- What: 1,079-line R3F skill and a 613-line Blender web pipeline skill (bpy glTF export, batch scripts, decimation, baking).
- Signals: 1.1K stars, 3.2-4.3K installs, last push 2025-11-20. [P]
- Weaknesses: stale (about 11 months before the fetch date). The R3F skill mentions GSAP 4 times, so it likely pairs with GSAP animation. Very long. Copied into other accounts (`avabillions2040`).
- Fit: **Low**, superseded by EnzeD and the Blender skills above.
- Source: `sources/skills-sh/freshtechbro__claudedesignskills__react-three-fiber/`, `...__blender-web-pipeline/`

### 3.15 earthtojake/text-to-cad@cad — CAD
- Link: https://github.com/earthtojake/text-to-cad. Install: `npx skills add earthtojake/text-to-cad@cad`.
- What: Parametric CAD via `cadgen` with STEP/STL/3MF/GLB export and a CAD Viewer.
- Signals: 20.9K stars, 13K installs, pushed 2026-10-16. [P]
- Fit: **Low**. A mechanical/printing tool. It can emit GLB, but it is not a web 3D design skill.
- Source: `sources/skills-sh/earthtojake__text-to-cad__cad/`

### 3.16 Remaining fetched sources (reviewed but not outlined)
`cazala/webgpu-skill@webgpu` (raw WebGPU/WGSL; not three.js), `MengTo/Skills@3d-paper-material` and `@optimize-threejs-games` (26-line stub), `gabremoku/immersive-3d-web`, `vercel-labs/json-render@react-three-fiber` (documents the json-render R3F package, not a general R3F skill), `Impertio-Studio/...@threejs-impl-react-three-fiber` (267 lines, 120 installs, thin repo), `full-stack-skills/threejs-skills@threejs-node-tsl` (84-line doc map), `PlayableIntelligence/game-creator@threejs-perf` (game instancing), `nexu-io/open-design@threejs` (43-line pointer), `arjun988/blender-skills` (@export-pipeline, @asset-optimization), `ra100/blender-claude-plugin@blender-python-scripting` (Blender 5.1), `HKUDS/CLI-Anything@cli-anything-blender`, `affaan-m/ECC@blender-motion-state-inspection`, `SFKislev/Flue@Blender`.

## 4. Dissent, red flags, gaps

**Red flags**
- Install counts mislead. `hyperframes@three` (69K) is a video-frame adapter. `superpowers@*` copies are repackaged across several accounts. Count-matched families (`full-stack-skills`, `cesartevisual`, `bbeierle12`, `linegel`) are bulk sets with 5-130 installs.
- Everything three.js here is community-authored. No pmndrs or three.js-org skill showed up. The nearest "official" signal is the JetBrains mirror of a community skill.
- GSAP/Lenis: `skinnye@scroll-3d-scene`, `gabremoku@immersive-3d-web` and `freshtechbro@react-three-fiber` assume GSAP, and this repo uses Motion only. `MengTo@build-threejs-scroll-worlds` points to a separate GSAP skill but does not itself depend on it.
- WebGL-only vs WebGPU: CloudAI-X targets `WebGLRenderer` only. The TSL/WebGPU skills assume `WebGPURenderer`. A project must pick one or accept the fallback cost.
- Staleness check not done: I did not confirm which three.js release any skill targets beyond import paths.

**Gaps**
- Spline: only `freshtechbro` and `sickn33`/`codecrafter98` variants (10-2.6K installs). None read.
- Text-to-3D: `meshy-dev/meshy-3d-agent` (908 installs) and `fal-3d` variants not read; Meshy needs a paid API.
- No skill found specifically for drei `ScrollControls`, `MeshTransmissionMaterial` or Next.js SSR and dynamic import of R3F canvases.
- I read headings, frontmatter and sampled bodies. I did not run any skill or check it against three.js docs. Nothing was installed, and no scripts were executed.
- skills.sh security-audit badges (Gen Agent Trust Hub, Socket, Snyk) were only seen on the `hyperframes` page. I did not check them for the finalists.
