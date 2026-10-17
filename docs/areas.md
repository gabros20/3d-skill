# Areas

The `3d` pack is one skill with 48 flat, area-prefixed references in
[`skills/3d/references/`](../skills/3d/references). The router
([`SKILL.md`](../skills/3d/SKILL.md)) links every one directly; nothing depends on directory
discovery, and a reference is read only when its condition matches. This page lists each area, what
each reference produces, and when it routes. The stages they serve are in [loop.md](loop.md).

Every reference opens with the same header: **Purpose**, **Read when**, **Skip when**, **Inputs**,
**Produces**, a contents line. `scripts/lint-skill` enforces it. Scripts named below run as
`<skill>/scripts/<x>` from your project root.

## Front door

Turns a request and references into an approved brief. Read in this order for a new piece.

| Reference | Routes when | Produces |
|---|---|---|
| [intake-grill](../skills/3d/references/intake-grill.md) | a new request has no approved `.3d/brief.md`; the prompt is vague | a restated brief with `[assumed]` tags and an Out of scope line, then `.3d/brief.md` after your yes |
| [intake-references](../skills/3d/references/intake-references.md) | an image, video, screenshot, site capture or "make it look like this" | `.3d/refs/<name>/` and `.3d/reference-spec.json` |
| [refspec](../skills/3d/references/refspec.md) | writing or validating `.3d/reference-spec.json`; a refspec becomes a generation prompt | a valid `refspec.v1` file |
| [refspec-mapping](../skills/3d/references/refspec-mapping.md) | a refspec or brief must become camera, lights, tone, materials, post; a render does not match | starting parameters and the one to move first |
| [brief-spec](../skills/3d/references/brief-spec.md) | writing the brief, storyboard, shot list, scroll map, camera path, sign-off gates | `.3d/brief.md`, `.3d/shots.json` |
| [brief-lexicon](../skills/3d/references/brief-lexicon.md) | a term like "dramatic" or "glossy" must become checkable | precise wording; no artifact |
| [brief-approach](../skills/3d/references/brief-approach.md) | choosing how to build it: real-time or pre-render, fallback ladder | the brief's Pipeline section, recorded in `3D.md` |

## Engine and realism

Settles the engine and says, before building, how close live three.js can get to a reference.

| Reference | Routes when | Produces |
|---|---|---|
| [engine-choice](../skills/3d/references/engine-choice.md) | approach is being chosen and the project hints at Babylon.js, PlayCanvas, Needle, model-viewer or Spline; `@babylonjs/*` in `package.json` | one engine decision line in `3D.md` (engine, reason, rejected alternatives) |
| [realism-gap](../skills/3d/references/realism-gap.md) | a reference is a Cycles or Redshift render, photo or AI image or video and the brief says "match"; a critic defect must be labelled FIXABLE, CEILING or ARTEFACT | per-feature tier (live, bake-only, offline-only, reference artefact), a per-category ceiling |
| [realism-toolbox](../skills/3d/references/realism-toolbox.md) | a FIXABLE defect names a technique; "make three.js look like the Blender render" | an ordered technique list with ids for `preview new-version --technique` |
| [realism-gate](../skills/3d/references/realism-gate.md) | the brief matches or styles a reference, or asks for realism; a critic round returns defects or scores stall; "keep going" | `.3d/feasibility.json`, per-round `rounds.v1` lines, a `preview rounds` verdict, a MAX REACHED report on stop |

The gate runs before the build and needs your yes on the stated ceiling and ship bar. After every
critic round `preview rounds` returns pass or stop (S1 nothing fixable, S2 plateau, S3 diminishing
returns, S4 budget) or continue, and "iterate until it passes" never overrides it.

## Shared

Used by every lane.

