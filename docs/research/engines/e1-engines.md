# E1 — Web 3D engine choice in 2026

Research date: 2026-10-16. Grades: [V] official/source, [B] measured by me, [P] practitioner/secondary, [U] unverified.
Versions (npm view, 2026-10-16): three 0.186.1 (r186, 2026-09-24), @react-three/fiber 9.8.2, drei 10.7.9, @react-three/postprocessing 3.2.0, @react-three/rapier 2.2.0, @react-three/xr 6.6.32, @babylonjs/core 9.31.0, @babylonjs/havok 1.3.14, react-babylonjs 4.0.2, playcanvas 2.23.3, @needle-tools/engine 6.0.0-alpha.7 (support repo release 5.1.16), @google/model-viewer 4.4.0, @splinetool/runtime 2.0.92. [B]

## 1. The 2022 article, claim by claim

Source: https://www.spotvirtual.com/blog/why-we-use-babylonjs-instead-of-threejs-in-2022 (fetched 2026-10-16; claims paraphrased from the fetch summary, quotes short).

| # | 2022 claim | 2026 verdict | Evidence |
|---|---|---|---|
| 1 | TypeScript codebase is friendlier than plain JS | **Mostly obsolete.** three ships first-party types in-package since r16x era (`@types/three` no longer required) and R3F 9/10 are typed end to end. Babylon is still TS-native with the better API-doc-from-source story, but the gap is small. | R3F v10 alpha.5 notes are a types release [V] https://github.com/pmndrs/react-three-fiber/releases ; [U] three types-in-package date not re-checked |
| 2 | Selective shadows/lights via ShadowGenerator | **Still true, narrower.** Babylon lights/shadow casters are explicit per object. three has per-light `castShadow` plus per-mesh `castShadow/receiveShadow`, so scene-level selectivity exists; Babylon's `includedOnlyMeshes` on lights is finer. | [P] |
| 3 | More game-engine features in core (team lacks 3D background) | **Still true and widened.** Babylon core: Inspector, GUI, Havok physics, Frame Graph v1, clustered lighting, node editors, Gaussian splatting with shadows (v9). three is a renderer + addons; you assemble physics/post/UI. | v9 coverage https://www.windowsmode.com/babylon-js-9-0-released-build-immersive-3d-web-apps/ [P]; `@babylonjs/inspector` 9.31.0, `@babylonjs/gui` 9.31.0 on npm [B] |
| 4 | Babylon "a little further along" on WebGPU | **Reversed to parity.** Babylon: WebGPU since 5.0, WGSL core shaders since 2024, WebGL/WebGPU "side by side for the foreseeable future"; WebGPU-XR experimental. three: `WebGPURenderer` + TSL are the active focus (migration guide: ~109 breaking bullets r170→r187, dominated by WebGPU/TSL), automatic WebGL2 fallback; r185 reworked premultiplied alpha, r186 dropped `PCFSoftShadowMap` in WebGPURenderer. three's examples tree now has a full TSL post suite (SSR, SSGI, GTAO, TRAA, DoF, Bloom, Godrays, OIT, motion blur). | https://doc.babylonjs.com/setup/support/webGPU [V]; https://github.com/mrdoob/three.js/wiki/Migration-Guide [V]; `examples/jsm/tsl/display` in three@0.186.1 [B] |
| 5 | Snapshot rendering cuts CPU | **Still a Babylon-only differentiator** (render bundles / snapshot mode). Not re-benchmarked; matters for many-static-mesh scenes, not heroes. | [U] |
| 6 | Inspector debugs in the live app | **Still true, and the decisive tooling gap.** Babylon Inspector (scene tree, materials, shader/NME, perf, GLB export) is first-party. three has no equivalent first-party tool: three.js editor (separate app), Tweakpane/Leva/lil-gui, r3f-perf, browser "three.js Developer Tools" extension [P]. | |
| 7 | Blender addon fits asset workflow | **Still true**: Babylon Blender exporter exists, but with glTF being universal, both engines consume the same GLB; the exporter matters mainly for Babylon-specific metadata. | [P] |
| 8 | Fast fixes from core team, nightly builds | **Still true.** 9.x ships roughly weekly (9.22.1 → 9.30.0 between 2026-08-20 and 2026-10-08); only 15 open GitHub issues on Babylon.js vs 390 on three.js. Caveat: a low issue count reflects a triage policy (forum-first), not fewer bugs. | gh api releases/issues [B] |
| 9 | Playground indispensable | **Still true.** Babylon Playground vs three has jsfiddle/CodeSandbox/R3F sandboxes and Claude-style generation; the Playground (with versioned snapshots) remains the best shareable repro tool. | [P] |
| - | "Docs a bit clunky" | Unchanged-ish; both sets are large. three's docs lean on ~400 examples; Babylon's on docs + Playground. | [P] |
| - | "react-babylonjs has less traction than R3F" | **Much stronger now**: 3,232 vs 6,241,878 weekly downloads (see §4). | npm api, week 2026-10-06..12 [B] |
| - | WebXR: both fine | Still true. R3F has `@react-three/xr` 6.6.32 (actively released 2026-10-13). Babylon has the more complete built-in WebXR helpers (teleportation, hand tracking, features manager). | [B]/[P] |

