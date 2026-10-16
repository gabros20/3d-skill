# Sources

Purpose: Record which community skills and primary docs informed each area, under which licence, and whether they were adapted or only inspired the text.

Read when:
- Someone asks where a rule or technique came from, or whether text may be reused.
- Adding a reference that draws on a new outside source.

Skip when:
- Doing 3D work; no runtime decision depends on this file.

Inputs:
- The area or rule in question.

Produces:
- A provenance answer; a new row when a source is added.

## Contents

- Front door · Shared · three.js, R3F, shaders · Scroll and design · Assets and Blender · Realism · Engines · Optional · Primary documentation

Every reference is written in this skill's own words. **Adapted** = MIT, Apache-2.0 or ISC source whose ideas were rewritten, never copied. **Inspired only** = no licence, NOASSERTION, AGPL or vendor docs: ideas informed the text, nothing was copied or vendored. Surveyed 2026-10-16; the long form with commits and dates is the repository's `SOURCES.md`.

## Front door: intake, references, brief

| Source | Licence | Use |
|---|---|---|
| mattpocock/skills `grilling` | MIT | adapted: frontier rounds, a recommended answer per question |
| addyosmani/agent-skills `interview-me` | MIT | adapted: hypothesis plus confidence, restate and explicit yes |
| calesthio/generative-media-skills `storyboard-previsualization` | MIT | adapted: intake checklist, lowest useful fidelity |
| img2threejs/img2threejs (and the jangtrinh fork) | Apache-2.0 | adapted: observe before infer, flag what one view hides |
| wuyoscar/gpt-image2-skill, caph-dev, soheik/agent-skills `video-scene-analyzer` | MIT | adapted: image dimensions, two-pass video funnel, shot enums |
| nikolasfaria/video-sharingan, NewTurn2017/make-awesome-video | MIT | adapted: measured camera language, cuts and palette passes, brief gates |
| charlie947/motion-graphics-skills, workspace-labs/frameflow, YanKaFei/art-aesthetic-vault | MIT | adapted: ask-first brief rules, storyboard questions, layered style decomposition |
| postplusai `reference-decode` | NOASSERTION | inspired only |
| Technicalflight/image-prompt-reverse | AGPL-3.0 | inspired only: nothing copied |

## Shared: preflight, preview, verification, performance, debug

| Source | Licence | Use |
|---|---|---|
| orchestrate-skill, scroll-animation-skill (same author) | own | house patterns: capabilities, propose-never-install, stale-stylesheet triage |
| vladmdgolam/agent-skills `threejs-perf-loading` | MIT | adapted: warm-up behind the preloader, adaptive quality |
| majidmanzarpour/threejs-game-skills `qa-release` | MIT | adapted: evidence manifest, scorecard |
| echris6/motion-video-kit, SamG-Coder/ThreeBrowserStudio, tallslab/threeforge | MIT | adapted: fresh-critic rounds, render and look after each stage, pixel-parity gate |
| mintdotgg/mint-threejs-skills | MIT | adapted: the dissent that browser and screenshot QA waits for user approval |
| donmccurdy/three-gltf-viewer; KhronosGroup/glTF-Sample-Viewer | MIT; Apache-2.0 | ideas only; the viewer was written fresh |
| millionco/react-doctor `improve-threejs` | NOASSERTION | inspired only: frame-loop triage |

## three.js, R3F, shaders

| Source | Licence | Use |
|---|---|---|
| scottstts/Threejs-Awesome-Graphics-Agent-Skills, OpenAEC/Impertio, zebbern | MIT | adapted: image pipeline, grading, R3F practice |
| linegel/threejs-complete-set-of-skill | ISC | adapted: visual-validation method |
| EnzeD/r3f-skills, CloudAI-X/threejs-skills, dgreenheck/webgpu-claude-skill, openai/plugins | none | inspired only |
| AThevon/genjutsu | NOASSERTION | inspired only |

## Scroll and design