| Reference | Routes when | Produces |
|---|---|---|
| [shared-preflight](../skills/3d/references/shared-preflight.md) | no `3D.md`; a recorded decision would change; "command not found" | `.3d/capabilities.md`, a filled `3D.md`, one batched install question |
| [shared-debug](../skills/3d/references/shared-debug.md) | anything renders wrong, blank, slow, or unlike Blender or the reference | one confirmed cause and one change |
| [shared-performance](../skills/3d/references/shared-performance.md) | budgets; slow, hot, first-frame jank, memory growth | budget numbers in `3D.md`, a frame-loop and quality plan |
| [shared-preview](../skills/3d/references/shared-preview.md) | a version must be seen; notes came back | `.3d/versions/vNNN/`, `.3d/evidence/vNNN/`, read-back notes |
| [shared-verification](../skills/3d/references/shared-verification.md) | about to say "done", "matches" or "fast" | claim-scoped verdicts, a scorecard, a sign-off line |

## three.js, R3F and shaders

| Reference | Routes when | Produces |
|---|---|---|
| [threejs-renderer](../skills/3d/references/threejs-renderer.md) | vanilla renderer setup; washed, dark or blank output; `Clock`, `PostProcessing`, `RGBELoader` in code | one loop, one resize path, one dispose path |
| [threejs-r3f-next](../skills/3d/references/threejs-r3f-next.md) | `<Canvas>` in Next or React; `ssr: false` errors; double mount; GPU burning off-screen | a client-only scene behind a lazy wrapper, paused off-screen |
| [threejs-lookdev](../skills/3d/references/threejs-lookdev.md) | lighting rig, environment, materials, shadows; metals render black | environment, one to three lights, material roles, shadow cost |
| [threejs-loading](../skills/3d/references/threejs-loading.md) | loaders and decoders (meshopt, Draco, KTX2); freeze after the preloader | one loader module, a gated reveal |
| [threejs-postfx](../skills/3d/references/threejs-postfx.md) | bloom, LUT, DOF, SSAO; double tone mapping | one pipeline, a no-post baseline toggle |
| [threejs-interaction](../skills/3d/references/threejs-interaction.md) | picking, orbit or transform controls, glTF clips, physics proposals | event wiring, one mixer owner |
| [shader-glsl](../skills/3d/references/shader-glsl.md) | custom GLSL or patched materials on `WebGLRenderer` | stable uniforms, a cache key, a tested mobile fallback |
| [shader-tsl](../skills/3d/references/shader-tsl.md) | TSL, node materials, compute, `WebGPURenderer` | node graphs built once, a verified WebGL2 fallback, a pinned three version |

Defaults behind these (recorded decisions D4, D16): three r186+, R3F 9 with drei 10, `WebGLRenderer`
unless TSL or compute is needed, `Timer` rather than `Clock`, `RenderPipeline` rather than
`PostProcessing`, and the Canvas always in a Client Component under the Next App Router.

## Design

| Reference | Routes when | Produces |
|---|---|---|
| [design-art-direction](../skills/3d/references/design-art-direction.md) | what the 3D should be; "looks flat or CG"; six chapters that look alike | a world sentence, world bible, scene ledger, shot intent per chapter, a critique list |
| [design-lookdev-presets](../skills/3d/references/design-lookdev-presets.md) | picking a look; brand colour renders wrong; Blender and three disagree | one preset, one view transform, recorded in `3D.md` |

## Assets

| Reference | Routes when | Produces |
|---|---|---|
| [asset-acquire](../skills/3d/references/asset-acquire.md) | no model yet: stock, generative 3D, image-to-procedural | a source decision per object, a licence line per asset in `3D.md`, a raw file ready for cleanup |
| [asset-pipeline](../skills/3d/references/asset-pipeline.md) | a GLB must ship; about to type `gltf-transform`, `gltfpack`, `ktx` or `gltfjsx` | an optimised validated GLB, the untouched master, a before/after size line |

The pipeline never runs bare `gltf-transform optimize` (its defaults are lossy), keeps the master,
compresses once, prefers meshopt, and ends on a `glb-report` verdict plus a pixel-parity diff.

## Blender

