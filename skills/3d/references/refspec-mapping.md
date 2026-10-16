# Refspec to 3D Parameters

Purpose: Convert refspec fields into starting parameters for three.js and Blender, with the traps that make numbers lie.

Read when:
- A refspec or brief must become a camera, lights, tone mapping, materials or post stack.
- A render does not match its reference and you need to know which parameter to move first.

Skip when:
- Schema questions (→ [refspec](refspec.md)).
- Renderer API detail (→ [threejs-lookdev](threejs-lookdev.md), [threejs-postfx](threejs-postfx.md), [blender-lookdev-render](blender-lookdev-render.md)).

Inputs:
- `.3d/reference-spec.json` (ranges, confidence) and the target renderer.

Produces:
- Measured and derived values written to `.3d/reference-spec.json` and the brief. Colour and tone policy and starting light values are owned by [design-lookdev-presets](design-lookdev-presets.md) and recorded in `3D.md` from there; this file never writes `3D.md`.

## Contents

- Camera · Light · Colour and tone · Materials · Post · Medium · Traps

## Camera

Treat every value as a starting range; verify by rendering the shot and comparing ([shared-verification](shared-verification.md)).

- **FOV from mm**: the `shots.json` convention defines `focal_mm` by a **24 mm sensor height at every aspect**: vertical `fov = 2·atan(12 / f)`: 24 mm 53.1°, 35 mm 37.8°, 50 mm 27.0°, 85 mm 16.1°. A reference shot at 3:2 and used at 16:9 keeps its vertical FOV (the width crops).
- **three.js**: `PerspectiveCamera.fov` is vertical, degrees. Write `camera.fov = 2·atan(12/f)` directly. `setFocalLength` takes film height as `filmGauge / max(aspect, 1)`; if you use it, first set `camera.filmGauge = 24 * Math.max(camera.aspect, 1)` and redo that on every aspect change.
- **Same lens on a letterboxed target** (same horizontal view, different aspect): preserve horizontal FOV, `v = 2·atan(tan(h/2) / aspect)`. Otherwise preserve vertical.
- **Blender**: `cam.data.sensor_fit = 'VERTICAL'`, `sensor_height = 24`, `lens = f` (matches `shots.json`; `AUTO` with a 36 mm width gives a 20.25 mm height at 16:9 and a different framing); `lens_unit = 'FOV'` to enter FOV. DOF: `use_dof`, `dof.focus_object` or `focus_distance`, `aperture_fstop` (shallow low, deep high).
- **Distance from shot size**: `d ≈ subject_height / (2·tan(fov_v/2)·fill)`. Fill (subject height / frame height): EWS <0.05, WS 0.15-0.3, MWS 0.4-0.55, MS 0.6-0.75, MCU 0.8-0.9, CU ≥1.
- **Angle and height** place the camera on a sphere around the target: elevation low -10…-25°, eye 0…10°, high 25-45°, top-down 80-90°. Subject left of centre means the camera yaws toward the empty side.
- **Moves to keyframes**: push-in = dolly on the view axis (FOV change only when background scale changes uniformly and no parallax shows); orbit = azimuth over eased `t` around the target; truck/pedestal = translation perpendicular to view; crane = elevation plus translation with the target locked; handheld = noise on position (about 0.5% of frame) and roll (about 0.3°). Easing: the sampled curve first, a named ease second. For scroll, pose is a pure function of progress ([scroll-conductor](scroll-conductor.md)).
- Lens defaults by shot type live in [brief-spec](brief-spec.md); this file only converts. Orthographic (isometric, true iso: elevation 35.26°, azimuth 45°): size the frustum, not FOV.

## Light

| refspec | three.js | Blender |
|---|---|---|
| hard key, sun-like | `DirectionalLight`; shadow map, small bias, `shadow.radius` for softness | Sun; `angle` small = hard, large = soft |
| softbox, window | `RectAreaLight` (no shadows; init its uniforms lib for Standard/Physical) or a wide `SpotLight` with high `penumbra` | Area light; larger = softer |
| fill | dim `HemisphereLight`, env map, or a second dim light | world colour or a low area light |
| rim | `DirectionalLight` or `SpotLight` behind the subject | tight spot or area behind |
| practical, neon | emissive mesh plus a point light; bloom for glow | emission shader plus light |
| environment | `scene.environment` and `background` from an HDRI via `PMREMGenerator`; intensity with `scene.environmentIntensity` | World Environment Texture, strength |

