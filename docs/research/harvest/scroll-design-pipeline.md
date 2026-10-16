# Harvest R4: scroll-driven 3D, art direction, asset pipeline, Spline / splats / generative

Compiled 2026-10-16. Grades: [V] official · [B] measured · [P] practitioner · [U] unverified. "UOWN" = the user's own battle-tested material (highest weight). Sources are under `docs/research/community-scan/sources/` unless a path is given. Nothing installed or run.

| Source | Licence | Use |
|---|---|---|
| UOWN `~/Documents/Personal/Projects/scroll-animation-skill/skills/scroll-animation` (SKILL + 17 refs; measurements "S1-S7", Sept 2026, Chromium 153 / WebKit 26.6 [B]) | own | route to it, never duplicate |
| UOWN eagle-website `CLAUDE.md`, `docs/MOTION-DESIGN-SYSTEM.md`, `docs/FLUID-SCALE.md`, `src/components/motion/ScrubStage.tsx` | own | project rules |
| MengTo/Skills `build-threejs-scroll-worlds`, `3d-paper-material`, `3d-orbit-inspect-demo` (commit 83a47fe, 2026-10-06) | MIT | adopt method, adapt scroll layer |
| czlonkowski/blender-web-3d-skill v2.0 (858762f, 2026-09-23; three r186) | MIT | pipeline + look-dev; 1 maintainer, young [P] |
| skinnye/3d-web-pack (cabd221, 2026-06-14) | MIT | `optimize-3d-assets` only; scroll skill = adapter example |
| jangtrinh fork of img2threejs v1.5.0 (original: img2threejs/img2threejs, ~18K stars) | Apache-2.0 | generative-by-code process |
| sickn33 `3d-web-experience`, `premium-3d-website`, `3d-ui` | MIT | generic; low yield |
| freshtechbro `spline-interactive`, `web3d-integration-patterns` (2025-11-20, stale) | MIT | Spline API shape only |
| gabremoku `immersive-3d-web` (f51cbe4) | none found: inspire only | concept-to-form, retrofit |
| SkylarKitchen `3d-assembly-manual` | none found | niche ortho-diagram explainer genre only |

Not captured: MengTo's `scroll-conductor.js` and demo HTML; the contract is recoverable from `realtime-architecture.md` §1, §5, §7.

---

## 1. Scroll to normalised state to one conductor to scene (stack-agnostic core)

**The shape (MengTo, corroborated independently by UOWN).** Native scroll is the only source of truth. One conductor turns it into one state object. Camera, light, fog, DOM, interactions and analytics all read that object and never read scroll. Two values are kept: `exact` (reproducible; drives logic) and `smooth` (damped; drives visuals only). UOWN invariant 3 says the same in other words: "Smooth once; logic reads exact progress" [B].

```
adapter (scroll source) -> exact -> conductor -> { exact, smooth, index, localExact, localSmooth, direction, reduced } -> scene / DOM
```

### Procedure
1. **Name the clock first** (UOWN): trigger, scroll, media or render. A 3D scene is a *render* clock fed by a *scroll* value. Promote to scroll only where the reader should drive the motion (UOWN MOTION-DESIGN-SYSTEM §2).
2. **Write the scene ledger** (§2) with `scrollWeight` per chapter. Progress is fractional chapter index (e.g. 2.35), not 0..1, so weights and per-chapter overrides are data.
3. **Build the range wrapper + sticky pin** exactly as `scroll-animation/references/scenes.md` §1: wrapper measured, pin `100lvh` holding the canvas, content layer `margin-top:-100lvh`. The canvas is just "media" in that pin.
4. **Adapter produces `exact`** (table below). Re-measure after `document.fonts.ready` and critical images, on `ResizeObserver`, on width/orientation change; update immediately on `scroll`, `pageshow`, `hashchange`, history restore.
5. **Conductor damps `smooth`** with `damp(cur, target, lambda, dt)`, lambda about 4.5-7, `dt = min(delta, 1/30)`. Never `lerp(a, b, 0.1)` per frame.
6. **Resolve once per frame**: `{a, b, t} = segment(smooth)`; interpolate every declared channel (key, fog, emissive, grade) from the ledger; position/target via Catmull-Rom (`centripetal`, 0.5) then `lookAt`; quaternion `slerp` only for deliberate roll. Never Euler-lerp.
7. **Frame order** (MengTo): read exact + input, damp, resolve camera + world, mixers/sims/particles, proxies + DOM state, render post, sample perf.
8. **DOM gets exact** (nav, `aria-current`, hash, gating of interactions); **visuals get smooth** (scrims, word reveals). Interaction availability is exact-range, never damped.
9. **Discrete states change per transition, not per frame** (UOWN invariant 4): latch with hysteresis, two thresholds per boundary, hysteresis as a ratio of the hold (UOWN scenes §3).
10. **Verify by progress, not pixels** (UOWN verification §1): drive to 0, 1/4, 1/2, 3/4, 1 of the wrapper, wait for glide, screenshot, tile into a contact sheet, read state (`data-scene-state`, `renderer.info`).