| Reference | Routes when | Produces |
|---|---|---|
| [blender-channels](../skills/3d/references/blender-channels.md) | any Blender task; MCP or headless; a bridge timed out | a chosen channel, a working connection, recorded consent for arbitrary Python |
| [blender-scripting](../skills/3d/references/blender-scripting.md) | writing, debugging or reviewing any bpy snippet; a call returned FINISHED but nothing changed; a script exits 0 after failing | a short idempotent script that prints one JSON line, plus a verified result |
| [blender-modeling](../skills/3d/references/blender-modeling.md) | blockout, hard-surface, Geometry Nodes, repairing an import | a `.blend` that passes the numeric gate |
| [blender-shading](../skills/3d/references/blender-shading.md) | authoring or fixing a node material, procedural look, glass, skin, hair or toon shader; "flat in three.js" | a Principled-based material, every non-exportable node flagged for baking |
| [blender-uv-bake](../skills/3d/references/blender-uv-bake.md) | unwrapping, packing UVs, baking procedurals to maps, hi-to-lo normals, baking lighting | unwrapped UVs, baked images that passed the pixel gates, a material rebuilt from them |
| [blender-texturing](../skills/3d/references/blender-texturing.md) | image textures not yet on disk; seams, repeating lattice, baked-in light, wrong scale; "texture this mesh from a prompt" | a map set (albedo sRGB, others Non-Color), a material, a looked-at render, a licence line in the `3D.md` ledger |
| [blender-geometry-nodes](../skills/3d/references/blender-geometry-nodes.md) | scattering, arraying along curves, greebling, hair curves, repeat zones; a GN asset exports as its base mesh | a node group with named inputs, a verified evaluated count, an applied mesh or kept instances |
| [blender-rigging](../skills/3d/references/blender-rigging.md) | a mesh needs a skeleton, weights, Rigify, IK/FK or shape keys; a skinned GLB deforms wrongly | an armature that passes `rig_check.py`, with a pose-test render |
| [blender-animation](../skills/3d/references/blender-animation.md) | keyframes, loops or clips on objects, cameras, shape keys or armatures; a camera move from `shots.v1` needs a Blender twin | one named action per clip, constraints baked into keys, a numeric pose check |
| [blender-physics](../skills/3d/references/blender-physics.md) | anything must fall, drape, splash or grow hair; "bake the simulation"; a sim differs between runs | an approved cache on disk, then keys, shape keys or pre-rendered frames; verification JSON |
| [blender-lookdev-render](../skills/3d/references/blender-lookdev-render.md) | materials, bakes, lighting, stills, turntables, loops | web-safe materials, baked maps, numbered frames or a video |
| [blender-export](../skills/3d/references/blender-export.md) | export GLB or USDZ; "materials lost", "flat in three.js" | `.3d/versions/vNNN/<name>.glb`, uncompressed |
| [blender-version-traps](../skills/3d/references/blender-version-traps.md) | writing or debugging any `bpy` | a corrected call from the Blender 5.x old-to-new list |

The checkers `uv_check.py`, `rig_check.py`, `bake_maps.py`, `material_from_maps.py` and `texture_prep.py` run inside Blender like the other `assets/blender` scripts. Headless CLI is the channel for anything that must reproduce (inspect, export, bake, render); an MCP
bridge is for a user watching a live scene, and always asks consent because both servers execute
arbitrary Python. The skill never launches a second GUI Blender.

## Scroll-driven 3D

The pack is stack-agnostic and owns what is *inside* the pin. When the `scroll-animation` skill is
installed it owns scroll authority, the pin, reduced-motion collapse and scroll verification; `3d`
recommends it and never invokes it. Project rules always win.

| Reference | Routes when | Produces |
|---|---|---|
| [scroll-conductor](../skills/3d/references/scroll-conductor.md) | a live scene moves with scroll: camera path, chapters, pinned 3D | one conductor, a camera path keyed by chapter, a reduced-motion and poster plan |
| [scroll-video](../skills/3d/references/scroll-video.md) | a fixed move is pre-rendered and scrubbed; a scrub feels like mud or freezes on iPhone | frames or a render, desktop and mobile encodes, a poster, a player on the conductor |
| [scroll-adapters](../skills/3d/references/scroll-adapters.md) | feeding the conductor from native, Motion, GSAP, Lenis or `ScrollControls`; pin jumps on iPhone | one adapter on one range wrapper, a pin that holds, a device-check list |

