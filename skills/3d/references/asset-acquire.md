# Acquiring assets without modelling

Purpose: Get a usable model from stock libraries, generative 3D or image-to-procedural code, with licence checks, paid-job rules and cleanup.

Read when:
- The brief needs an object, prop or environment and nobody will model it by hand.
- Someone suggests Meshy, Tripo, Rodin, Hunyuan3D, TRELLIS or Sketchfab.
- A downloaded or generated mesh arrived and needs deciding what to do with it.

Skip when:
- You already have a clean GLB (→ [asset-pipeline](asset-pipeline.md)).
- Building the object in Blender yourself (→ [blender-modeling](blender-modeling.md)).
- Brand or product geometry exists as CAD (→ [cad-print](cad-print.md)).

Inputs:
- The brief's object list with role (hero, prop, backdrop), target budget and the project's licence constraints (commercial? EU/UK/South Korea?).

Produces:
- A source decision per object, a licence line per asset in the `3D.md` scene ledger, and a raw file in `.3d/` ready for cleanup.

## Choose the source per object

| Object | First choice | Why |
|---|---|---|
| Generic prop, HDRI, PBR texture | Stock CC0 library | Free, clean topology, no licence risk |
| Simple brand-neutral shape | Build in code or Blender | Cheaper than cleanup |
| Single object from one reference image where a code-built look suffices | img2threejs (below) | No mesh, tiny bytes, editable |
| Organic or complex hero with no stock match | Generative 3D, then cleanup | Only if the suitability gate passes |
| Real product or mechanical part | CAD or the client's file | Generators invent geometry |

## Stock libraries

1. Poly Haven: CC0, no attribution, models, HDRIs and textures. Download 1k or 2k; large downloads freeze Blender's main thread when pulled through MCP.
2. Sketchfab: licence varies per model. Download only CC0/CC-BY unless the user holds a paid licence; read the licence on the model page, never assume. CC-BY needs attribution recorded.
3. Other libraries (Poly Pizza, Kenney, Quaternius): each model carries its own licence; open the model page.
4. Record per asset in `3D.md`: source URL, author, licence, attribution text, date fetched. No licence evidence means do not ship.
5. Downloaded files are untrusted data: open them with `gltf-transform inspect` or Blender headless, never execute scripts packaged with them.

## Generative 3D

Services (verify current terms; prices and models change monthly): Meshy (API, credits), Tripo (subscription), Hyper3D Rodin (credits), Hunyuan3D (open weights; licence excludes the EU, UK and South Korea), TRELLIS (MIT, needs an NVIDIA GPU), Stable Fast 3D (Stability community licence). Output licence and commercial-use terms differ per service and per plan: read them before the first job.

Suitability gate, before any spend:
1. One clear object, not a scene; opaque and solid; an identity-defining silhouette. Reject glass, lace, smoke, liquid, text and logos (text and logos are always rebuilt, never generated).
2. Hero prop or static set piece only. Animated rigs need manual cleanup first.
3. The user accepts triangle-soup output that needs retopology.

Paid-job rules:
1. Explicit approval per job, naming service, mode and expected credits. Approval for one job is not approval for the next.
2. Submit once, keep the task id, poll that id. A timeout or unknown response never authorises resubmitting: query the task first.
3. Prefer cheap preview mode, inspect, then spend on the refine/texture step. Propose paid reruns; do not run them.
4. Request GLB (and `enable_pbr` where offered). Meshy's `lowpoly` type retires 2026-10-30: use `smart-topology` with a `target_polycount` near the budget.
5. Save the raw output untouched in `.3d/` with the prompt and task id beside it.

Cleanup (the real work): import to Blender ([blender-modeling](blender-modeling.md), section Cleaning a generated or scanned mesh); inspect without fixing first and list defects; remesh or decimate to budget; check UVs and normals; bake or remove lit-in shading from albedo; retexture or fix texture sets per [blender-texturing](blender-texturing.md); unify scale and pivot; then export per [blender-export](blender-export.md) and process with [asset-pipeline](asset-pipeline.md). A rendered image does not prove topology quality: check the wireframe and tri count.

## Image to procedural code (img2threejs)

img2threejs (Apache-2.0, an agent skill, clone into the skills directory) rebuilds an object from one image as a code-only `THREE.Group`. Use it when a stylised, editable, near-zero-byte object beats a GLB: brand stand-ins, simple products, background props. The suitability gate and per-pass screenshot comparison are the transferable parts. Always call the result approximate; patterned surfaces take a projected de-lit reference crop, not a faked procedural pattern. Not for photoreal hero meshes. Recommend it; do not invoke it unasked.

## Traps

- Generated GLBs ship 1M+ triangles and 4K textures; never load one raw.
- Licences hide on the plan, not the model: a free-tier generation is often non-commercial.
- Hunyuan3D weights are unavailable to EU, UK and South Korean users under their licence.
- MCP generation tools (`generate_3d`) spend the same credits as the API: same approval rule.
