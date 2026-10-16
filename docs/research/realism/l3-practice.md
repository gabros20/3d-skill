# L3 - Practitioner practice: real-time vs baked vs pre-rendered, and when to stop

Fetched 2026-10-16. Grades: [V] official/source, [B] measured, [P] practitioner, [U] unverified.
Method: WebSearch + WebFetch (fetch results are small-model summaries, not full text), xrelay (read-only), ghrelay.
Saved sources: `docs/research/community-scan/sources/realism/<name>/SOURCE.txt` (the leftover `_q/` there holds raw xrelay/ghrelay corpora).

## 0. Coverage and gaps (read first)

- **Found with primary sources:** Lusion (own Awwwards write-up), Bruno Simon's Three.js Journey baking lesson, Needle Engine lightmapping docs, three.js forum AgX/baking threads, Khronos PBR Neutral, pmndrs/postprocessing AgX CDL PR, one open-source baked-scene repo.
- **NOT found (do not cite the skill as if it knew them):** Active Theory (only a third-party decompile post, unread), Igloo Inc (only an Awwwards credit page, no build detail), 14islands, Resn, Dogstudio, Unseen. Searches returned no technical case studies. Treat claims about their pipelines as [U].
- **X (xrelay) was low-yield:** broad queries returned hype posts; no thread was worth a full read. Nothing from X is cited as evidence below.
- **No practitioner source states a numeric "realism budget" or a plateau test for visual iteration.** Those rows are marked as gaps, not inferred.

## 1. Techniques in use and who states them

| Technique | Who / source | What it buys | Stated cost / limit |
|---|---|---|---|
| Cycles bake to textures (Blender), unlit/basic material | Bruno Simon, Three.js Journey [P] https://www.threejs-journey.com/lessons/creating-a-scene-in-blender | Ray-traced-quality lighting at near-zero runtime cost | "no light, no real-time shadows"; lights cannot move; any change means re-bake; many textures slow load; mixing baked and non-baked is hard to keep consistent |
| Bake to texture + sRGB Filmic compositor step | drcmda (pmndrs) on forum [P] https://discourse.threejs.org/t/how-to-bake-light-with-textures/52076 | Filmic result matches Blender view; he says this step "made the biggest difference" | glTF has no native 2nd-UV lightmap support "without hacks"; atlas UV choice is hard to change afterwards |
| Lightmap on 2nd UV set, static geometry only | Needle Engine docs [V] https://engine.needle.tools/docs/blender/lightmapping | Static GI + dynamic point lights for moving things | "Lightmap static architecture, not characters"; 128-512 samples for production, 1024-4096 map res; plugin "experimental" |
| Baked diffuse + live specular (MeshBakedMaterial) | mesh-baked-material README [P] https://unpkg.com/mesh-baked-material@1.0.4/README.md | Fixes the two bad options: MeshBasic = flat, no spec; MeshStandard + lights = baked shading applied twice | Specular still depends on scene lights; roughness/metalness need hand-tuning |
| Cloud-GPU Cycles bake, OIDN denoise, RGBM WebP lightmaps, precomputed reflection probes, one bake per state | sesasa/3d-house-walkthrough [P] https://github.com/sesasa/3d-house-walkthrough | Baked-quality interiors on a static site | State changes (door open/closed) need separate bakes; self-described "architectural approximation" |
| Pre-render layers, recombine with matcaps | Lusion [P] https://awwwards.com/case-study-for-lusion-by-lusion-winner-of-site-of-the-month-may.html | Translucent hero object with 2 switchable states at tiny cost (normal, AO, thickness, 2 diffuse-illumination sets prerendered) | Fixed lighting set; look is limited to what was pre-computed |
| Offline render (Redshift3D) to video + exported camera JSON + ~150 KB GLTF with live cursor light | Lusion, same source [P] | Offline-grade image with a thin real-time layer (light, small look-around ~1.7 deg) on top | Video/frame sync is fragile: `video.currentTime` unreliable on some browsers; they encoded a frame counter in the video and read it with `readPixels()` ("the only universal solution we could think of") |
| Houdini cloth sim baked to vertex-animation PNGs, blended by user input | Lusion, same source [P] | Sim-quality motion at 983 KB desktop / 246 KB mobile | "the results do not look as perfect as a proper cloth simulation"; they add real-time distortion to hide it |
| Pre-rendered image sequence on canvas (500 WebP from Blender) | Webflow showcase [U] https://webflow.com/made-in-webflow/website/image-sequence-on-scroll | Guaranteed look, trivial runtime | One skill doc (tessl) lists downsides: heavy assets, fixed path/resolution pixelates on Retina/4K, any colour/lighting/timing change = re-render all [U] |

