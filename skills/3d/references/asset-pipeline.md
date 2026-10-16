# Asset pipeline

Purpose: The one canonical path from an authored or acquired model to a validated, budgeted GLB that three.js or R3F can load.

Read when:
- A GLB/glTF exists (exported, downloaded or generated) and must ship to the web.
- A GLB is too big, slow, washed out or has lost its node/material names after processing.
- You are about to type `gltf-transform`, `gltfpack`, `ktx` or `gltfjsx`.

Skip when:
- Still modelling or exporting from Blender (→ [blender-export](blender-export.md)).
- Wiring decoders and loaders at runtime (→ [threejs-loading](threejs-loading.md)).
- Deciding what the budgets are (→ [shared-performance](shared-performance.md)).
- You have no model yet (→ [asset-acquire](asset-acquire.md)).

Inputs:
- An uncompressed master GLB, the target (hero, world, AR) and the budget recorded in `3D.md`.

Produces:
- `<name>.glb` (optimised, validated), `<name>-master.glb` kept untouched, a before/after size line, optional `<Name>.tsx` from gltfjsx.

## Rules

- ALWAYS keep the uncompressed master. Compress once, from the master, into a new file. Never recompress a compressed file.
- NEVER run bare `gltf-transform optimize`. Its defaults (4.5.1, read via `help optimize`) are lossy: `--simplify`, `--join`, `--flatten`, `--palette` and `--texture-size 2048` are all on. Join and flatten delete the node names and pivots that code animates; palette merges materials the runtime looks up by name; simplify changes silhouettes.
- Pin the CLI (`npm i -D @gltf-transform/cli@4.5`) and confirm flags with `gltf-transform help <command>`; they drift between versions.
- meshopt is the default geometry compression; Draco only for large static, geometry-dominant meshes where the decoder cost is accepted. Never both.

## Steps

1. Inspect the master: `gltf-transform inspect master.glb` and `<skill>/scripts/glb-report master.glb --budget hero`. Read which axis is heavy: geometry, textures or draw calls. Check real-world scale here (1 unit = 1 m) before any AR use.
2. Structural passes, one file per step or a chained shell run, always writing a new file:
   ```
   gltf-transform dedup master.glb a.glb
   gltf-transform weld a.glb b.glb
   gltf-transform prune b.glb c.glb --keep-leaves true
   ```
   `--keep-leaves true` keeps empty pivot nodes that code drives. `weld` is required before any simplify.
3. Textures, only as far as the budget demands. Resize to the `3D.md` texture budget (D6: 1024 default, 2048 close-up hero):
   ```
   gltf-transform resize c.glb d.glb --width 2048 --height 2048
   ```
   Then one of two options. Option A, WebP (download size; decodes to full RGBA8 in VRAM):
   ```
   gltf-transform webp d.glb f.glb --quality 85 --slots "{baseColor,emissive}*"
   ```
   Option B, KTX2 (cuts VRAM; use when VRAM or many textures matter):
   ```
   gltf-transform etc1s d.glb e.glb --slots "{baseColor,emissive}*"
   gltf-transform uastc e.glb f.glb --slots "normal*" --level 2
   ```
   Only `resize` or KTX2 reduces VRAM.
   `--slots` takes a glob over slot names; check the textures actually changed in `inspect`. There is no `ktx2` command. Both shell out to `ktx` from KTX-Software ≥ 4.4 (not `toktx`); `ktx --version` first. If `ktx` is missing, propose the install (shared-preflight) or fall back to `webp`.
4. Geometry compression, last: `gltf-transform meshopt f.glb out.glb --level high` (or `draco`). Meshopt output requires `KHR_mesh_quantization` plus `EXT_meshopt_compression`, so the loader needs `MeshoptDecoder`.
5. Optional one-liner, only with the lossy passes explicitly off. `optimize` always runs prune with `keepLeaves: false`, so disable it and run the discrete `prune --keep-leaves true` from step 2 first:
   ```
   gltf-transform optimize c.glb out.glb --prune false --simplify false --join false --flatten false --palette false --instance false --compress meshopt --texture-compress webp --texture-size 2048
   ```
   `--instance false` is required when parts are code-addressed. Confirm each flag with `help optimize` first.
6. Validate: `gltf-transform validate out.glb` (runs the Khronos validator; errors fail the step) then `<skill>/scripts/glb-report out.glb --budget hero`. Inspect again; compare node names and material names against the master.
7. Judge by eye: load `out.glb` in a bare scene and compare hero view and one close-up against the master at target DPR. Normal maps that look blocky or albedo that bands means raise quality or leave that slot uncompressed.
8. R3F component (optional): `npx gltfjsx out.glb --types --keepnames`. Skip `--transform` (it re-runs its own pipeline, defaults to 1024 px textures, and writes `*-transformed.glb`). gltfjsx last released 2024-11: check the generated file against R3F 9 types and replace any `useGLTF` Draco path assumptions per [threejs-loading](threejs-loading.md).
9. Pixel-parity gate. Capture the same shots from the master and from `out.glb` (`<skill>/scripts/preview capture`, same camera, DPR and shots file, one version each), then `<skill>/scripts/preview diff A B`. Lossless-intended passes (dedup, weld, prune, meshopt, instance) FAIL when ssim < 0.99 or more than 0.5% of pixels changed: find the pass that changed the look and redo from the master. Lossy texture passes (resize, WebP, KTX2, simplify) are judged visually against the brief; record the diff numbers. Headless GL may be unavailable: say so rather than passing (→ [shared-verification](shared-verification.md)).
10. Budget check: compare the `glb-report` verdict to the budgets in `3D.md` ([shared-performance](shared-performance.md)). Record before/after bytes in the `3D.md` version log.

## gltfpack (alternative)

Use when `gltf-transform` cannot be installed or you want one fast pass. Prefer the native binary from the meshoptimizer releases; the npm build lacks texture compression.
```
gltfpack -i master.glb -o out.glb -c -kn -km
```
(flags checked with `gltfpack -h`, v1.3.) gltfpack merges meshes and materials by default: `-kn -km` keep named nodes and materials, so check names after. `-c` meshopt, `-cc` smaller (needs gzip serving), `-tc` ETC1S KTX2 and `-tu` UASTC (class form `-tc color -tu normal`, full build only), `-tq N` quality, `-tl N` max texture size, `-si R` simplify (lossy, off by default). Quantised output needs `MeshoptDecoder` at runtime. Do not chain gltfpack and gltf-transform on one asset.

## Traps

- Keep the master anyway: quantised and compressed output is lossy and not meant for re-editing. Blender 5.2 can import meshopt; earlier versions may not (introspect).
- `instance` is skipped when the file has animation; do not rely on it.
- Quantised positions are Int16 plus a node matrix: dequantise before transforming geometry in place.
- WebP and KTX2 slots matter: colour slots sRGB, normal/ORM linear. Wrong slots show as a hue or lighting shift.
- Material or node names that vanish after a pass mean a lossy pass ran: redo from the master.
