# Best agent skills for three.js, 3D design and Blender — research report

Fetched and compiled 2026-10-16. Three parallel Sonnet lanes searched skills.sh (`npx skills find`),
X (`xrelay`) and GitHub (`ghrelay`, plus web-curated lists). A separate verifier then checked the
load-bearing claims (`factcheck.md`: 15 claims; 12 confirmed, 1 partly refuted, 1 refuted, 1 a data answer; all corrections applied below). Nothing was installed and no downloaded script was run.

- Lane files, with full query logs, ranked tables and long outlines: `lane-skills-sh.md` · `lane-x.md` · `lane-github.md`
- Raw sources: `sources/<lane>/<owner>__<repo>__<skill>/`. Each folder holds SKILL.md, its references and `SOURCE.txt` (URL, commit, date). There are 99 skill folders in all.
- Discovery cross-feed between lanes: `shared-names.md`

Claim grades: [V] vendor/official · [B] independent measurement · [P] practitioner/metadata · [U] unverified.

---

## The answer

**No official skill exists for any of the three areas.** There is nothing from pmndrs, mrdoob/three.js or
Blender.org on skills.sh or GitHub, so every pick below is community-authored. Most repos are under 9 months old and have
one maintainer. Install counts and stars measure reach, not quality: `heygen-com/hyperframes@three` has 69K
installs but is a video-frame adapter. **Adopt a few small, well-targeted skills instead of the big packs.**

For eagle-website (Next 16, React 19, Motion only, one scroll-driven scene), the shortlist is:

| Area | Adopt | Conditional | Reference only |
|---|---|---|---|
| **three.js / R3F** | `EnzeD/r3f-skills` · `vladmdgolam/agent-skills@threejs-perf-loading` · `millionco/react-doctor@improve-threejs` | `dgreenheck/webgpu-claude-skill@webgpu-threejs-tsl` (only if you choose WebGPU/TSL) · `scottstts/Threejs-Awesome-Graphics-Agent-Skills` (5 skills, selectively) | `CloudAI-X/threejs-skills` |
| **3D design / pipeline** | `MengTo/Skills@build-threejs-scroll-worlds` (the method; swap its scroll layer for Motion) · `skinnye/3d-web-pack@optimize-3d-assets` | `czlonkowski/blender-web-3d-skill` (vet first) | `img2threejs/img2threejs` · `majidmanzarpour/threejs-game-skills` (QA and scorecard) |
| **Blender** | One MCP engine (`ahujasid/mcp-for-blender` or the official Blender Lab MCP) + `vladmdgolam/agent-skills@blender-mcp` + `scenario-labs/skills@scenario-blender-expert` | `EL4CTEO/blender-skills` (core, export, asset-qa) · `kajisho5/blender-skill` | `RobLe3/cc-blender-skill` and `ifBars/blender-agent-studio` (renders and turntables) |

**Every scroll-3D skill found defaults to GSAP and/or Lenis.** None of them teaches `motion/react`. Any scroll guidance
you adopt has to be overridden by `docs/MOTION-DESIGN-SYSTEM.md`. This was found independently by all three lanes.

---

## 1. three.js / React Three Fiber

### 1.1 EnzeD/r3f-skills — **adopt** (R3F baseline)
- **Link / install:** https://github.com/EnzeD/r3f-skills · `npx skills add EnzeD/r3f-skills` (11 skills)
- **What:** short routing skills for R3F and drei. This is the only R3F set that states a Fiber 9 + React 19 baseline.
- **Outline (r3f-fundamentals):**
  - Choose the baseline: read the manifest and lockfile first; Fiber 9/React 19 vs 8/18
  - Minimal scene
  - Scene and type boundaries
  - Render-loop decisions
  - Renderer and ownership pitfalls (`dispose={null}`, Strict Mode)
  - Verify
  - Sources
- **The other skills:** animation, geometry, interaction, lighting, loaders, materials, physics (Rapier 2), postprocessing, shaders (GLSL vs TSL path), textures. Each is about 80 lines and ends in Verify + Sources.
- **Signals:** 128★, about 1.8K installs per skill, pushed 2026-08-31, **no licence file**. [P]
- **+** Version-aware, and it does not upgrade the project. **−** Terse routing notes rather than recipes; no licence, so don't vendor it.
- **Fit: high.**
- **Source:** `sources/github/EnzeD__r3f-skills__r3f-skills/`, `sources/skills-sh/EnzeD__r3f-skills__r3f-{fundamentals,shaders}/`