**Not in 2022 and now matters:** (a) gaussian splats — Babylon 9 added shadow casting, SOG/SOGS and multiple-splat sorting; three has community loaders and `KHR_gaussian_splatting` appears in both glTF loaders [B, loader source]; (b) glTF material extension breadth (§2); (c) AI-assisted authoring — three/R3F code has by far the larger training corpus [P].

### Updated bottom line on the article
The 2022 case was "Babylon = batteries included, three = flexible renderer". In 2026 that framing still holds on tooling and core features, but its three counterweights have grown: WebGPU/TSL parity, R3F+drei ecosystem, and a 50x npm gap (21.4M vs 0.40M weekly).

## 2. Comparison matrix

Downloads = npm last-week, 2026-10-06..12. Stars/issues = GitHub 2026-10-16. [B]

| Axis | three.js | Babylon.js | PlayCanvas | Needle Engine | Spline | Verge3D | model-viewer |
|---|---|---|---|---|---|---|---|
| Nature | renderer + addons | full engine | engine (MIT) + cloud editor | three.js-based component runtime + Unity/Blender editor integrations | no-code 3D design tool + runtime | Blender/Max/Maya → web toolkit on three.js | web component for viewing GLB |
| Version / cadence | r186; releases 2026-02-20, 04-16, 07-01, 09-24 (~every 2-3 months) | 9.31.0; near-weekly minors; majors yearly (8.0 2025-03-27, 9.0 2026-03-26) | 2.23.3; releases several per week | 6.0.0-alpha.7 / 5.1.16 | 2.0.92, near-daily | slow, paid-license cadence [U] | 4.4.0, ~monthly |
| npm weekly | 21,426,650 | 403,145 | 133,434 | 6,133 | 626,107 | n/a (not on npm) | 558,454 |
| GitHub | 116.5k stars, 390 open issues | 26.2k, 15 | 17.1k, 462 | support repo 609 stars | closed source | closed | 8.3k, 118 |
| License | MIT | Apache-2.0 | MIT (editor cloud, paid tiers [U]) | MIT engine [P]; pricing for commercial use not verified [U] | proprietary; watermark on free exports; paid plans (sources conflict: $12-20 vs $15-25 /seat/mo) [P] | paid: Freelance $290, Team $990, Enterprise $2,990 (soft8soft.com/licensing via search) [P] | Apache-2.0 |
| PBR + IBL defaults | `MeshStandardMaterial`/`MeshPhysicalMaterial`, PMREM, `RoomEnvironment`; you pick tone mapping (ACES/AgX/Neutral) | PBRMaterial + default environment helper, image-processing config built in | PBR StandardMaterial, IBL, clustered lights | inherits three | simplified PBR, built-in lighting | PBR from Blender Principled | Neutral/ACES tone mapping preset, IBL, shadow, good "just works" |
| Post (SSAO/SSR/bloom/TAA) | WebGL: `pmndrs/postprocessing` (SSAO, bloom, SMAA, DoF…). WebGPU: TSL nodes SSR, SSGI, GTAO, TRAA/TAAU, Bloom, DoF, Godrays, OIT in core examples [B] | `DefaultRenderingPipeline` (bloom, FXAA/MSAA, DoF, grain, TAA via `TAARenderingPipeline`), SSAO2, SSR2, motion blur, Frame Graph v1 [V-ish/P] | post effects (bloom, TAA, SSAO, DoF) in engine | three's | bloom/DoF/noise etc., limited | three's | none (exposure/shadow only) |
| Shadows | PCF/VSM; contact shadow helpers via drei | CSM, ShadowGenerator (PCF, PCSS, blur ESM) | PCF/VSM, cascades | three's | basic | three's | soft shadow plane |
| glTF KHR_materials (loader source inspected, @babylonjs/loaders 9.31.0 and three 0.186.1 GLTFLoader) | clearcoat, sheen, transmission, volume, ior, iridescence, anisotropy, specular, dispersion, emissive_strength, unlit, variants, bump (EXT) [B]. Core loader lacks `diffuse_transmission`, `coat`, `fuzz`, `volume_scatter`, `diffuse_roughness` found in Babylon [B] | superset: all of the above + `coat`, `fuzz`, `diffuse_transmission`, `volume_scatter`, `diffuse_roughness`, `pbrSpecularGlossiness`, `EXT_lights_area/ies`, `KHR_interactivity`, `node_visibility`, `MSFT_lod` [B] | broad; sheen/clearcoat/transmission/iridescence [U per-extension] | three's | own format | three's | three's (Draco/Meshopt/KTX2 supported) |
| WebGPU | WebGPURenderer + TSL, WebGL2 fallback, still churning | production, WGSL core, side-by-side with WebGL | supported (WebGPU device in 2.x) [U details] | not three's WebGPU path by default [U] | no | no | no |
| Editor / inspector | none first-party for live debug; community tools | Inspector, Node Material Editor, Node Geometry/Particle Editors, Playground, Sandbox, Sandbox GLB viewer | cloud editor (strong, collaborative); engine usable headless/code-only | Unity/Blender component workflow, hot reload | the product | Blender add-on | n/a |
| Physics | Rapier (via R3F rapier 2.2.0), cannon-es, Jolt, Ammo; BYO | Havok (@babylonjs/havok 1.3.14) first-party, plus Cannon/Oimo/ammo plugins | ammo/Rapier-style built-in | Rapier built-in [V needle docs] | basic | via three | none |
| XR | WebXR native + @react-three/xr 6.6.32 | most complete built-in (feature manager, teleport, hands); WebGPU-XR experimental | WebXR built-in | WebXR/AR, iOS AR via Quick Look | limited | yes | AR quick-look/Scene Viewer |
| Min bundle (gzip, esbuild, minify, tree-shake; scratch ./bs) [B] | box + MeshStandardMaterial + light + WebGLRenderer: **134 KB**; + GLTFLoader: **157 KB** | box + PBRMaterial + hemi light + ArcRotateCamera + Engine: **481 KB**; + glTF loader: **868 KB** | box + Application: **532 KB** | three + runtime (>>157 KB) [U] | `@splinetool/runtime` ~500 KB+ [P] | three + runtime [U] | ~lazy-loaded; `three` peer 0.183 (3D elements pull three) [B] |
| Tree-shaking | good for core; addons per-file | `@babylonjs/core/...` deep imports work but side-effect imports (e.g. shaders, `Ray` extensions) frequently needed; plain `import {X} from '@babylonjs/core'` bloats | module-based, but app bootstrap is heavy | n/a | n/a | n/a | n/a |
| Learning curve | low entry, wide ceiling; low-level knowledge helps | steeper surface area, more guidance in-box | easy in editor | easy for Unity users | easiest | easy in Blender | trivial |
| Breaking changes/yr | high at the edges: ~6 breaking bullets per release, 4-5 releases/yr (r170→r187 ≈ 109 bullets); ~19 in r184→r185 | low by policy: "we cherish backward compatibility"; two-major-cadence of yearly releases, a stated plan for rare "Babylon 10"-style breaks; small export moves still happen | moderate (2.x stable but frequent) | high (alpha 6.0) | vendor-controlled | tied to Blender versions | low |