| Source | Licence | Use |
|---|---|---|
| MengTo/Skills `build-threejs-scroll-worlds` | MIT | adapted: one conductor, exact and smooth state, world bible |
| scroll-animation-skill `video.md`, `sequences.md` (same author) | own | scrub encoding, seek and frame-sequence rules behind [scroll-video](scroll-video.md) |
| agiwhitelist/auteur | MIT | adapted: art direction committed in writing, anti-references |
| AirsupHQ/machine-skill, RobLe3/cc-blender-skill lighting | MIT | adapted: the critic's bar, lighting recipes |
| gabremoku/immersive-3d-web | none | inspired only: concept-to-form |

## Assets and Blender

| Source | Licence | Use |
|---|---|---|
| skinnye/3d-web-pack `optimize-3d-assets` | MIT | adapted: inspect, targeted passes, gltfjsx |
| vladmdgolam/agent-skills `blender-mcp` | MIT | adapted: headless export, no bare `optimize` |
| scenario-labs/skills, EL4CTEO/blender-skills, czlonkowski/blender-web-3d-skill | MIT | adapted: Blender 5.x traps, budgets, Blender-to-three hand-off |
| kajisho5/blender-skill, ifBars/blender-agent-studio, elithril blender-kiln | MIT | adapted: headless budget checks, render contract, MCP rules |
| meshy-dev/meshy-3d-agent | MIT | adapted: paid-job rules |
| ahujasid/mcp-for-blender; Blender Lab MCP | MIT; GPL-3.0 | recommended tools, no text taken |

## Realism: gap, toolbox, gate

| Source | Licence | Use |
|---|---|---|
| Andrew Woan (Codrops 2025); Lusion studio write-ups | articles | inspired only: bake recipe, texel density, offline plus live overlay |
| Wawa Sensei, Immersive Studios (YouTube) | videos | inspired only: when to bake, texture budgets |
| three.js forum threads by drcmda and donmccurdy | forum posts | inspired only: environment first, colour management, AgX base only |
| "Moving Frostbite to PBR" course notes (Lagarde, de Rousiers) | none stated | reference only: the gap taxonomy, nothing reproduced |
| Filament PBR docs; LearnOpenGL PBR/IBL | Apache-2.0 repo; CC BY-NC 4.0 | inspired only: split-sum IBL limits, BRDF terms |
| gkjohnson/three-gpu-pathtracer | MIT | recommended tool: the path-traced twin; API from its docs |

## Engines

| Source | Licence | Use |
|---|---|---|
| Spotvirtual, "Why we use Babylon.js instead of three.js" (2022) | article | inspired only: when Babylon's batteries pay off |
| Babylon.js docs; Khronos glTF 2.0 and the Blender glTF I/O | Apache-2.0 docs | adapted: Babylon loading, environment, PBR and lightmap notes; export facts measured by hand |
| gamefromscratch Babylon 9 review; Wawa Sensei; freeCodeCamp café course; Bruno Simon (2026 WebGPU/TSL course) | videos | inspired only: engine trade-offs, Blender-to-web practice |

## Optional: Spline, splats and XR, CAD

| Source | Licence | Use |
|---|---|---|
| Spline docs (MCP server, agent skill, export) | vendor docs | inspired only |
| sparkjsdev/spark docs; google/model-viewer | MIT; Apache-2.0 | adapted from library docs |
| meta-quest/agentic-tools `hz-iwsdk-webxr`; ahmettasdemirusa/threejs-product-skills | Apache-2.0; MIT | adapted: device gotchas, AR checklist |
| shi3z/sparkjs-skill | none | inspired only |
| earthtojake/text-to-cad, heyixuan2/bambu-studio-ai | MIT | adapted: CAD routing, the user starts the print |
| mdbritt/claudecad, mitsuhiko/openscad | Apache-2.0 | adapted: verification laws, multi-view checks |
| flowful-ai/cad-skill; santiagomoneta/orca-slicer | NOASSERTION; none | inspired only |

## Primary documentation (ground truth wins over every source above)

three.js docs, source and release notes (r186); pmndrs React Three Fiber 9, drei 10 and the v10
migration notes; Next.js App Router docs; Khronos glTF 2.0, PBR Neutral and KTX-Software; glTF
Transform and meshoptimizer (`gltfpack`) docs; Blender 5.x manual, Python API and release notes;
Blender Lab MCP docs; Spline, Spark and model-viewer docs; Apple AR Quick Look and WebXR; Motion,
GSAP and Lenis docs; FFmpeg filters; Playwright.