### 1.2 vladmdgolam/agent-skills @threejs-perf-loading — **adopt** (perf for marketing scenes)
- **Link / install:** https://github.com/vladmdgolam/agent-skills · `npx skills add vladmdgolam/agent-skills --skill threejs-perf-loading`
- **Outline (565 lines):**
  - Loading and warmup: hide shader compile and texture decode behind the preloader
  - Render-loop cost discipline
  - Adaptive quality (DPR, effects)
  - Scroll and input smoothing: cap the step, not the value
  - Ownership of the transmission/glass render target
  - Frame-attribution tooling
- **Signals:** 9★, MIT, pushed 2026-10-14, one maintainer. [P]
- **+** Studio-grade practice that maps directly onto a hero scene. **−** Tiny repo, long single file.
- **Fit: high.**
- **Source:** `sources/github/vladmdgolam__agent-skills__threejs-perf-loading/`

### 1.3 millionco/react-doctor @improve-threejs — **adopt** (review pass)
- **Link / install:** https://github.com/millionco/react-doctor · `npx skills add millionco/react-doctor --skill improve-threejs`
- **Outline:**
  - Recon: map every `useFrame`/RAF hot path
  - Scan with `npx react-doctor@latest --verbose`, read-only
  - Triage by frame-loop leverage
  - Visual audit
  - Fix
  - Validate
  - "Checks the scanner always misses": z-fighting, shadow acne, colour space, resize, GPU disposal
- **Signals:** about 15K★ active org repo, licence NOASSERTION (non-standard); 299 installs. [P]
- **+** A process skill, so it doesn't go stale on API churn. **−** It runs an **unpinned** `npx react-doctor@latest` at run time, so review it before allowing the call.
- **Fit: high once a scene exists.**
- **Source:** `sources/github/millionco__react-doctor__improve-threejs/`

### 1.4 dgreenheck/webgpu-claude-skill @webgpu-threejs-tsl — **conditional** (WebGPU + TSL)
- **Link / install:** https://github.com/dgreenheck/webgpu-claude-skill · `npx skills add dgreenheck/webgpu-claude-skill@webgpu-threejs-tsl`. `JetBrains/skills` holds a lightly edited mirror (about 22 diff lines, credited to dgreenheck), so prefer the original.
- **Outline:**
  - SKILL.md is an index: imports from `three/webgpu` + `three/tsl`, `await renderer.init()`, node materials
  - `docs/`: core concepts, materials, compute shaders, post-processing, WGSL integration, device loss, limits
  - `examples/`: particles, earth shader, custom material
  - `REFERENCE.md`: the TSL cheatsheet
- **Signals:** about 1.25K★, about 1.3K installs, **last push 2026-04-10**, no licence. The author is a known three.js educator. [P]
- **+** Current three.js idiom. **−** Six months without a push on a fast-moving API. It needs a WebGL2 fallback decision. No R3F coverage.
- **Fit: medium,** and only if you pick WebGPU/TSL.
- **Source:** `sources/github/dgreenheck__webgpu-claude-skill__webgpu-threejs-tsl/`, `sources/skills-sh/JetBrains__skills__webgpu-threejs-tsl/`

### 1.5 scottstts/Threejs-Awesome-Graphics-Agent-Skills — **conditional, selective**
- **Link / install:** https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills (24 skills, router-led, 78 reference files)
- **Take only these:**
  - `threejs-skill-router`
  - `threejs-bloom`
  - `threejs-image-pipeline` (GTAO, tone mapping, LUT)
  - `threejs-exposure-color-grading`
  - `threejs-visual-validation`
- **Signals:** 913★, MIT, created 2026-06-19, pushed 2026-10-15. [P]
- **−** Mostly showpiece effects (planets, oceans), and loading the whole pack is expensive in context.
- **Source:** `sources/github/scottstts__Threejs-Awesome-Graphics-Agent-Skills__threejs-awesome-graphics/`

### 1.6 CloudAI-X/threejs-skills — **reference only**
- **Link / install:** https://github.com/CloudAI-X/threejs-skills · `npx skills add CloudAI-X/threejs-skills` (10 skills)
- **Outline:** fundamentals, geometry, materials, lighting, textures, loaders, animation, interaction, shaders (ShaderMaterial, `onBeforeCompile`), postprocessing (EffectComposer, bloom, SSAO, DOF).
- **Signals:** about 3.6K★, **13.5–18.1K installs each, the most-installed 3D skill** (`threejs-animation` 18.1K, `-fundamentals` 15K, `-shaders` 13.5K), and the most promoted on X. No licence. Star-burst flag. Unanswered issues. Pushed 2026-07-09, but every visible commit is dated 2026-01-19. [P]
- **−** Built around `WebGLRenderer`/GLSL, with no R3F, no drei and no TSL. The only WebGPU content is one "WebGPU Post-Processing" section. Imperative code would need translating to components.
- **Use:** concept reference only.
- **Source:** `sources/github/CloudAI-X__threejs-skills__threejs-skills/`, `sources/x/CloudAI-X__threejs-skills__threejs-all/`