Notes on matrix:
- Bundle numbers are one minimal scene each, not full apps; Babylon's cost scales less with features than it appears (PBR, default shaders, engine core are the floor), but its floor is 3.5x three's [B].
- Nominal-number caveats: esbuild `--minify --tree-shaking`, no custom splitting; real Next.js bundling differs by a few %.
- Needle claims: Unity 6 LTS / Blender 4.5 LTS & 5.0.1 listed, Rapier built-in, hot reload [V] https://engine.needle.tools/docs/getting-started . The page does not state the renderer; three.js based per the package/repo [P].

## 3. React bindings verdict

| | React Three Fiber | react-babylonjs |
|---|---|---|
| Version | 9.8.2 (2026-10-15), v10.0.0-alpha.5 (2026-09-08) with WebGPU/TSL hooks (`useUniforms`, `useNodes`, `useGPUStorage`) | 4.0.2 (2026-06-02); 4.x requires React 19, 3.x line (`r18` branch) for React 18 |
| Weekly downloads | 6,241,878 | 3,232 (≈1,900x fewer) |
| GitHub | 33.0k stars, 13 open issues | 892 stars, 9 open issues (all from 2022-2025; newest 2025-01-21 unresolved) |
| Maintainers | pmndrs collective; releases every 1-3 weeks | one maintainer (brianzinn 484 commits; next contributor 118); sparse bursts (2025-05 → 2026-05-26 gap of 12 months, then 4.0.0 and fixes) |
| Ecosystem | drei 10.7.9, postprocessing 3.2.0, rapier 2.2.0, xr 6.6.32, leva, zustand, theatre, lamina, maath… | Declarative wrappers generated from Babylon API (code-gen), GUI, physics props; "~50 samples" |
| React 19 | peer `react >=19 <19.4` (9.x) | peer `react >=19` |
| Next App Router | Well-trodden: `'use client'` Canvas, `dynamic(..., {ssr:false})`, `@react-three/offscreen` experimental | Possible; same constraints, almost no public writeups [U] |