### Adapters: when each
| Adapter | Use when | Wiring and numbers | Not when |
|---|---|---|---|
| **Native scroll + rect maths** | default; reading-first pages; any 3D scene whose state is a function of one wrapper | `progress = -rect.top/(height-innerHeight)`; rAF read inside the render loop is fine | none; it is the base case |
| **CSS scroll-driven (`animation-timeline`)** | decoration around the canvas (progress bar, fades, label parallax) | Chromium 115+, Safari 26+, not Firefox stable [B, UOWN]; under Lenis Safari reads the previous frame | driving camera/uniforms; anything that must register to the render |
| **Motion `useScroll`** (the Eagle path) | React + Motion-only repos (eagle-website: no GSAP, no Lenis) | `useScroll({target: wrapperRef, offset: ['start start','end end']})` at module-scope offset; `useMotionValueEvent` writes a **ref**, never `style` and never React state; read `useReducedMotionLive()` | ScrollSmoother routes (reads unsmoothed scroll, up to 244 px off [B]) |
| **GSAP ScrollTrigger** | repo already loads GSAP; timeline with about 4+ named spans; ScrollSmoother pages | trigger `top top`/`bottom bottom`, `onUpdate: self.progress` into a store, read in render loop; `scrub:true` under Lenis; `ignoreMobileResize:true`; create in page order; `gsap.matchMedia` | repo bans it (eagle-website does) |
| **Lenis** | wants inertial scroll; WebGL must line up with DOM boxes; mixed engines | ticker -> `lenis.raf` -> `ScrollTrigger.update`; `autoRaf:false` (`ReactLenis` defaults true); touch stays native; capped 60 fps in Safari [B]; `data-lenis-prevent` on nested scrollers | repo bans it; reading routes |
| **drei `ScrollControls`** | a pure full-screen 3D experience with no page flow | virtual scroller inside the Canvas; `useScroll().offset`; `<Scroll html>` | a marketing page: it is a nested second scroll authority (inference from UOWN invariant 1; anchors, Lenis, sticky, iOS pin all break) [U] |

**R3F render coupling** (UOWN scroll-authority §6 [B]): canvas that does not track DOM boxes: `frameloop="demand"` + `invalidate()` from the writer. Canvas whose plane tracks a DOM box under Lenis: `frameloop="never"` + `advance()` from the GSAP ticker after Lenis (0 frames late); demand+invalidate was 1 frame late on every other frame.

### ALWAYS / NEVER
- ALWAYS one scroll authority per route; stamp it (`<html data-scroll-authority>`). NEVER two (Lenis + ScrollSmoother, `normalizeScroll` with Lenis, CSS `scroll-behavior:smooth` with ScrollTrigger).
- ALWAYS smooth once. NEVER spring/lerp on top of Lenis (trailed 16-18 frames, about 0.3 s [B]).
- ALWAYS write per-frame values to refs/uniforms. NEVER bind a scroll value to Motion `style` (drifts back past input range over a pin; Motion 13.4 [B]).
- NEVER integrate wheel delta into story position (MengTo); scroll must stay reversible, reload-safe, jump-safe: same position, same state forward, backward, after a flick, after reload.
- ALWAYS size the pin `lvh` and the content margin in the same unit; NEVER `dvh` inside a scene (relayout during toolbar animation); NEVER `svh` pin (page shows along the bottom) [B, UOWN scenes §1, ios §1].
- NEVER a transform on the wrapper/pin/ancestor; NEVER `overflow:hidden` (any axis) on an ancestor, use `clip`; NEVER `content-visibility:auto` in or around a runway.
- ALWAYS clamp `dt`; pause render on `document.hidden` and off-screen (IO-gate with a wide warm margin and a tight run margin, UOWN perf §6).

