# R3F in Next App Router

Purpose: Mount a React Three Fiber 9 scene in Next.js (App Router, React 19) without SSR errors, wasted GPU, or Strict Mode leaks.

Read when:
- Adding `<Canvas>` to a Next page, or the build fails with `ssr: false` / `window is not defined`.
- Canvas re-renders, double-mounts, burns GPU off-screen, or looks tone-mapped differently than expected.

Skip when:
- Vanilla three → [threejs-renderer](threejs-renderer.md).
- Scroll-driven camera/state → [scroll-conductor](scroll-conductor.md).

Inputs:
- `react`, `next`, `@react-three/fiber`, `@react-three/drei` versions from the lockfile.

Produces:
- A client-only scene module behind a lazy wrapper, paused when off-screen.

## Contents

- Stack · Boundary · Mount · Pause · Strict Mode and disposal · Canvas defaults · drei essentials · R3F 10 alpha

## Stack

R3F 9.8.x (`latest`) needs React `>=19 <19.4`; drei 10.7.x needs fiber `^9`; postprocessing wrapper 3.2 for WebGL. R3F 10 / drei 11 are alpha: never default (see end). Never upgrade React to fit a recipe.

## Boundary

1. Any file with `<Canvas>`, `useFrame`, `useThree`, drei, or `window` starts with `'use client'`.
2. `dynamic(() => import('./Scene'), { ssr: false })` is legal only inside a Client Component. In a Server Component (e.g. `app/page.tsx`) it fails the build. Put it in a `'use client'` wrapper; keep copy and SEO text in Server Components around it.
3. Never call `useThree`/`useFrame`/loader hooks in the component that renders `<Canvas>`; they belong in children.
4. `<Canvas>` parent needs a non-zero height. DOM UI lives outside, or in drei `Html`.

Copy-and-own block: `assets/web/r3f/SceneCanvas.tsx` (client wrapper, lazy mount, visibility pause). Prefer it over hand-rolling.

## Mount

- Mount the Canvas lazily: render the poster or static fallback first, mount when the section nears the viewport (`IntersectionObserver` with `rootMargin` ≈ one viewport) or after idle.
- Heavy scene = separate chunk; `loading` shows the poster, not a spinner.
- Reduced motion and no-WebGL: render the fallback image, never an empty box.

## Pause

- `frameloop="demand"` for scenes that can rest; call `invalidate()` after any imperative change and keep invalidating until an animation settles (9.8 also wakes a frame when an object is removed).
- Off-screen: flip `frameloop` to `"never"` (or `"demand"`) from an `IntersectionObserver`; flip back to `"always"` when visible. Also pause on `document.hidden`.
- A positive `useFrame` priority disables auto-render; its owner must render (relevant with composers).

## Strict Mode and disposal

- v9 inherits Strict Mode from outside the Canvas: remove any inner `<StrictMode>`.
- R3F disposes JSX-owned geometry/materials on unmount. `<primitive object>` and cached loader assets are not disposed; give them an owner. `dispose={null}` only for deliberately shared resources.
- Imperative resources made in effects (PMREM, render targets, controls) need cleanup returns; dev double-mount will expose leaks.
- Never `key`-flip a material family to switch looks: it disposes and recompiles everything in one frame (936 ms measured with ~24 transmission materials). Swap uniforms or toggle visibility.
- Allocate nothing per frame (`new Vector3()`), never `setState` in `useFrame`; mutate refs, use `delta`.

## Canvas defaults to override on purpose

`dpr=[1,2]`, ACES Filmic tone mapping ON (`flat` turns it off), sRGB output, antialias, default camera fov 75 at z=5. ACES makes scenes look desaturated against a glTF viewer: set `flat` or `gl={{ toneMapping: AgXToneMapping }}` deliberately; neither `flat` nor `linear` is a generic fix for washed assets. Policy: [design-lookdev-presets](design-lookdev-presets.md).
- `gl` receives constructor props, not a canvas: `gl={(props) => new WebGLRenderer(props)}`. For WebGPU on v9: async `gl` that awaits `init()` plus `extend(THREE)` from `three/webgpu`; drei and `@react-three/postprocessing` then do not work.
- `shadows` (true) selects deprecated `PCFSoftShadowMap`; use `shadows="percentage"` and verify console warnings.
- `dpr` prop overwrites `setDpr` on every re-render (9.8.2).

## drei essentials

- `useGLTF(url)` + module-scope `useGLTF.preload(url)`; decoders: [threejs-loading](threejs-loading.md).
- `Environment` (preset or file; `background` optional), `View` (many scenes, one Canvas), `PerformanceMonitor` + `AdaptiveDpr`, `Bvh` (picking cost), `Preload all`.
- `useThree((s) => s.camera)` selectors only; stable `args`.

## R3F 10 alpha (not default)

Needs three `>=0.185`. `<Canvas renderer>` opts into WebGPU; `state.gl` → `state.renderer`; `state.clock` removed (`{time, delta, elapsed}`); `useFrame` priority `>0` → `{ phase: 'render' }`; `onUpdate` removed; TSL hooks in `@react-three/tsl`. Mention only when the user asks; keep code on 9.x.
