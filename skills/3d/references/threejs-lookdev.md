# three.js Lookdev Implementation

Purpose: Implement lighting, materials, environment and shadows in three r186 so a scene reads as designed, with the colour policy applied once.

Read when:
- Metals render black, scene is flat/washed, shadows acne or float, or you are building a lighting rig.
- Translating a lookdev preset or Blender look into three.

Skip when:
- Choosing the look, presets, tone-mapping policy → [design-lookdev-presets](design-lookdev-presets.md).
- Blender-side lookdev → [blender-lookdev-render](blender-lookdev-render.md).

Inputs:
- Chosen preset/tone mapping, hero asset loaded, target tier ([shared-performance](shared-performance.md)).

Produces:
- Environment, 1–3 lights, material roles, shadow settings with measured cost.

## Procedure

1. Fix the colour pipeline first ([threejs-renderer](threejs-renderer.md) Colour): output colour space, tone mapping, exposure. Settle exposure and tone curve against the reference's luma percentiles (see [intake-references](intake-references.md)) BEFORE tuning materials; never patch the tone curve later with offsets. Judge materials only after.
2. Environment: PBR needs `scene.environment`; metals without it render black and more ambient light does not fix that.
   - Prototype: `new PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture` (`three/addons/environments/RoomEnvironment.js`).
   - Production: `HDRLoader` (`three/addons/loaders/HDRLoader.js`) → `texture.mapping = EquirectangularReflectionMapping`; or drei `Environment`. Dispose the PMREM generator after use.
   - Metals need a contrasty environment to read as polished (T1, ranking in [realism-toolbox](realism-toolbox.md)): dark surround plus bright strips. Build it from emitters: a `Scene` of dark walls plus emissive strip meshes (emitter intensity 10–50) through `PMREMGenerator.fromScene(scene, 0.02)`, or drei `<Environment frames={1} resolution={256}><Lightformer form="rect" intensity={…} scale={…} position={…} /></Environment>`. A flat bright HDRI gives matte metal. One environment per metal look; a second look needs its own env, not a bigger intensity.
   - Intensity: `scene.environmentIntensity` (not `envMapIntensity`, which affects only a material's own `envMap`). Rotation: `scene.environmentRotation` / `backgroundRotation`; semantics changed r184.
3. Direct lights: one key (directional or spot) for direction and shadow, optional rim. Units are physical: Point/Spot intensity in candela, so values are about π × pre-r155 numbers. Tune by exposure, not by stacking lights.
4. Materials by role: `MeshStandardMaterial` default; `MeshPhysicalMaterial` only for clearcoat, transmission, sheen, iridescence. Share materials per role; `clone()` before per-instance edits (glTF materials are cached and shared).
5. Textures: `colorSpace` per [threejs-renderer](threejs-renderer.md); AO/light maps use `texture.channel = 1` for `uv1`; `anisotropy` 4–8 on large floors.
6. Shadows (budget in [shared-performance](shared-performance.md)):
   - `renderer.shadowMap.enabled = true; type = PCFShadowMap` (or `VSMShadowMap`; VSM makes every receiver also cast). `PCFSoftShadowMap` is deprecated (r186).
   - Tighten the shadow camera (`left/right/top/bottom/near/far`) before raising `mapSize`. Tune `bias` (≈ -0.0005) and `normalBias` (≈ 0.02) to kill acne and floating.
   - Add `light.target` to the scene or its matrix never updates. Inspect with `CameraHelper`.
   - Static scene: `renderer.shadowMap.autoUpdate = false`, set `needsUpdate = true` on change. Largest cheap win.
   - Never point-light shadows on mobile (six renders each).
7. Keep a no-post baseline that still reads: lock silhouette, material separation, key/fill/rim before adding fog, bloom or grade. No fog or glow volumes that hide geometry to fake depth ([threejs-postfx](threejs-postfx.md)).

## Tunables in one object

Keep every tunable (exposure, env intensity, light intensities, colours, roughness) in one `P` params object the scene reads each frame; `?p=` and the bridge `setParams` write it, and an optional lil-gui panel edits it live. Tune by changing `P` (via `preview sweep`), never by regex-editing scene code.

```ts
import { readParams } from '<skill>/assets/web/bridge'; // merges ?p= over defaults; window.__3d.setParams/getParams
export const P = readParams({ exposure: 1, envIntensity: 1, keyIntensity: 3 });
// each frame: renderer.toneMappingExposure = P.exposure; scene.environmentIntensity = P.envIntensity;
```

## Realism recipes

Ranking and gains: [realism-toolbox](realism-toolbox.md). Recipes live here.

- Area strips (T8): `RectAreaLight` (no shadows; Standard/Physical only) as long strips beside the subject. WebGL: call `RectAreaLightUniformsLib.init()` once (`three/addons/lights/RectAreaLightUniformsLib.js`). WebGPU: `RectAreaLightNode.setLTC(RectAreaLightTexturesLib.init())`. Pair with T1 for the highlight shape; they do not cast shadows, so add one directional shadow caster.
- Brushed metal (T3): `MeshPhysicalMaterial` `anisotropy` (0–1) with `anisotropyRotation` or `anisotropyMap`, plus a grain roughness map; vary `roughness` ±0.05 and tilt per instance so repeated parts do not read as clones.
- Reflection probe (T5): `CubeCamera` placed at the object, hide the object, `update()` once (or every N frames), assign `cubeRenderTarget.texture` to `material.envMap`. Cost 1–3 ms per update [U].
- Shadows (T6): drei `ContactShadows` for grounding, `AccumulativeShadows` + `RandomizedLight` for static soft shadows (`frames` 40–100, `temporal` off for stills), `SoftShadows` is a global shader patch.
- Baked maps (T4): `lightMap` with `texture.channel = 1`, `lightMapIntensity`; lightmap colour space sRGB, AO map linear data. A lightMap is multiplied by the diffuse contribution, so it has no visible effect at `metalness` 1: bake diffuse only and let metal read the env/probe. Bake recipe in [blender-uv-bake](blender-uv-bake.md). Output Combined with Background-vs-Emission set so lights are not applied twice. GLTFLoader maps occlusion to `aoMap` only; assign `lightMap` in code.

## Cost notes

- Transmission renders the scene again into a buffer: one or two transmissive hero meshes, never dozens. Keep `opacity = 1`, use `transmission`, `thickness`, `ior`; lower `renderer.transmissionResolutionScale` (WebGL, default 1) to ~0.5 on mobile.
- Clearcoat adds a second specular lobe; fine on a hero, avoid scene-wide.
- `DoubleSide` everywhere hides winding bugs and costs fill; fix normals instead.
- Fog interacts with custom shaders only if they include fog chunks.

## Traps

- Tone-mapping defaults differ (R3F vs three): confirm which is active; see [design-lookdev-presets](design-lookdev-presets.md).
- Hex colour → `Color` converts to linear; raw uniform vectors are already linear. Do not convert twice.
- Look drift across r181/r185/r186 PMREM changes: re-tune after upgrading.
