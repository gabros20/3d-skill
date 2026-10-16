# Scroll Adapters

Purpose: Pick and wire the one scroll source that feeds the conductor, state the pin rule when `scroll-animation` is absent, and avoid the iOS Safari traps.

Read when:
- Connecting `<skill>/assets/web/conductor.ts` to native scroll, Motion, GSAP ScrollTrigger, Lenis or drei `ScrollControls`.
- The pinned canvas jumps, shows page along the bottom, or lags the DOM on iPhone or Safari.

Skip when:
- What the conductor computes and who owns what → [scroll-conductor](scroll-conductor.md).
- The page already has a `scroll-animation` scene: its pin, authority and verification win; adapt only the feed.

Inputs:
- `package.json` stack (`<skill>/scripts/capabilities` lists it), the route's scroll authority, project motion rules.

Produces:
- One adapter attached to one range wrapper, a pin that holds, a device-check list.

## Choose

Project rules first (a MOTION doc, CLAUDE.md): if they ban an engine, never propose it. Then detect:

| Found in `package.json` / page | Adapter | Notes |
|---|---|---|
| `motion`, no `gsap`, no `lenis` | `<skill>/assets/web/adapters/motion.ts` | native authority; do not suggest GSAP, Lenis or ScrollControls |
| `gsap` | `<skill>/assets/web/adapters/gsap.ts` | ScrollSmoother route: this one only |
| `lenis` (not `@studio-freight/lenis`, renamed) | native or gsap adapter + one tick | `damping: null` on the conductor |
| nothing | `<skill>/assets/web/adapters/native.ts` | default |
| drei `ScrollControls` wanted | only on a full-screen 3D page with no other scroll | it owns a scroll container in front of the canvas |

**Same travel everywhere**: every adapter computes progress over `wrapperHeight - 100lvh` (shared `createLvhProbe`), the distance the `lvh` pin actually travels. Never `bottom bottom`, `['start start','end end']` or `innerHeight`: they follow the visual viewport and, with the iOS toolbar shown, hit 1 up to one toolbar height after the pin releases, holding the last frame while the scene scrolls away.

Every adapter returns `{ refresh, destroy }` (Motion: a hook) and calls `setExact` then `settle()` on mount. One authority per route; stamp it (`<html data-scroll-authority>`). Never two: no Lenis with ScrollSmoother, no `ScrollTrigger.normalizeScroll()` with Lenis, no CSS `scroll-behavior: smooth` with ScrollTrigger.

## Native and CSS

`native.ts`: `(scrollY - wrapperTop) / (wrapperHeight - lvh)` (the reference formula for all adapters), geometry cached, re-measured on `ResizeObserver`, `document.fonts.ready`, width change; re-derived on `pageshow`, `hashchange`, `focus`, visibility return. CSS `animation-timeline` (Chromium 115+, Safari 26+, not Firefox stable) only decorates the canvas (progress bar, label parallax); never drive camera or uniforms with it; under Lenis Safari reads the previous frame.

## Motion

`useMotionScrollConductor(conductor, wrapperRef)` reads `useScroll().scrollY` and applies the lvh travel above (a `useScroll` offset cannot express it). Rules:
- Measure the wrapper, never the sticky pin; geometry is cached and re-measured on resize, fonts, `pageshow`.
- Write per-frame values to the conductor, a ref or a uniform. Never bind a scroll value to `style` (measured on Motion 13.4, re-check on 14.x: it can hand off to a native timeline and drift back past the input range), never React state per frame, never a `useSpring` (the conductor smooths).
- Reduced motion: `bindReducedMotion(conductor)`; hand writers render the settled state.
- Under Lenis: run Lenis from Motion's `frame.setup` and dispatch a `scroll` event so `useScroll` reads the same frame; not from `frame.update` (one frame late).

## GSAP

`attachScrollTrigger(conductor, { wrapper })` creates `start: 'top top'`, `end: '+=' + (wrapperHeight - lvh)` (function end, `invalidateOnRefresh`) with no `scrub` and no `pin`. `driveFromGsapTicker(conductor, render)` is the one tick.
- A separate GSAP timeline for DOM copy under Lenis uses `scrub: true`; on native, `scrub: 0.3-1`. Never nest the scene in a GSAP `pin: true`.
- `ignoreMobileResize: true` (default here), create triggers in page order, `ScrollTrigger.refresh()` once after fonts and images settle, build in `useGSAP` with `scope` so Strict Mode and route hides revert them.
- ScrollSmoother: sticky and `view()` timelines break inside `#smooth-content`. Pin `[data-scene-pin]` in the page with a separate ScrollTrigger (`pinSpacing: false`, the content margin already cancels it); the adapter itself never pins. Create the smoother once per route.

## Lenis

```ts
const lenis = new Lenis({ autoRaf: false })        // ReactLenis defaults autoRaf true: set it false
gsap.ticker.add((t) => lenis.raf(t * 1000))        // register before driveFromGsapTicker
gsap.ticker.lagSmoothing(0)
lenis.on('scroll', ScrollTrigger.update)
```
Touch stays native; Safari caps it at 60 fps; `data-lenis-prevent` on nested scrollers; CSS scroll-snap does not work (use `lenis/snap`); `stop()` on modals. Native adapter works unchanged because Lenis moves the real scroll position.

## R3F render coupling

- Canvas that does not track DOM boxes: `frameloop="demand"`; `ConductorDriver` invalidates on input and until smooth settles.
- Canvas plane aligned to a DOM box under Lenis: `frameloop="never"` and `advance(timestamp)` from the GSAP ticker after Lenis (0 frames late; demand plus `invalidate()` measured one frame late on every other frame).

## drei ScrollControls

Only with no other scroll authority: `pages`, `damping` (default 0.25 s), `useScroll().offset` read in `useFrame` into `conductor.setExact` (use `damping: null` on the conductor; it already smooths). It breaks anchors, sticky, Lenis and the iOS pin on a page with flow.

## Pin rule when `scroll-animation` is absent

```html
<div data-scene-root>                       <!-- range wrapper: measured -->
  <div data-scene-pin>canvas</div>          <!-- position: sticky; top: 0; height: 100lvh; pointer-events: none -->
  <div data-scene-content>copy</div>        <!-- margin-top: -100lvh -->
</div>
```
- Pin `100lvh`, content margin `-100lvh` in the same unit. Never `svh` (page shows along the bottom), never `dvh` (re-lays out while the toolbar animates).
- No `transform` on the wrapper, pin or any ancestor; no `overflow: hidden` on an ancestor (use `clip`; one hidden axis makes the other `auto`); no `content-visibility: auto` in or around the runway.
- Wrapper height = copy height; add an empty spacer act to pace.

## iOS Safari

- Defer geometry reads one `requestAnimationFrame` on `resize`; ignore height-only resizes on touch (toolbar). `native.ts` does both.
- `overscroll-behavior: none` on the root of a scroll scene.
- iOS restores scroll after scripts run: re-derive from the wrapper on mount, `pageshow`, focus.
- A result from one iOS version is not verified on another; note the exact version tested.
- DevTools emulation cannot reproduce toolbar or compositing behaviour: verify on a real device, and confirm the deployed build contains the fix first.

## Traps

- Two authorities, or two smoothers (Lenis plus damping, Lenis plus `useSpring`).
- `@studio-freight/lenis` in new code: the package is `lenis`.
- Pin geometry from the sticky element instead of the wrapper.
- `framer-motion-3d` or `@theatre/r3f` for new scroll work: unmaintained.