All adapters compute progress over `wrapperHeight - 100lvh`, the distance the pin actually travels,
so iOS toolbar changes cannot hold the last frame.

## Optional

| Reference | Routes when | Produces |
|---|---|---|
| [spline](../skills/3d/references/spline.md) | Spline named; a designer maintains the scene | a decision (Spline runtime, Spline GLB, or R3F) in `3D.md`, an embed or export |
| [splats-xr](../skills/3d/references/splats-xr.md) | `.ply`, `.splat`, `.spz`; WebXR, AR, Quick Look | a splat or XR decision with budgets, a working embed |
| [cad-print](../skills/3d/references/cad-print.md) | a printable or mechanical part, STL or STEP, CAD in a web scene | a routing decision, verified geometry, a web GLB when needed |
| [SOURCES](../skills/3d/references/SOURCES.md) | where a technique came from; a licence question | a provenance answer |

## Routing by target use

[brief-approach](../skills/3d/references/brief-approach.md) picks the pipeline from the use and names
the files to read next; pick OBJECT live when the object is the point (inspect, compare, configure, a product page). Always added: design-art-direction for the look, asset-acquire when geometry
or textures must be sourced, shared-verification for the exit criteria.

| Use | Strategy | Read next |
|---|---|---|
| OBJECT live | real-time GLB the visitor spins, zooms or configures; compressed, poster first | threejs-interaction, threejs-lookdev, threejs-loading, asset-pipeline, threejs-r3f-next (Next or React) |
| Hero, live | real-time three.js or R3F, compressed GLB, poster first | threejs-renderer, threejs-r3f-next, threejs-lookdev, threejs-loading, asset-pipeline |
| Hero simple, video loop | pre-rendered WebM or MP4 (or frame sequence) from Blender, with a poster | blender-lookdev-render, blender-channels, shared-performance |
| Scroll world | real-time scene driven by normalised scroll; camera path from `shots.json` | scroll-conductor, scroll-adapters, threejs-r3f-next or threejs-renderer |
| Scroll scrub | pre-rendered frames or keyframe-dense video scrubbed by progress | blender-lookdev-render, scroll-conductor, scroll-adapters (and scroll-video for the encode and player) |
| Production stills, turntable | offline Blender render with comp tweaks | blender-lookdev-render, blender-modeling |
| Spline | Spline scene or embed | spline |
| Splat | Gaussian-splat viewer | splats-xr |
| AR | GLB plus USDZ or WebXR | splats-xr, asset-pipeline |
| Game asset | glTF or engine-native handoff; engine work out of scope | blender-modeling, blender-export, asset-pipeline |
| Print | offline render at 300 dpi or more, 16-bit, ICC | blender-lookdev-render |
| CAD part | CAD to mesh; printing handled elsewhere | cad-print |

## Budgets in one place

Defaults live in [shared-performance](../skills/3d/references/shared-performance.md) and are recorded
per project in `3D.md`; `glb-report` enforces them (sizes in MiB).

| Target | Triangles | GLB | Textures | Draw calls |
|---|---|---|---|---|
| Hero object, desktop | at most 100k | at most 3 MB | 1024 (2048 close-up) | at most 300 |
| Hero object, mobile | at most 100k (aim 50k) | at most 2 MB | 1024, KTX2 where possible | at most 100 |
| World, desktop | at most 750k | at most 15 MB total | at most 60 textures | at most 300 |
| World, mobile | at most 300k | at most 8 MB | at most 40 textures | at most 150 |
| AR | at most 100k | at most 5 MB | 1024 | few |
| Offline renders | unconstrained | n/a | any | n/a |