### Gotchas and numbers
- Progress per viewport is `1/(N-1)`: three 1-vh acts land at halves, not thirds. Pace with an empty `data-scene-spacer` act (UOWN scenes §2; Eagle's middle act is `200svh`).
- Responsive camera: author endpoints per breakpoint, **rebuild the curve on width/orientation change; do not blend desktop to mobile curve** (MengTo). Ignore height-only resizes on touch (same fix as UOWN `ignoreMobileResize`; defer geometry reads one rAF). Drive framing by viewport **height**, not width (UOWN §4.8; compatible with MengTo's tall-screen pullback `max(0, h/w - 1.15)` as an emergency fallback only).
- Pointer parallax lives in a separate `inputRig` child of the path rig, never in waypoint data; clamp, damp, blend out near transitions (MengTo).
- Stale CSS on `/` produces "frame one then snap to end" for ANY pinned scene including a canvas: read `getComputedStyle(documentElement).getPropertyValue('--fluid')` first; the fix is a fresh tab, then `rm -rf .next` (eagle CLAUDE.md). **The dev server is the developer's: the 3d skill must ask, never start/kill it.**
- iOS restores scroll after scripts ran: re-derive state from the rect on mount, resume, bfcache, focus (UOWN `onRehydrate`).
- **Source defects not to copy:** skinnye `scroll-3d-scene` uses `scrub:1` plus `camera.position.lerp(pos, 0.1)` per frame (double smoothing, frame-rate dependent) and `@studio-freight/lenis` (renamed `lenis`; check) [P]. freshtechbro uses `framer-motion-3d` (unmaintained; verify on React 19) [U]. MengTo's `uv2` for AO is pre-r152 vocabulary; czlonkowski sets `texture.channel = 1` [P].

### Reduced motion, a11y, failure
- Alternate scene, not removal: pin collapses (`height:auto`), acts show end state, **WebGL: check query and WebGL support once, render the poster, never load the 3D bundle** (UOWN accessibility). Live listener: MengTo snaps camera/state to the nearest composed chapter; ambient loops, stagger, blur stop; DOM story intact.
- DOM carries meaning: real headings in order, copy readable with canvas hidden, 44 px DOM proxies for every hotspot, focus state shared with the 3D state through one setter (MengTo). Ambient WebGL over 5 s needs a pause control; no strobe over 3 flashes/s (WCAG 2.2.2/2.3.1).
- Context loss: `preventDefault`, pause, fallback, rebuild from retained sources, reapply exact state; never reload unprompted.

### Composition with the scroll-animation skill (route, do not duplicate)
| scroll-animation owns | 3d owns |
|---|---|
| scroll authority per route, Lenis/ScrollSmoother wiring, one tick | the conductor *contract* (state object), the adapter that feeds it from that authority |
| range wrapper, sticky `lvh` pin, acts, latch, holds, `inert`, scroll well, rails | what is inside the pin: renderer, scene graph, camera path, world-state channels |
| reduced-motion CSS collapse of the pin; `useReducedMotionLive`; pause controls | the poster/no-WebGL alternate for the *canvas*; skipping the 3D bundle |
| `ANIMATION.md` scene ledger (clock, block, runway, reduced alt) | the world bible + chapter ledger (camera, world state, assets); one row of `ANIMATION.md` links to it |
| `verify-motion.mjs`, `audit-motion.mjs`, stale-stylesheet check, device discipline | visual QA of the frame, perf (calls, triangles, ms), asset checks |
| pre-rendered video/image-sequence scrub (`ScrubVideo`, `FrameSequence`, all-intra encode) | real-time 3D only when geometry must stay spatial/interactive (MengTo: "do not disguise a video as Three.js") |
Decision: if the art is a fixed camera move with no interaction, a rendered sequence (`sequences.md` §1: exact at any scroll speed, 5.5 MiB decoded per 1600x900 frame) or all-intra scrub video beats a live world on cost. `preflight.md` §3.1 already lists Three/R3F as the "Immersive" engine and defers everything inside the canvas.

---

## 2. 3D art direction and design

**Process (MengTo `world-bible.md`, the strongest source).**
1. **Intake** only what cannot be inferred: purpose, subject, audience, ordered beats, topology (continuous / connected sets / layered reveal), art direction, interaction depth, device floor, existing assets, byte budget. If a working scene or approved reference exists, copy its measured constants into the ledger; "do not replace measured details with adjectives."
2. **World sentence**: subject + spatial journey + transformation; plus an interaction sentence ("scroll owns the camera and global time; pointer/touch/keyboard reveal local evidence"). Reject sentences that only describe style.
3. **Form follows subject** (gabremoku `concept-to-form`, practitioner, no licence): before geometry write "This scene shows ___, moving like ___, because ___". Icosahedra/torus knots are the default trap. "No hero object" (real product UI, gradient, video) is a legitimate answer. Motion borrows from the referent (mechanical = stepped, signal = pulse then rest). "Calm is not frozen": per-node sine drift with random phase.
4. **Visual bible with real constants**: unit (1 u = 1 m), human reference 1.7, bevel 0.5-2% of width, silhouette > structure > accent, palette by role name, FOV range, horizon, safe copy zones per breakpoint, motion table (camera damping 4.5-7; pointer parallax 0.1-0.5 deg; dust 0.02-0.12 u/s; word reveal 40-90 ms).
5. **Scene ledger** (4-8 chapters): `id, beat, landmark, change (beyond copy), scrollWeight, camera{position,target,fov,mobile}, occlusion, worldState, focus, copy, foreground, assets, fallback`. **Reject a chapter whose landmark, change and camera cannot be named; six dolly-ins at one centre are not six scenes.**
6. **Camera ledger before curves**: endpoints per breakpoint, roll, near/far, failure risk. Inspect each segment for clipping, target flips, velocity spikes at joins, copy overlap. Sample offline against coarse proxies, do not collide per frame. Parameterise by chapter progress, not arc length. Hide unavoidable seams behind occlusion/dark/fog/threshold; never teleport in open space.
7. **Compose endpoints at desktop and mobile first**, then interpolate. Mobile is a second composition (pull back, own copy zones), not a crop.

**Lighting / look-dev recipes (czlonkowski `lookdev-and-shaders.md` [P], numbers local):**
- One sun: key direction = sky disc = env warm side = terminator. AgX on both sides (Blender view transform and `renderer.toneMapping`) so render and browser match. Bloom only on real lights: threshold just above the brightest lit surface (about 1.1-1.2 linear), strength 0.25-0.35, radius about 0.2; wide radius = haze = "amateur". Contrast from ratio, not exposure: `environmentIntensity` about 0.4-0.5 vs key about 4 (0.85 reads grey/CG). Emissive window about 3, above about 7 AgX washes to white. Life at three tempos (slow 0.07 rad/s, medium 2-4 s strobes, rare flicker). Finish pass after OutputPass (vignette, radial CA, animated grain also dithers banding).
- MengTo: one authored key + restrained fill + practicals; add a light only for a visible relationship; 1-2 shadow casters mobile, 2-4 desktop; fog separates depth planes, keep the focal landmark inside the contrast window; match emissive geometry, glow sprite, real light and bloom threshold; compose the unprocessed frame first, effects must not hide weak materials. Disable each system in turn in QA; delete any with no named job.
- Marketing-hero shortcut (gabremoku): drei `Environment` HDRI instead of hand lights, `ContactShadows` for grounding.
- Baked light for interiors/close-ups (czlonkowski `baked-lighting.md`): Cycles diffuse bake lighting-only (`use_pass_color=False`), about 64 samples, margin 3, 2048 float atlas, dedicated UV set; median 3x3 then Gaussian 3x3; store as Radiance `.hdr` not the glTF occlusion slot; `lightMap.channel=1`, `flipY=false`, intensity times stored scale. Skip for single-sun exteriors.

**Material recipes (MengTo + `3d-paper-material`):**
- Colour space: base colour and emissive sRGB; normal/rough/metal/AO/masks `NoColorSpace`; HDR via PMREM. Never one file as both colour and data.
- Texel budget: `required px = projected CSS px x DPR x 1.0-1.5`; 2K-4K only for surfaces filling frame, 512-1K atlases elsewhere; consistent density in a camera range. `normalScale` 0.25-0.8. `alphaTest` for foliage before blended planes. Wear is causal (edges polish, recesses grime).
- Detail by scale: geometry for silhouette, shader patch for surface (`onBeforeCompile` + `customProgramCacheKey`, patch PBR, do not replace). Detail fades before it aliases (`fwidth`, about 3 px). Hash instead of texture for variation.
- Close-up survival (paper skill): bake a second high-density window at the focus point (7.3 px/mm overview, 22.8 px/mm macro); never tile a small texture; `alphaToCoverage` not `alphaTest` for soft edges. Paper constants are scene-specific.

**Hero-object inspect (`3d-orbit-inspect-demo`):** hover leans the *camera* (az +-0.30, el +-0.09, damping 4.5/s, gain from a raycast hit); click lifts the *object* to a second render layer (1.0 s in, 0.6 s home, zoom 0.70-1.45); lean freezes on pointerdown and while inspecting; click = under 6 px and 600 ms; lights need `layers.enable(1)` or the lifted piece is black; real button opener, focus returns after copy is visible; zero frames at rest.

---

## 3. Asset pipeline: author, export, optimise, validate, load

Sources: czlonkowski `export-pipeline`/`performance`, skinnye `optimize-3d-assets`, MengTo `realtime-architecture` §4, sickn33 (generic). Blender-side detail belongs to R2.

### Procedure
1. **Author with the contract in mind.** Units 1 u = 1 m; scale only in the app. Name materials and pivots deliberately: names are the contract with the runtime (czlonkowski). One object per (material, animation root) is the cheapest draw-call fix. Linked duplicates + `export_gpu_instances` for repeats.
2. **Export raw, scoped.** Select one root hierarchy; `export_apply=True`; no cameras/lights; animations on; **no compression at this stage** (lossless archive). Keep versioned files, never overwrite (`model-raw-v007.glb`).
3. **Optimise in one reproducible step**, always writing a new file and printing before/after: `gltf-transform inspect`, then `optimize` chain `dedup, instance, join(keepNamed), weld, [simplify], resample, prune(keepLeaves), sparse, textureCompress, meshopt|draco`. Then targeted `resize` (cap 2048), or `gltfpack -cc`. Demo: 1,470 KB to 332 KB [P/B local].
4. **Textures**: WebP for smallest download; KTX2 (ETC1S colour, UASTC normals) when VRAM matters (decoded WebP is full RGBA8 in VRAM; KTX2 stays compressed, 4-8x less [P]). Needs `ktx` CLI. If washed out, raise quality or skip compressing normals (skinnye).
5. **Validate**: re-inspect (nodes, meshes, textures, extensions); load in a bare scene; compare hero view and a close-up at target DPR; read `renderer.info` with `autoReset=false` and manual reset so every pass counts; check pivots still animate and material names survive.
6. **Load**: `<link rel="preload" as="fetch" crossorigin>` for the hero GLB (biggest TTFF win, czlonkowski); decoders (Draco, Basis, meshopt) version-pinned to the three runtime; `await renderer.compileAsync(scene, camera)` before reveal; groups `idle, queued, loading, ready|failed, retired`; prefetch window `round(exact) + direction x {0,1,2}`; keep the previous chapter resident until reverse scroll is safe; progress reported by required bytes; designed poster + semantic DOM if anything fails; lazy-load the whole canvas chunk (route split + Suspense) so non-3D routes pay nothing (gabremoku retrofit).

### Budgets (starting envelopes, profile on device; MengTo [P], not success claims)
| | mobile | desktop |
|---|---:|---:|
| DPR cap | 1.25-1.5 | 1.5-2 |
| visible triangles | 150-300k | 500k-1.2M |
| draw calls | 50-90 | 90-160 |
| shadowed lights | 1-2 | 2-4 |
| blended fullscreen layers | 2 | 3 |
| critical initial transfer | 3-6 MB | 5-10 MB |
| frame time | <=16.7 ideal, <=25 fallback | <=16.7 |
Quality governor: downgrade after sustained misses (MengTo: 120 frames over 22 ms; czlonkowski: p75 over 23 ms in a 90-frame window), **upgrade only after 5 healthy windows (p75 under 18 ms)**; symmetric thresholds flap. Cheapest lever first: DPR, post resolution (half-res bloom costs about a quarter), reflections, shadow update rate, transparent particles, then LOD. Profile toggle order in MengTo `quality-and-qa` §10.

### Tools
`@gltf-transform/cli` (pin it; verify flags per version), `gltfpack`, KTX-Software `ktx`, `gltfjsx -t -T`, Blender headless. Preflight detects and proposes, never auto-installs.

### Traps (each silently breaks output; czlonkowski)
- `flatten()` re-parents meshes under JS-driven pivots and `prune()` deletes the empty pivot: part stops moving, no error. Keep flatten opt-in, `prune keepLeaves`.
- `palette()` merges materials: names the runtime keys on vanish. `instance()` is skipped when the file has any animation.
- meshopt quantises positions (`KHR_mesh_quantization`, Int16 + node matrix): transforming geometry in place truncates (use `getX/Y/Z`, not `getComponent`); object-space shader detail sized in metres "compiles but shows nothing".
- Drivers do not export (re-drive in JS); collection instances export expanded (draw calls multiply); Normal Map chained via Bump breaks WebP export; no-UV meshes need UV0 first.
- Shadow: `light.shadow.autoUpdate=false` needs `light.shadow.needsUpdate` per light, else receivers sample garbage and the **whole model vanishes** with normal draw counts.
- Bloom + Apple GPUs: one NaN fragment smears to a black frame. Always a NaN-scrub pass before bloom; display-referred effects after OutputPass.
- **Hidden tab: rAF never fires, `Timer` delta 0, screenshots show a stale/black frame.** Check `visibilityState` first; agent QA loops need a debug hook that steps frames with fixed dt and reads `toDataURL` (needs `preserveDrawingBuffer`, debug builds only).
- Meshopt vs Draco: czlonkowski says meshopt decodes 5-10x faster and wins for most scenes, Draco for huge static scans; skinnye defaults to Draco. **Conflict, defer to R1 (official gltf-transform/three docs).** `RGBELoader` rename to `HDRLoader` is czlonkowski only [P, verify in R1].

---

## 4. Spline, Gaussian splats, generative 3D

### Spline vs R3F
What the sources teach (freshtechbro stale 2025-11-20, sickn33 generic; no official docs read) [P]:
1. Choose Spline for designer-authored, quick, one-element embeds with built-in state/event animation. Choose R3F/three when the scene is code-owned, scroll-linked, part of a conductor, or held to a byte/frame budget.
2. Embed: `@splinetool/react-spline`; Next: `@splinetool/react-spline/next` (SSR placeholder, avoids hydration errors); `React.lazy` + Suspense; `prefetch` link; `renderOnDemand`.
3. Control from code: `onLoad(app)`, `app.findObjectByName()`, write `position/rotation/scale/visible/material.color` in *your* frame loop from conductor state; events `onSplineMouseDown/Hover/Scroll`.
4. Mobile: separate lower-detail scene, lower canvas res, no shadows/reflections, 2-3 lights max.
5. Escape hatch: export GLB and take it into three.
- NEVER let Spline's own event/scroll system and the page conductor both drive the same object (second authority; freshtechbro's own "animation conflicts" pitfall).
- Gaps: no numbers for runtime weight, `.splinecode` size, licence/pricing; web research needed.

### Gaussian splats
**No harvested source teaches it** (grep of all 99 skill folders: zero hits). Seeds, all [U], for a web lane: runtime libs (Spark, gsplat.js), formats (.ply/.splat/.spz/.ksplat), mobile cost, sorting, no-physical-shading, fallback poster. Do not write splat rules from this document.

### Generative 3D
- **Image to procedural code (img2threejs v1.5.0, Apache-2.0):** reconstruction-by-code, not photogrammetry. Order: validate image suitability (pass/conditional/reject: ambiguous target, scene not object, hidden/blurred/transparent key shape, smoke/liquid/glass/lace) then `qualityContract` then spec (component hierarchy, topology class per component before choosing a primitive, PBR channels independent, pivots/sockets) then locked build passes (blockout, structure, form, material, lighting, interaction, optimisation) with a screenshot-vs-reference review at each pass. Gates: a failed identity-defining feature blocks `continue` even if the global score passes; child parts need attachment data (no mid-air parts); `check_part_coverage` scores structure (every other gate scores pixels). **Patterned surfaces: project the de-lit reference crop, do not fake the pattern procedurally.** ALWAYS state approximate/stylised; never over-claim ("improved" is not "done"); list what changed with values and what still differs. Fit for Eagle: low-medium (brand-object stand-ins); heavy ceremony, so borrow the *gates* (suitability, spec before code, per-pass screenshot, no over-claiming), not the CLI.
- **Text-to-3D (Tripo/Meshy/fal):** not read; all need paid APIs (REPORT §292). Seed rules [U]: treat output as an untrusted asset, run the §3 pipeline (decimate/retopo, bake, optimise), check output licence, never ship raw.

---

## 5. Router signals (for the `3d` SKILL.md)

| Signal in request / repo | Route |
|---|---|
| "scroll", "scrub", "pinned 3D", "camera moves as you scroll", "chapters", `ScrubStage`, `useScroll` | 3d scroll pack (§1) + hand scroll authority/pin/reduced-motion/verify to `scroll-animation` |
| repo has `motion` and no `gsap`/`lenis` (eagle-website) | Motion adapter, native authority; never suggest GSAP/Lenis/ScrollControls |
| `gsap`, `lenis`, `@14islands/r3f-scroll-rig` in `package.json` | GSAP/Lenis adapter, one tick, `advance()` |
| "fixed camera move", "no interaction", "exploded view", "turntable" | ask: rendered sequence/scrub video (`scroll-animation`) before real-time |
| "scrub stuck on frame one", "snaps at the bottom", "full-bleed no gutters" | stale stylesheet check first; developer restarts server |
| "world", "chapters", "mood", "art direction", "hero object", "looks flat/CG/amateur" | art-direction pack (§2): world sentence, ledger, look-dev numbers |
| "what should the 3D be", "hero for X brand" | concept-to-form sentence; "no object" allowed |
| "model too heavy", ".glb", "KTX2", "meshopt", "draco", "gltf-transform", "slow load" | pipeline pack (§3) |
| "black frame", "model disappeared", "shader does nothing", "part stopped moving" | §3 traps first |
| "Spline", "splinecode", "no-code 3D" | Spline pack: when vs R3F, Next embed, no second authority |
| ".splat", ".ply", "gaussian", "NeRF scan" | splat pack (gap: research first) |
| "from this image/photo/logo make a 3D", "text to 3D", "Tripo", "Meshy" | generative pack: suitability gate, state approximation |
| `ANIMATION.md` exists | add the world's row to its scene ledger |
| iPhone/Safari 3D problem | UOWN `ios-safari-motion.md`; real device only |

## 6. Discrepancies and gaps for the lead
1. **Pin unit conflict.** Eagle `docs/MOTION-DESIGN-SYSTEM.md` §4.2 and `ScrubStage` use `100svh`; scroll-animation (measured, Sept 2026) mandates `lvh` pin + `lvh` margin (svh leaves a page band, dvh thrashes). The 3d skill should route to the measured rule and flag the Eagle doc as older.
2. Eagle doc says "no ScrollSmoother, no Lenis"; scroll-animation ships both. Project rule wins for eagle-website; keep adapters generic.
3. No source covers splats; Spline numbers and licence missing; text-to-3D unread; MengTo conductor file not captured; frontier (WebGPU/TSL scroll scenes) not addressed here (R1/R3).
4. No community skill teaches Motion; the Motion adapter is assembled from UOWN measurements.