Pattern across the sources: every case that looks "rendered" decides **per element** what is frozen (lighting, sims, hero object, background plate) and keeps only a thin live layer (cursor light, camera nudge, state blend). Nobody in the sources claims full path-traced realism from live lighting.

## 2. Blender to three.js look-matching: why exports look flat

Ordered by how often the sources blame them.

1. **View transform mismatch.** Blender 4+/5 defaults to AgX; three.js AgX is not identical: "not 100% identical to Blender's", simple clamp gamut mapping, and no Blender "Looks" (donmccurdy, three.js maintainer) [V/P] https://discourse.threejs.org/t/is-agx-tonemapping-implemented-correctly/60609. AgX Base is "less saturated than ACES Filmic by design" and is intended as a grading base, not a finished look. AgX's author (troy_s) notes contrast is easy to raise, impossible to lower.
2. **Fix = add the missing grade.** three.js ships `AgXPunchyToneMapping` (PR #27618, "more contrasty and saturated"); pmndrs/postprocessing PR #723 adds an AgX CDL step with Punchy and a Needle Engine preset [V] https://github.com/pmndrs/postprocessing/pull/723. Version matters: first AgX (r160) lacked a gamut-mapping fix landed in r161 - judge on current (r186).
3. **Filmic family desaturates by design.** Khronos: ACES "push colors toward white the brighter they are"; saturated yellows/greens/blues "impossible to output"; AgX "shares this problem" [V] https://modelviewer.dev/examples/tone-mapping. Their PBR Neutral exists for colour fidelity (product/e-commerce), explicitly "not a competitor to AgX" (Blender PR #118936 body, fetched via API). Use rule from the sources: Neutral when base colours must read true; filmic/AgX when HDR highlight roll-off matters.
4. **Baking path colour step.** Bake in Cycles with the same view transform you intend to match; drcmda says the compositor sRGB-Filmic step was the biggest single improvement [P]. Texture colour space set explicitly (`SRGBColorSpace` for colour maps, `flipY=false` for glTF-style UVs) - the forum code in the thread shows these settings; the thread itself does not explain them.
5. **Lighting confound.** Blender's default world is not grey; exact hue matching needs a neutral studio light in both (Blender PR discussion, via search summary [U]).
6. **Material double-lighting** (section 1, MeshBakedMaterial).

Not found: a measured side-by-side "Blender Cycles vs three.js" error figure from any practitioner. [gap]

## 3. Real-time vs baked vs pre-rendered: decision rules practitioners actually state

| Rule (verbatim or close) | Source |
|---|---|
| "You don't need to do everything real-time." | Lusion [P] |
| Bake because "real-time WebGL can't match offline ray tracing" and must hold frame rate; you get ray-traced lighting at low runtime cost | Bruno Simon [P] |
| Bake what is static; do not lightmap anything that moves; add dynamic lights only for moving elements | Needle [V] |
| Accept a visibly lower-fidelity precompute when you can add a cheap live layer to sell it | Lusion cloth [P] |
| Prefer a live WebGL scene only if depth, lighting or a real 3D camera "materially strengthen the idea" | tessl skill doc [U] https://tessl.io/registry/skills/github/MengTo/Skills/build-threejs-scroll-worlds |
| Prefer pre-rendered frames when you need a guaranteed look, but expect large asset weight, fixed camera/resolution and full re-render on any change | tessl scroll-scrubbed doc [U] |

Synthesised decision order (this is my synthesis of the above, not a quoted rule):
1. Camera fixed or on rails + lighting fixed + hero is the whole show: pre-rendered video/sequence, plus a live layer only if cheap.
2. Camera free but scene static: baked textures (+ baked reflection probes), live specular only.
3. Moving/dynamic objects: live PBR + environment, accept the lower ceiling, keep them small in frame or hide the gap (see section 4).
4. Anything needing path-traced effects (caustics, true interreflection, sub-surface, many-bounce metal): bake or pre-render; no source shows live equivalents.

## 4. The "uncanny gap" and realism budgets

- **Authoritative statement of the gap:** Bruno Simon: offline renders look better than imported three.js models; WebGL uses "cheaper techniques that don't look as good but at least keep a decent frame rate" [P].
- **Practitioner mitigation, not elimination:** studios keep the real-time part small, lit by an identical baked environment, and layered over a pre-rendered plate (Lusion's big-screen scene). Gap is hidden by composition, not closed.
- **Rule-of-thumb numbers found:** Needle bake samples 128-512, lightmap 1024-4096 [V]; Lusion cloth payloads under 1 MB [P]. No source gives a frame-time or triangle "realism budget" for photoreal; I did not invent one. [gap]
- **Not found:** talks titled around "uncanny" offline-vs-WebGL. Searches returned generic baking tutorials and forward/deferred shading articles.

## 5. Stop and acceptance criteria for visual iteration

What evidence exists (thin):

| Finding | Source | Grade |
|---|---|---|
| Critic-actor loops degrade or converge "after multiple iterations (often three)"; no formal stop rule; actor "does not always incorporate the critic's feedback" | arXiv 2601.05016 sec 5.3 https://arxiv.org/html/2601.05016v1 | [P] (single paper, 3D modelling) |
| Stop condition "must be external to the agent's opinion"; an LLM judging completion is the weakest gate; subjective gates need an attempt cap, a human, and a separate adversarial grader | mejba.me loop engineering https://www.mejba.me/blog/loop-engineering-agent-loops-explained | [U] blog |
| Plateau detection is not covered by that article | same | - |
| Other agent-3D papers use fixed caps (e.g. up to 10 turns for a camera agent; 2 self-critique iterations in a code benchmark) | search summary of arXiv 2604.25318 and 2606.01057, not fetched | [U] |
| Weaker vision critics over-accept or over-revise; the strongest backbone was the most conservative critic | search summary of 2606.01057, not fetched | [U] |
| A builder-critic loop let a visual bug through because the rubric had no criterion for it; fix was adding the criterion | search summary of a levelup.gitconnected article (paywalled, fetch 403) | [U] |

Studio acceptance practice (art-director sign-off on a real-time approximation): **not found in any fetched source.** The only observable behaviour is Lusion's explicit admission of lower fidelity plus a mitigation layer, and sesasa's labelling of the result as an "approximation" and use of automated checks (Playwright) for non-visual correctness.

Candidate gates for the skill (my recommendation, grounded in the above, to be calibrated):
1. **Set the ceiling before iterating:** classify each element with the section 3 order; state which gaps are structural (real-time cannot do) vs fixable (tone mapping, colour space, double-lit materials, missing grade). Section 2 items are the "fixable" list - each has a known fix.
2. **External gate, not VLM opinion:** define pass as named defects resolved plus a measurable comparison to the reference (the loop-engineering rule). Vision-critic verdict is advisory.
3. **Attempt cap + plateau rule:** cap loops (sources use 2-10; the one measured claim is ~3 before degradation); stop when two consecutive iterations leave the named-defect list unchanged, and keep best-so-far (rollback) rather than the last.
4. **Escalate, do not cut corners:** on cap or plateau, present best result + the list of structural gaps + the options (bake/pre-render for that element, change the camera/composition, accept) and ask for a direction.

## 6. Dissent and caveats

- Baking vs live: Bruno Simon teaches baking as the way to hit quality; MeshBakedMaterial's README shows baking is not free of artefacts (flat or over-contrasty results) [P].
- Pre-rendered sequences: favoured for guaranteed looks, but one skill doc argues against them for weight, pixelation and inflexibility; that doc is an opinion, not a measurement [U].
- AgX vs Neutral: Khronos frames filmic curves as a colour-fidelity problem for products; Blender developers still recommend AgX for general realism (via search summary of the Blender devtalk thread, not fetched) [U].
- Lightmaps via glTF: drcmda prefers baking into textures over LM-bake because Filmic is not supported there and glTF lacks 2nd-UV lightmaps; Needle supports lightmaps through its own plugin. Choice depends on the toolchain.
- All "fetched" claims here come from summarising fetches; quotes were not checked against full page text.