**Also seen and not recommended:**
- `linegel/threejs-complete-set-of-skill`: WebGPU/TSL only, 10★. Its visual-validation method is worth borrowing.
- `OpenAEC-Foundation/Three.js-Claude-Skill-Package`: 21★, r160+, mixed renderers.
- `openai/plugins@react-three-fiber-game`: game architecture.
- `vercel-labs/json-render@react-three-fiber`: only for json-render users.
- `AThevon/genjutsu@threejs-r3f`: bundled with GSAP/framer motion.
- `freshtechbro/claudedesignskills`: **stale since 2025-11-20**, R3F 8, GSAP-first.
- `zebbern r3f-best-practices`: not reviewed in depth.

---

## 2. 3D design and asset pipeline

### 2.1 MengTo/Skills @build-threejs-scroll-worlds — **adopt the method**
- **Link / install:** https://github.com/MengTo/Skills (`agent-skills/web-design/…`) · `npx skills add MengTo/Skills --skill build-threejs-scroll-worlds`
- **What:** one persistent 3D world whose camera, light, fog and copy evolve across scroll chapters. Native scroll is mapped to normalized, reversible state through **one conductor**.
- **Outline:**
  - Route the request
  - Read the build references
  - Start from the output
  - World bible
  - Scene ledger
  - One persistent spatial architecture
  - Geometry, materials, lighting
  - Map native scroll to deterministic state
  - Camera as cinematography
  - Interpolate from one conductor
  - Interactions that don't fight scroll
  - Semantic DOM story
  - Progressive loading
  - Measurable performance budget
  - Reduced motion and failure
  - Verify the whole journey
  - Refs: `realtime-architecture.md`, `world-bible.md`, `quality-and-qa.md`, `scroll-conductor.js`
- **Signals:** repo about 6.8K★, MIT, pushed 2026-10-06, 1.3K installs. Strong X reach: the author has 189K followers and a 4K-like launch thread. [P]
- **+** The "single conductor, deterministic scroll state" model matches how `ScrubStage` already works.
- **−** Vanilla three.js, not R3F. Long (18.7 KB). For DOM choreography it routes to sibling skills (`cinematic-scroll-storytelling`, `gsap-scrolltrigger-storytelling`) that use **GSAP/Lenis**, so don't install those.
- **Fit: high** as a planning method; drive the conductor from Motion.
- **Source:** `sources/github/MengTo__Skills__build-threejs-scroll-worlds/` (also under skills-sh and x)

### 2.2 skinnye/3d-web-pack @optimize-3d-assets — **adopt** (GLB pipeline checklist)
- **Link / install:** https://github.com/skinnye/3d-web-pack · `npx skills add skinnye/3d-web-pack --skill optimize-3d-assets`
- **Outline (60 lines):**
  - Inspect
  - One-shot optimize (gltf-transform / gltfpack)
  - Targeted passes (meshopt, Draco, KTX2)
  - `gltfjsx` to an R3F component
  - Runtime decoders in drei
  - Verify and report against targets
- **Signals:** 5★, 40 installs, MIT, created 2026-06-14. [U]
- **+** Correct toolchain and short enough to check yourself. **−** Its siblings `scroll-3d-scene` (Lenis + GSAP) and `scaffold-3d-site` (Vite-first) are a **no**.
- **Source:** `sources/skills-sh/skinnye__3d-web-pack__optimize-3d-assets/`

### 2.3 czlonkowski/blender-web-3d-skill — **conditional** (closest to the exact use case, no track record)
- **Link / install:** https://github.com/czlonkowski/blender-web-3d-skill · `npx skills add czlonkowski/blender-web-3d-skill@blender-web-3d`
- **Outline (113 lines + 6 refs):**
  - Start from the assets
  - MCP vs headless CLI
  - One-change iteration loop (change → export → optimise → view)
  - Refs: blender-scripting, export-pipeline (gltf-transform, meshopt/KTX2), threejs-viewer, performance, baked lighting, lookdev/shaders (AgX colour)
  - Design lessons
  - Debugging from a screenshot
  - Ships an `assets/viewer/` template
