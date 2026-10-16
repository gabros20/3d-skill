# Debug: symptom to cause

Purpose: Fast triage from an observed symptom to its likely cause, the check that confirms it, and the fix, across web and Blender.

Read when:
- Something renders wrong, slow, blank or differently from the reference.
- An export looks different in three.js than in Blender.

Skip when:
- Planning a build (→ the area reference).
- Proving a claim (→ [shared-verification](shared-verification.md)).

Inputs:
- The symptom, console output, a capture, the three.js version and renderer backend.

Produces:
- A confirmed cause (one check run) and one change.

## Contents

- Triage order
- Web
- Blender
- Traps

## Triage order

Scripts run by path (`<skill>/scripts/...`) with the project root as the working directory.

1. Reproduce on the same URL and viewport. Read console, page and network errors.
2. Confirm the build you expect is the one on that port, and that the tab is not stale (first row of the table).
3. Check the cause cheaply before changing code. Change one thing, re-measure.

## Web

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| Scroll-driven scene holds frame one, then snaps to the end | In order: (1) scrub video with sparse keyframes or a long GOP, so seeks land on one frame; (2) zero pin travel (section height collapsed, so progress spans no scroll distance); (3) progress not wired to the scene (read the value, log it); (4) stale CSS after a dev-server restart, a tab left open across it | (1) `ffprobe` keyframe interval; (2) measure the pinned section's scroll distance; (3) log normalized progress while scrolling; (4) `getComputedStyle(document.documentElement).getPropertyValue('--x')` for a token you know changed, or open a fresh tab | (1) re-encode short-GOP or all-intra ([scroll-video](scroll-video.md)); (2)-(3) [scroll-adapters](scroll-adapters.md), [scroll-conductor](scroll-conductor.md); (4) ask the developer to close the tab and open a new one; if it persists they clear the build cache and restart. You never restart their server |
| Black canvas, no errors ([threejs-renderer](threejs-renderer.md)) | Canvas has zero CSS size; camera inside or facing away; near/far wrong; no light on a lit material; context never created | element size, `renderer.getContext()`, `camera.position`, `renderer.info.render.calls` | Size the container; frame by bounding box; add environment light |
| Black canvas only in headless capture | No GL context, or hidden page so rAF never fires | capture report renderer string; `document.visibilityState` | Capture via `frame(n)`; use the headed or alternate flag set the report suggests |
| Washed-out or desaturated vs Blender or a glTF viewer | R3F `<Canvas>` default ACES tone mapping; wrong view transform; texture colour space | `renderer.toneMapping`, `renderer.outputColorSpace`, texture `colorSpace` | Pick the tone mapper deliberately (Neutral for brand colour, AgX for cinematic); colour textures sRGB, data textures linear ([threejs-lookdev](threejs-lookdev.md), [threejs-renderer](threejs-renderer.md)) |
| Too dark, black metals | No environment map; metalness 1 reflects nothing | `scene.environment` | Add a PMREM environment ([threejs-lookdev](threejs-lookdev.md)) |
| Flat or untextured after export | Material not Principled-compatible or textures not packed; export dropped them | open GLB in `<skill>/scripts/glb-report` | Re-export per [blender-export](blender-export.md); check compression passes in [asset-pipeline](asset-pipeline.md) |
| Z-fighting, flicker on coplanar faces | Overlapping surfaces; near/far ratio too wide | camera `near`/`far` | Raise `near`, offset or delete the duplicate face, `polygonOffset` for decals |
| Shadow acne or peter-panning | Bias wrong for light and scale | `light.shadow.bias`, `normalBias` | Tune `normalBias` first; tighten shadow camera bounds |
| First-frame jank on reveal | Textures upload and shaders compile on first draw | Performance panel at reveal | Preload and warm up ([threejs-loading](threejs-loading.md)) |
| Context lost | GPU memory pressure, too many renderers or tabs | `webglcontextlost` event | One renderer, dispose on unmount, lower DPR and textures ([threejs-renderer](threejs-renderer.md)) |
| Memory climbs after route changes | Undisposed geometries, materials, textures, render targets; double-mount in Strict Mode | `renderer.info.memory` after navigating back and forth | Dispose in effect cleanup; reuse loaders ([threejs-r3f-next](threejs-r3f-next.md)) |
| Jerky scroll scrub, soft feel | Two smoothing layers stacked, or scroll state read from a different clock | one smoothing owner? | One owner, scrub from normalized progress ([scroll-conductor](scroll-conductor.md), [scroll-adapters](scroll-adapters.md)) |
| Critic will not converge, or the scene still looks CG next to the reference after tuning | Chasing a limit with the wrong techniques, or a bar above the ceiling; an exhausted loop | `<skill>/scripts/preview rounds`; `.3d/feasibility.json` | Follow the verdict and label defects per [realism-gate](realism-gate.md); try the contrasty-environment, tone, material and baked-light techniques in [realism-toolbox](realism-toolbox.md) before any screen-space pass |
| Hot phone, dropped frames | Fill-rate: DPR, post, transparency | triage order in [shared-performance](shared-performance.md) | Cap DPR, remove post, render on demand |
| Next build error or hydration mismatch with the Canvas | Canvas rendered on the server | error mentions `window`/`document` | Canvas in a Client Component; `dynamic(..., { ssr:false })` only inside one ([threejs-r3f-next](threejs-r3f-next.md)) |
| Everything looks mirrored or huge/tiny | Units or handedness (cm vs m, Z-up vs Y-up) | object bounding box | Fix in Blender export scale/axis, not with a runtime fudge |

## Blender

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| Materials lost or wrong after export | Non-Principled node tree, procedural textures not baked, unpacked images | inspect scene with `assets/blender/inspect_scene.py` | Bake procedurals, use Principled, pack textures |
| Shape keys or modifiers vanish in GLB | `export_apply=True` drops shape keys; Geometry Nodes not applied | exporter params introspected at runtime | Decide per modifier; export a copy with GN applied |
| Normals look faceted or inverted | Negative scale, flipped normals, missing smooth shading | inspect output for scale and normals | Apply scale, recalculate normals, shade smooth |
| MCP call times out | Long export or render over the default tool timeout; Blender main thread busy | tool timeout setting | Split the request; raise the per-server timeout; use headless CLI for exports ([blender-channels](blender-channels.md)) |
| MCP says connected but does nothing | Add-on server not started, or two Blender MCPs active | add-on panel status | Start the server; keep only one MCP active |
| Headless script runs but changes nothing | Script ran before the `.blend` loaded | argument order | `blender -b file.blend --python-exit-code 1 --python x.py -- args` (file first) |

## Traps

- Debugging scene code before ruling out zero pin travel and a stale tab.
- Fixing a colour problem with exposure when the view transform differs.
- Testing in one tab that has survived several server restarts.