**Verdict.** react-babylonjs is **alive but marginal**: usable for a team that already owns Babylon and wants a declarative scene graph, but it should not be the default and it is a **single-maintainer risk**. For Babylon in a Next.js App Router site, prefer **plain Babylon in a `'use client'` component**: create `Engine`/`Scene` in `useEffect`, `dispose()` in cleanup, load via dynamic import, import from `@babylonjs/core/...` deep paths, and keep render loop outside React state (Spot Virtual's article needed to build on-demand rendering by hand). R3F is the only React 3D binding with a real ecosystem; if the user wants React-declarative 3D, pick three+R3F.

## 4. Decision rules (creative-experience sites)

Defaults first. Unless a rule below fires, **choose three.js + R3F + drei**: smallest bundle, biggest corpus (human + LLM), best Next integration, and the 3d skill's helpers/post-chains assume it.

| Situation | Pick | Why / evidence |
|---|---|---|
| Marketing hero, one product, scroll story, GSAP/Motion-driven | **three + R3F (+drei)**, plain three if no React | 134-157 KB gzip floor vs 481-868 KB [B]; scroll/DOM sync libs are written around R3F |
| Product configurator (materials, variants) | **three** (`KHR_materials_variants`) or **model-viewer** if it is "rotate + swap + AR" only | model-viewer: 558k/wk, AR built in; three if brand look needed |
| Single GLB showcase / AR quick-look, no custom scene | **model-viewer** | zero-engine, Apache-2.0, 4.4.0; cap on look control |
| Realism-heavy Blender scene with transmission/clearcoat/sheen | **Either**; test GLB in both viewers first. Babylon loader supports more KHR extensions (`coat`, `fuzz`, `diffuse_transmission`, `volume_scatter`) so for exotic Blender 5 materials Babylon renders closer out of the box [B]; for baked/lit scenes the difference vanishes | check extension list in §2 before choosing |
| Heavy scene: many lights, big world, game-ish, physics, UI in 3D | **Babylon** | clustered lighting (v9), Havok first-party, GUI, Frame Graph, snapshot rendering, Inspector |
| Team with game-engine/C# background, no WebGL knowledge, wants tools and stable API | **Babylon** (or PlayCanvas editor) | back-compat policy, Inspector/NME, one dependency |
| Team is React/TS web devs, designers drive the look with shaders and post | **three + R3F** | TSL/GLSL + `postprocessing` + drei |
| Non-developer designer owns the scene, few revisions | **Spline** (accept ~500 KB runtime, watermark/plan cost, perf risk) | no engineering; watch embed count (Spline recommends ≤1-2) |
| Unity or Blender artist authors interactions, devs integrate | **Needle Engine** (still alpha 6.0 [B]) | component workflow, hot reload; stability risk |
| Blender artist wants no code at all and licensing is acceptable | **Verge3D** ($290-2,990 [P]) | Blender puzzles; three.js underneath; vendor lock |
| WebXR-first product | **Babylon** for built-in features; **three + @react-three/xr** if you are already in R3F | WebGPU-XR is experimental in Babylon |
| WebGPU/compute/splat showpiece and willing to track churn | **three WebGPURenderer + TSL**, or **Babylon 9** if you prefer stability | three migration guide shows ~6 breaking bullets/release [V] |
| Long-lived product, few devs, upgrade pain matters | **Babylon** | stated compat policy; pin three and budget upgrades otherwise |

### Skill/team factors
- LLM-authored code quality is highest for three/R3F (bigger public corpus) [P]; for Babylon, give the agent the exact import-path rules (deep imports + side-effect imports) to avoid 3-4x bundles.
- Hiring: R3F devs far outnumber Babylon devs (npm ratio 15x for core, 1,900x for bindings).
- Blender pipeline is engine-agnostic via glTF (Draco/Meshopt/KTX2 all supported in both loaders [B]); bake lighting for either; per-engine Blender add-ons (Babylon exporter, Verge3D, Needle) buy tooling, not quality.
- Pairing rule for the `3d` skill: keep three/R3F primary; add a Babylon section only as "when to switch" with plain-component integration, not react-babylonjs.

## 5. Open items [U]
- PlayCanvas WebGPU maturity and per-extension glTF support not verified (official page fetch returned no detail).
- Needle licensing/pricing and renderer claim not confirmed on the docs page.
- Verge3D pricing came from search snippets of soft8soft.com/licensing; direct fetch failed (SSL handshake).
- Spline pricing sources conflict; no official limits found.
- Babylon post-processing list is from knowledge of the API plus the installed package's SSAO2/SSR config files [B]; no benchmark of quality vs three TSL.
- No FPS benchmark was run; all performance statements are structural.

## Sources
- https://www.spotvirtual.com/blog/why-we-use-babylonjs-instead-of-threejs-in-2022
- https://doc.babylonjs.com/setup/support/webGPU
- https://github.com/mrdoob/three.js/wiki/Migration-Guide
- https://engine.needle.tools/docs/getting-started
- https://forum.babylonjs.com/t/babylon-10-poll/49361 , https://babylonjs.medium.com/babylon-10-0675f7de54a4 (via search)
- https://www.windowsmode.com/babylon-js-9-0-released-build-immersive-3d-web-apps/ (Babylon 9 coverage, secondary)
- https://github.com/brianzinn/react-babylonjs (README, issues, commits via gh api)
- https://github.com/pmndrs/react-three-fiber/releases
- https://www.soft8soft.com/licensing/ (via search), https://costbench.com/software/ai-3d-generation/spline/ (via search)
- npm registry + api.npmjs.org downloads, GitHub API, esbuild measurements in scratchpad `bs/` (2026-10-16)