- Since r155 three uses physical light units (point and spot intensity in candela). Intensities do not transfer to Blender watts: anchor on key:fill **stops** (`key = fill · 2^stops`) and tune by eye against the reference.
- `envMapIntensity` no longer affects `scene.environment` (r163); use `scene.environmentIntensity`. PBR look shifted in r181 and r186: never promise "the same HDRI looks identical" across versions.
- Colour temperature: warm 2700-3500 K, neutral 4500-6000 K, cool 7000+ K. Convert to RGB with Blender's Blackbody node, or a blackbody fit in code; check the result against the reference instead of trusting a lookup table. Brand-exact work uses measured hex over inferred K.
- Time of day: golden = sun elevation 5-15° with a warm key and cool sky fill; blue hour = no sun, environment only; noon = elevation 60-80°, hard top shadows; overcast = very large soft key, ratio ≤1 stop.

## Colour and tone

- Intent lives in [design-lookdev-presets](design-lookdev-presets.md) (D8). `grade.lut_family` none/product/brand-exact: Khronos PBR Neutral. Filmic/cinematic: AgX. Stylised/flat: no tone mapping plus a custom grade.
- **three.js**: `renderer.toneMapping` constants include `AgXToneMapping` and `NeutralToneMapping`; `outputColorSpace = SRGBColorSpace`; `toneMappingExposure` sets key brightness. R3F `<Canvas>` turns on ACES Filmic unless `flat` is set, so set it deliberately. Through an `EffectComposer`, tone mapping applies only via `OutputPass`/the tone-mapping effect.
- **Blender**: View Transform Standard (brand-exact, stylised), AgX, or Khronos PBR Neutral (product); list the available names at runtime instead of trusting memory ([blender-version-traps](blender-version-traps.md)). Exposure so the p50 of the scene sits near the reference's `luma p5/p50/p95`.
- **Albedo is de-lit**: material base colour is the sRGB hex of an unshaded region, converted to linear by the engine. Never paste the hex of a shaded pixel.

## Materials

| refspec | three `MeshPhysicalMaterial` | Blender Principled BSDF |
|---|---|---|
| base colour, roughness, metalness | `color`, `roughness`, `metalness` | Base Color, Roughness, Metallic |
| clearcoat | `clearcoat`, `clearcoatRoughness` | Coat Weight, Coat Roughness |
| transmission | `transmission`, `thickness`, `ior`, `attenuationColor`, `attenuationDistance` | Transmission Weight, IOR, volume absorption |
| sss | thin-transmission or `sheen` approximation; no true SSS | Subsurface Weight, Radius |
| brushed | `anisotropy`, `anisotropyRotation` | Anisotropic, Rotation |
| emissive | `emissive`, `emissiveIntensity` plus bloom | Emission Color, Strength |
| relief | normal or bump map, `normalScale` | Bump or Normal node |

Roughness buckets (the finest a reference can support): mirror 0-0.2, glossy 0.2-0.45, satin 0.45-0.7, matte 0.7-1. Metalness 0 or 1; intermediate only for dirt or oxide blends. Dielectric F0 is about 4%. Metals with no environment render black: always supply one.

## Post

Match each `fx` field to an effect, then take the exact class names from [threejs-postfx](threejs-postfx.md) (pmndrs `postprocessing` on WebGLRenderer, `RenderPipeline` nodes on WebGPU, never mixed). Order: bloom before tone mapping; grain, vignette, aberration after. Blender equivalents: Compositor Glare (bloom), Lens Distortion dispersion (CA), Ellipse Mask (vignette), camera DOF. Live budget per effect: [shared-performance](shared-performance.md).

## Medium

photoreal and cgi-real: PBR, HDRI, physical light, AgX or Neutral, subtle DOF/grain. stylised-3d: simplified roughness, few lights, saturated palette. toon: `MeshToonMaterial` with a 2-4 step gradient map, inverted-hull outline. clay: white diffuse, roughness about 0.8, soft key, AO. low-poly: flat shading, vertex colours, one directional plus hemisphere.

## Traps

- `setFocalLength` with the default `filmGauge` of 35 and no aspect correction: framing disagrees with the preview camera.
- Averaging two references' lenses or light directions.
- Reading light intensity across engines as comparable.
- Forgetting that R3F's default ACES shifts every colour you matched.
