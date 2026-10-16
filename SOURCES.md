# Sources

Provenance for the `3d` skill. Every reference is written in this repository's own words: nothing is copied, vendored or redistributed from the sources below. The per-area summary the runtime carries is [skills/3d/references/SOURCES.md](skills/3d/references/SOURCES.md); this file is the long form.

## Method

Surveyed 2026-10-16 by three parallel lanes (skills.sh `npx skills find`, X, GitHub) plus gap, reference-analysis, brief-intake and relay sweeps, then a refute-mode fact-check of 15 load-bearing claims (12 confirmed, 1 partly refuted, 1 refuted, 1 a data answer; corrections applied). Nothing was installed and no downloaded script was run. Raw material (each skill's `SKILL.md` and `SOURCE.txt` with URL, commit and date) lives in `docs/research/community-scan/sources/`; ranked tables and query logs in `docs/research/community-scan/`; ground-truth checks against primary docs in `docs/research/ground-truth-web3d.md` and `ground-truth-blender-pipeline.md`; per-area harvests in `docs/research/harvest/`.

No official skill exists from pmndrs, mrdoob/three.js or Blender.org for these areas; every source below is community-authored, mostly one maintainer and under nine months old. Stars and installs measure reach, not quality.

## Licence policy

- **Permissive (MIT, Apache-2.0, ISC):** ideas and structure may be adapted, always rewritten. Verified for the two Blender sources the scan first flagged for vetting: `czlonkowski/blender-web-3d-skill` is MIT and `elithril/blender-kiln` is MIT.
- **No licence, NOASSERTION, AGPL-3.0, vendor docs:** inspiration only; nothing carried over. This covers `EnzeD/r3f-skills`, `CloudAI-X/threejs-skills`, `dgreenheck/webgpu-claude-skill` (and its JetBrains mirror), `millionco/react-doctor` (NOASSERTION; its skill runs an unpinned `npx react-doctor@latest`, which this pack never does), `postplusai/reference-decode`, `Technicalflight/image-prompt-reverse` (AGPL-3.0), `flowful-ai/cad-skill` (NOASSERTION) and Spline's vendor docs.
- **Blender expansion sources (2026-10-17):** adapted, rewritten, never copied: `scenario-labs/skills` Blender domains (MIT: rigging, animation, hair, retopo, UV and bake, hard-surface, Grease Pencil, sculpt, Geometry Nodes), `EL4CTEO/blender-skills` (MIT: game and web delivery, 5.x notes), `FreedomIntelligence/BlenderLore` (Apache-2.0: verification phrasing), `ifBars/blender-agent-studio` (MIT: simulation and render contract), `terminalskills/skills` (Apache-2.0: compositing and VSE API traps), `ra100/blender-claude-plugin` (MIT: physics and driver snippets). Inspired only: `icesixgod` astra (MIT, reference-first acceptance). Not used: `edemaistre`, `xliuxjianx`, `ptrthomas` (unlicensed).
- **Primary docs and licence texts:** Blender manual and Python API; Poly Haven and ambientCG (CC0); Meshy and Tripo API docs. Texturing-tool licence notes drove the refuse list: Ubisoft CHORD (research-only), Hunyuan3D-2.1 (territory exclusion for the EU, UK and South Korea, and a 1M MAU cap), TRELLIS.2 native texture (NVIDIA non-commercial); StableGen, DeepBump and Material Maker licences were also read.
- **Recommended tools, no text taken:** `ahujasid/mcp-for-blender` (MIT; the former `blender-mcp`, renamed) and the official Blender Lab MCP (GPL-3.0, `projects.blender.org/lab/blender_mcp`). The Lab MCP v1.0.3 source was read as reference only; nothing was copied. PyPI `blender-mcp` is the community server, not the official one.
- `img2threejs/img2threejs` (Apache-2.0, created 2026-07-15) is the original; the `jangtrinh/design-os-3d-blender` copy is a vendored duplicate inside an MIT repo.
- Commit, licence and date per source are as recorded at fetch time; the per-area "adapted vs inspired" ruling is in the runtime SOURCES.md.

## Sources by lane

Short commit SHA as fetched on 2026-10-16 unless the lane file says otherwise. Licence as recorded in the source's `SOURCE.txt`.


### Front door: intake, brief, storyboards

| Source | Commit | Licence |
|---|---|---|
| 101-skills/superpowers `product-photography` | becc256 | none declared |
| 101-skills/superpowers `storyboard-creation` | becc256 | none declared |
| addyosmani/agent-skills `interview-me` | aeac41d | MIT |
| arjun988/blender-skills `camera-cinematography` | 8f778d2 | MIT |
| calesthio/generative-media-skills `cinematic-shot-direction` | 8c85352 | MIT |
| calesthio/generative-media-skills `lighting-direction` | 8c85352 | MIT |
| calesthio/generative-media-skills `production-design-direction` | 8c85352 | MIT |
| calesthio/generative-media-skills `storyboard-previsualization` | 8c85352 | MIT |
| calesthio/generative-media-skills `visual-style-direction` | 8c85352 | MIT |
| fal-ai-community/skills `cinematography` | 9ca8504 | none declared |
| mattpocock/skills `grill-me` | 49dd158 | MIT |
| mattpocock/skills `grilling` | 49dd158 | MIT |
| mattpocock/skills `to-spec` | 49dd158 | MIT |

### Reference analysis (images and video)

| Source | Commit | Licence |
|---|---|---|
| caph-dev/image-style-prompt-reverse-engineer | 27d248d | MIT |
| gxinxing/short-video-shot-analysis | aadd42f | none |
| mugnimaestra/video-frames-skill `video-frames` | f0d30f9 | none |
| nuyoah-ai-works/nuyoah-image-reverse-prompt | f56616e | MIT |
| pascalorg/skills `image-analysis` | 7be87e9 | none |
| postplusai/postplus-skills `reference-decode` | 61e0460 | NOASSERTION |
| soheik/agent-skills `video-scene-analyzer` | 167cf9d | LICENSE file in folder (unchecked) |
| woven-video/skills `analyze-video` | 203f35f | none |
| wuyoscar/gpt-image2-skill `get-prompt-from-image` | 9f8aa1a | MIT |

### Preview, QA and critic loops

| Source | Commit | Licence |
|---|---|---|
| AbubakrChan/product-launch-motion | b25b163 | MIT |
| NewTurn2017/make-awesome-video | f339689 | MIT |
| SamG-Coder/ThreeBrowserStudio `threebrowser-studio-mcp` | fc93ab1 | MIT |
| Technicalflight/image-prompt-reverse | e1988d5 | AGPL-3.0 |
| YanKaFei/art-aesthetic-vault | b3f20a5 | MIT |
| charlie947/motion-graphics-skills | 229022e | MIT |
| echris6/motion-video-kit `business-motion-film` | e4b1c00 | MIT |
| korovin-aa97/talkthrough-mcp `talkthrough` | 350ac6b | MIT |
| linegel/threejs-complete-set-of-skill `product-from-scratch` | e3c9563 | ISC |
| mintdotgg/mint-playground `README` | 5ab1b94 | MIT |
| mintdotgg/mint-threejs-skills | de7af44 | MIT |
| nikolasfaria/video-sharingan | c7c2458 | MIT |
| tallslab/threeforge `AGENTS` | 8ac4ceb | MIT |
| workerpro666-ctrl/aigc-director-five-lines | b0e08db | MIT |
| workspace-labs/frameflow | bc84e29 | MIT |

### three.js, R3F, Blender, assets (GitHub scan)

| Source | Commit | Licence |
|---|---|---|
| AThevon/genjutsu `threejs-r3f` | 1f518a7 | NOASSERTION |
| CloudAI-X/threejs-skills | b1c6230 | none |
| EL4CTEO/blender-skills `blender-asset-qa` | cd55d92 | MIT |
| EL4CTEO/blender-skills `blender-core` | cd55d92 | MIT |
| EL4CTEO/blender-skills `blender-export-pipelines` | cd55d92 | MIT |
| EL4CTEO/blender-skills `blender-game-optimization` | cd55d92 | MIT |
| EnzeD/r3f-skills | 4a11805 | none |
| MengTo/Skills `3d-orbit-inspect-demo` | 83a47fe | MIT |
| MengTo/Skills `build-threejs-scroll-worlds` | 83a47fe | MIT |
| NousResearch/hermes-official-plugins `blender-mcp-official` | b9371bf | wraps the official Blender Lab MCP; see factcheck.md |
| OpenAEC-Foundation/Three.js-Claude-Skill-Package `threejs-agents-model-optimizer` | 6c190f0 | MIT |
| OpenAEC-Foundation/Three.js-Claude-Skill-Package `threejs-agents-scene-builder` | 6c190f0 | MIT |
| OpenAEC-Foundation/Three.js-Claude-Skill-Package `threejs-errors-performance` | 6c190f0 | MIT |
| OpenAEC-Foundation/Three.js-Claude-Skill-Package `threejs-impl-drei` | 6c190f0 | MIT |
| OpenAEC-Foundation/Three.js-Claude-Skill-Package `threejs-impl-react-three-fiber` | 6c190f0 | MIT |
| OpenAEC-Foundation/Three.js-Claude-Skill-Package `threejs-impl-webgpu` | 6c190f0 | MIT |
| QwenLM/Qwen-MM-Plugins `blender` | ce46a1e | Apache-2.0 (verified 2026-10-16) |
| RobLe3/cc-blender-skill `blender-export` | a2634b5 | MIT |
| RobLe3/cc-blender-skill `blender-pro-workflow` | a2634b5 | MIT |
| RobLe3/cc-blender-skill `text-to-blender` | a2634b5 | MIT |
| ahujasid/mcp-for-blender `README` | 7a0373e | MIT |
| arjun988/blender-skills `asset-optimization` | 8f778d2 | MIT (verified 2026-10-16) |
| arjun988/blender-skills `blender-director` | 8f778d2 | MIT (verified 2026-10-16) |
| arjun988/blender-skills `blender-modeler` | 8f778d2 | MIT (verified 2026-10-16) |
| czlonkowski/blender-web-3d-skill `blender-web-3d` | 858762f | MIT (verified) |
| dgreenheck/webgpu-claude-skill `webgpu-threejs-tsl` | af2319b | none |
| earthtojake/text-to-cad `cad` | 2457312 | MIT |
| elithril/blender-kiln | 4b170be | MIT (verified) |
| freshtechbro/claudedesignskills `blender-web-pipeline` | 1da73fe | MIT (verified 2026-10-16, stale 2025-11) |
| freshtechbro/claudedesignskills `lightweight-3d-effects` | 1da73fe | MIT (verified 2026-10-16, stale 2025-11) |
| freshtechbro/claudedesignskills `react-three-fiber` | 1da73fe | MIT (verified 2026-10-16, stale 2025-11) |
| freshtechbro/claudedesignskills `spline-interactive` | 1da73fe | MIT (verified 2026-10-16, stale 2025-11) |
| freshtechbro/claudedesignskills `threejs-webgl` | 1da73fe | MIT (verified 2026-10-16, stale 2025-11) |
| freshtechbro/claudedesignskills `web3d-integration-patterns` | 1da73fe | MIT (verified 2026-10-16, stale 2025-11) |
| jangtrinh/design-os-3d-blender `blender-image-to-3d` | 8909ac7 | MIT repo; vendored skill Apache-2.0 |
| jangtrinh/design-os-3d-blender `img2threejs` | 8909ac7 | MIT repo; vendored skill Apache-2.0 |
| linegel/threejs-complete-set-of-skill `threejs-choose-skills` | e3c9563 | ISC |
| majidmanzarpour/threejs-game-skills | 8286774 | MIT |
| math-inc/OpenGauss `blender-mcp` | f876339 | MIT (verified 2026-10-16) |
| millionco/react-doctor `improve-threejs` | 84ad0c8 | NOASSERTION |
| openai/plugins `react-three-fiber-game` | 0722921 | none |
| scenario-labs/skills `scenario-3d` | 49dd26e | MIT |
| scottstts/Threejs-Awesome-Graphics-Agent-Skills `threejs-awesome-graphics` | 897aaa0 | MIT |
| sickn33/agentic-awesome-skills `3d-ui` | c564f9f | MIT (verified 2026-10-16) |
| sickn33/agentic-awesome-skills `3d-web-experience` | c564f9f | MIT (verified 2026-10-16) |
| sickn33/agentic-awesome-skills `premium-3d-website` | c564f9f | MIT (verified 2026-10-16) |
| skinnye/3d-web-pack | cabd221 | MIT |
| thrixel/build-world | 39e09a7 | Apache-2.0 (verified 2026-10-16) |
| vercel-labs/json-render `react-three-fiber` | 72568f9 | Apache-2.0 (verified 2026-10-16) |
| vladmdgolam/agent-skills `blender-mcp` | b66d157 | MIT |
| vladmdgolam/agent-skills `threejs-perf-loading` | b66d157 | MIT |
| zebbern/claude-code-guide `r3f-best-practices` | cab276d | MIT |

### Scroll, art direction, Spline, splats, XR, CAD (gap scan)

| Source | Commit | Licence |
|---|---|---|
| AirsupHQ/machine-skill | e0bd066 | MIT |
| AvnehSBhatia/UltraUI `scroll-3d-camera-path-journey` | 592ae7f | MIT |
| RobLe3/cc-blender-skill `lighting-cameras` | a2634b5 | MIT |
| agiwhitelist/auteur | 9bca227 | MIT |
| ahmettasdemirusa/threejs-product-skills `model-viewer-ar` | a8150ad | MIT |
| aydinfer/spline-mcp-server `spline-mcp` | 047659e | MIT |
| ckorhonen/claude-skills `gsplat-optimizer` | 947001b | MIT |
| earthtojake/text-to-cad `cad` | 2457312 | MIT |
| flowful-ai/cad-skill `parametric-3d-printing` | fe42159 | NOASSERTION |
| heyixuan2/bambu-studio-ai | cdc2698 | MIT |
| instruktlabs/kiln | 743965a | MIT |
| jaccen/Awesome-Gaussian-Skills `agent-router` | a0f2bcc | Apache-2.0 |
| majidmanzarpour/threejs-game-skills `threejs-3d-generator` | 8286774 | MIT |
| mdbritt/claudecad `cad` | c568946 | Apache-2.0 |
| meshy-dev/meshy-3d-agent `meshy-3d-generation` | 92ffd74 | MIT |
| meta-quest/agentic-tools `hz-iwsdk-webxr` | 3a8553d | Apache-2.0 |
| mitsuhiko/agent-stuff `openscad` | 0865c84 | Apache-2.0 |
| noklip-io/agent-skills `theatre-js` | 319a0f1 | MIT |
| oakoss/agent-skills `threejs` | 85e3a39 | none |
| oakoss/agent-skills `threejs-r3f-patterns` | 85e3a39 | none |
| santiagomoneta/3d-printing-skills `orca-slicer` | 99fea76 | none |
| shi3z/sparkjs-skill `sparkjs` | 6b0179c | none |
| sparkjsdev/spark `docs` | 4e0b58c | MIT |
| splinetool/docs `spline-mcp-and-skill` | n/a | vendor docs |

## Own work

The `refspec.v1` and `shots.v1` schemas, the loop and its fresh-critic gate, the pixel-parity gate, the claim-scoped verdict scorecard, the preview tool and viewer, `scripts/capabilities`, `glb-report` and `ref-extract`, the `SceneCanvas`, conductor and adapter blocks, and the budget and decision defaults are this repository's own synthesis (2026-10-16), grounded in primary documentation (three.js, glTF-Transform, meshoptimizer, KTX-Software, Blender manual and API notes) as recorded in the ground-truth files.

Maintainers: add a row here and in `skills/3d/references/SOURCES.md` whenever a reference draws on a new outside source.
