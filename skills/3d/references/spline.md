# Spline

Purpose: Decide when a Spline scene beats hand-built three.js/R3F, and embed or export it without creating a second scroll or render authority.

Read when:
- The user names Spline, has a `.splinecode`/spline.design link, or a designer will maintain the scene.
- Choosing between Spline and R3F for a hero object or embed.
- A Spline scene is slow, clipped, or fights the page's scroll animation.

Skip when:
- The scene is code-owned, scroll-linked through the conductor, or held to a byte/frame budget (→ [threejs-r3f-next](threejs-r3f-next.md), [scroll-conductor](scroll-conductor.md)).
- You only need the model (export GLB → [asset-pipeline](asset-pipeline.md)).

Inputs:
- Who maintains the scene, the scroll/interaction requirement, target devices, whether the Spline desktop app is installed.

Produces:
- A decision (Spline runtime, Spline-exported GLB, or R3F) recorded in `3D.md`, and an embed or export.

## Spline or R3F

Choose Spline when a designer iterates visually, the piece is one self-contained embed with built-in states and events, and mobile weight is manageable. Choose R3F when engineers maintain it, it is driven by scroll state from the conductor, it shares a scene with other 3D, or it must meet the budgets in [shared-performance](shared-performance.md). Rule of thumb: Spline when a designer will maintain it, three.js when engineers will.

A `.splinecode` scene runs in Spline's own runtime and renderer. It cannot share a scene, camera, post chain or loader pipeline with your three.js canvas, and it bypasses gltf-transform.

## Packages (current)

- `@splinetool/runtime` releases almost daily; `@splinetool/react-spline` 4.1.0 has had no npm release since 2025-07. Install both: `npm i @splinetool/react-spline @splinetool/runtime`, and pin the runtime.
- Scene API: `onLoad(app)`, `app.findObjectByName(name)`, `emitEvent`, `emitEventReverse`, `setZoom`; `renderOnDemand` is on by default.
- Self-host the `.splinecode` file when CORS blocks the Spline CDN.

## Next.js

1. The component is client-only: put it in a Client Component (`'use client'`); any `dynamic(..., { ssr:false })` also lives there, never in a Server Component page.
2. `@splinetool/react-spline/next` renders a server-side blurred placeholder: use it for an above-the-fold hero to avoid a blank flash.
3. Lazy-load below the fold; give the container fixed dimensions so layout does not shift.
4. Always render a designed poster plus real DOM text; the canvas is decoration, not the content.

## Control and scroll

- Drive Spline objects from code only through `findObjectByName` and your own frame loop, reading the conductor's normalized state.
- NEVER let Spline's scroll/event system and the page conductor both move the same object. One authority; disable one set of triggers in the Spline file.
- Spline events and animations work only in the Vanilla JS and React exports, not in the three.js or R3F exports.

## Weight and performance

No official polygon ceiling exists. Practical limits: open the editor's Performance panel (Export) and fix what it flags; delete unused objects; keep subdivision ≤ 3; set geometry compression to Performance and compress images; ship a lower-detail mobile scene; avoid shadows, reflections and more than 2-3 lights on phones. Measure the real scene on a mid phone with the project's frame budget before committing.

## Exporting to three

Spline exports GLB, glTF, STL and USDZ, and code for Vanilla JS, three.js (`@splinetool/loader`), React/Next and R3F. Exported code does not sync back to the Spline file, and `r3f-spline` has been dead since 2022. For a model you want to own: export GLB, then [asset-pipeline](asset-pipeline.md); materials will need re-lighting under your environment.

## Spline MCP (official)

Spline V2 (launched 2026-08) ships an MCP server inside the desktop app (macOS/Windows); it registers itself in the client config and exposes `mcp__Spline__3d_*` / `2d_*` tools. It does not work from the browser app. Rules:
1. Check the tools exist in your own tool list. If not connected, say so and ask the user to open the app; do not silently fall back to code.
2. Load the surface's skill call before the first edit (per the docs), and re-read the document before every edit: a human may have moved things.
3. Community `aydinfer/spline-mcp-server` is archived and calls nonexistent endpoints: do not use.
4. The MCP executes edits in the user's open document: confirm before bulk changes.