- **Signals:** 3★, 4 installs, MIT, created 2026-08-03. [U]
- **−** Vanilla viewer with custom GLSL, not R3F. Read it before trusting the template; most likely you'll cherry-pick its references.
- **Source:** `sources/github/czlonkowski__blender-web-3d-skill__blender-web-3d/`

### 2.4 Reference only
- **img2threejs/img2threejs:** turns a reference image into a procedural three.js model behind quality gates. This is the original: about 18.2K★, Apache-2.0, created 2026-07-15, with independent X posts. `jangtrinh/design-os-3d-blender` (96★) only vendors a copy of it.
  - Heavy: a 33 KB SKILL.md, a harness, and a "mandatory local-state gate".
  - The output is code rather than a GLB, and it leans towards characters.
  - Could be useful to recreate a hero object from a brand image.
  - Source: `sources/x/img2threejs__img2threejs__img2threejs/`
- **majidmanzarpour/threejs-game-skills:** `aaa-graphics-builder` (a 10-category render scorecard), `qa-release` (an evidence manifest of captures, PASS/FAIL) and `debug-profiler`.
  - The QA loop transfers to marketing scenes.
  - The rest is game-specific and needs a paid Tripo or ElevenLabs key.
  - Source: `sources/x/majidmanzarpour__threejs-game-skills__game-skills/`
- **Skip:**
  - `sickn33/agentic-awesome-skills@3d-web-experience`: a generic mirror, though it has a usable Spline-vs-R3F decision tree.
  - `gabremoku/immersive-3d-web`: GSAP.
  - `earthtojake/text-to-cad`: mechanical CAD.
  - `SkylarKitchen@3d-assembly-manual`: niche.
  - Spline skills: not read, a gap.

---

## 3. Blender

**Choose one MCP engine per project.** The two engines expose different tool names.
- **Community: `ahujasid/mcp-for-blender`** (formerly `blender-mcp`). About 31K★, MIT. It includes the Poly Haven, Sketchfab and Hyper3D integrations, and most skills target it. [P]
- **Official: Blender Lab MCP.** Source: https://projects.blender.org/lab/blender_mcp; docs: https://www.blender.org/lab/mcp-server/. It is packaged as `NousResearch/hermes-official-plugins@blender`, pinned to commit `2cea8d56` (v1.0.3) and needing Blender 5.1+. That skill is a 44-line wrapper. Blender's own page warns that the server runs LLM-generated code with no guards. [V]
- A token-lean fork, `bpy-dev/blender-mcp`, claims 15% of the tokens. That figure is self-reported and not reproduced. **Watchlist.**

### 3.1 vladmdgolam/agent-skills @blender-mcp — **adopt** (Blender → glTF for the web)
- **Link / install:** https://github.com/vladmdgolam/agent-skills · `npx skills add vladmdgolam/agent-skills --skill blender-mcp`
- **Outline (675 lines + 3 refs):**
  - Tool selection
  - Health check first
  - Full export workflow: inspect, verify materials, export via **headless CLI** (MCP times out on exports), optimise with gltf-transform, validate
  - Critical rules: "Never use gltf-transform `optimize`", because it includes `simplify`, which destroys geometry; run `resize` / `webp` / `draco` as separate steps instead. Also: don't apply modifiers on export; export without Draco first; procedural textures don't export; quote paths
  - Refs: asset integrations, errors, texture optimisation
- **Signals:** 9★ but 2.2K installs, MIT, pushed 2026-10-14. [P]
- **+** Hard-won failure modes for exactly the hand-off from Blender to R3F. Pairs with §2.2.
- **Fit: high.**
- **Source:** `sources/github/vladmdgolam__agent-skills__blender-mcp/`

### 3.2 scenario-labs/skills @scenario-blender-expert — **adopt** (best for Blender 5.x API drift)
- **Link / install:** https://github.com/scenario-labs/skills/tree/main/skills/dcc/blender · `npx skills add scenario-labs/skills@scenario-blender-expert`
- **Outline (router, 83 lines):**
  - Execution channel (Python or MCP)
  - The expert loop
  - Persona pipelines
  - Shared `scripts/` (tested on Blender 5.2.1)
  - **Version traps that break remembered code**
- **Sub-skills:** geometry nodes, lighting/rendering, hard-surface, retopology, UV/bake, rigging, and more.
- **Signals:** repo about 1K★, MIT. The vendor launch thread has 17.7K likes. Targets Blender 5.2 LTS. [V]
- **Resolved dissent:** the GitHub lane rated it vendor-tied. The fact-check found that it **needs no Scenario account or API key**; it runs through headless Blender Python or any MCP bridge. Only the sibling `scenario-3d` skill needs Scenario's MCP, so skip that one.
- **Source:** `sources/x/scenario-labs__skills__blender-expert/`, `sources/skills-sh/scenario-labs__skills__scenario-blender-expert/`

### 3.3 EL4CTEO/blender-skills — **conditional, watchlist** (Blender 5.x, brand new)
- **Link / install:** https://github.com/EL4CTEO/blender-skills (20 skills)
- **Take:**
  - `blender-core`: a router covering the 5.x API breakages
  - `blender-export-pipelines`: a glTF/GLB web preset with meshopt, Draco and WebP
  - `blender-asset-qa`
- **Signals:** 44★, MIT, **created 2026-10-14**. [U]
- **Source:** `sources/github/EL4CTEO__blender-skills__*/`

### 3.4 kajisho5/blender-skill — **conditional, watchlist** (headless GLB budget checks)
- **Link / install:** https://github.com/kajisho5/blender-skill · `npx blender-skill`
- **What:** a `blender -b` pipeline: inspect, convert, optimise (decimate, texture caps, LOD), bake, turntable, then validate against three.js/WebXR budgets as PASS/WARN/FAIL. 13 stdlib-Python tools, no cloud.
- **Signals:** 0★, single author, v0.31. **Review the scripts and use `--dry-run` first.** [U]
- **Source:** `sources/x/kajisho5__blender-skill__blender-skill/`

### 3.5 For marketing renders rather than web assets
- **`RobLe3/cc-blender-skill`:** about 1K installs per skill and 98★. It is a 30-skill MCP orchestrator with an 11-step assembly order and a forced visual-validation step.
  - Take `blender-export` (10 recipes and a polycount table) and `blender-pro-workflow`.
  - Source: `sources/github/RobLe3__cc-blender-skill__*/`
- **`ifBars/blender-agent-studio@blender-rendering-workflow`:** a render contract for reproducible stills and turntables. 84★.
  - Source: `sources/skills-sh/ifBars__blender-agent-studio__blender-rendering-workflow/`

**Skip:**
- `arjun988/blender-skills`: 188 SKILL.md files with style packs; context bloat.
- `QwenLM/Qwen-MM-Plugins@blender`: a single 12 KB file.
- `freshtechbro@blender-web-pipeline`: stale.
- `thrixel/build-world`: vendor assets, Unreal.
- `majidmanzarpour/blender-game-skills`: game-oriented.

---

## 4. Cross-cutting findings

- **Motion vs GSAP:** see the answer above. It is the biggest compatibility issue for this repo.
- **Vanilla vs R3F:** the most popular sets are vanilla `WebGLRenderer`. Only EnzeD is React 19 / Fiber 9 aware. Nothing covers Next.js SSR or `dynamic()` for R3F canvases, or drei `ScrollControls`. **This is a gap you would fill yourselves.**
- **WebGL vs WebGPU:** decide once. The TSL skills assume `WebGPURenderer`; the CloudAI-X set assumes WebGL.
- **Licences:** CloudAI-X, dgreenheck, EnzeD and openai/plugins have no licence file. They are fine to install locally but must not be vendored into the repo.
- **Star validity:** ghrelay flagged star bursts on CloudAI-X, majidmanzarpour, react-doctor and ahujasid. skills.sh has bulk and mirror publishers (`superpowers` copies, `avabillions2040`, `raptoravis`, `sickn33`), and none of them were ranked.
- **X is showcase-heavy:** most "Opus built this in Blender" posts link no repo. Seven finalists were traced to primary sources; posts that link no repo are graded [U] and excluded.

## 5. Suggested install set (when you want it)

Project scope, not global. **Nothing has been installed.**

```bash
npx skills add EnzeD/r3f-skills
npx skills add vladmdgolam/agent-skills --skill threejs-perf-loading
npx skills add vladmdgolam/agent-skills --skill blender-mcp
npx skills add scenario-labs/skills@scenario-blender-expert
npx skills add millionco/react-doctor --skill improve-threejs
npx skills add MengTo/Skills --skill build-threejs-scroll-worlds
npx skills add skinnye/3d-web-pack --skill optimize-3d-assets
# + one Blender MCP engine (community mcp-for-blender, or official Blender Lab MCP)
```

## 6. Gaps

- Spline skills were not read.
- Text-to-3D (Meshy, fal, Tripo) was not read. All of these need paid APIs.
- No skill was executed or checked line by line against the current three.js docs.
- skills.sh security-audit badges were not checked for the finalists.
- Three X threads were truncated at 40 replies.
- The 1,131-reply Scenario launch thread was not read in full.
