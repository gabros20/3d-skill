# CAD and 3D printing

Purpose: Route CAD and print work to the right owner and set the verification laws that stop plausible-looking geometry from passing.

Read when:
- The request involves a printable or mechanical part, STL/3MF/STEP, tolerances, a slicer or a printer.
- CAD geometry must appear in a web scene.

Skip when:
- The model is organic or visual only (→ [blender-modeling](blender-modeling.md)).
- Only the web asset path is needed (→ [asset-pipeline](asset-pipeline.md)).

Inputs:
- Real dimensions and tolerances, the printer/material if printing, and which CAD skills are installed.

Produces:
- A routing decision, verified geometry with stated checks, and a web GLB when needed.

## Route first

1. If the `manufacturing-workflow` skill is installed, recommend it for anything with slicing, printers, readiness review or artifact provenance. Do not invoke it automatically; it owns those stages and the physical-action gate. Without it, continue below and keep to the safety rules.
2. text-to-cad (MIT, `earthtojake/text-to-cad`, plugin or `npx skills add`) is the usual CAD generator: build123d Python, STEP primary, STL/3MF/GLB exports. Telemetry defaults on (`DO_NOT_TRACK=1` disables); tell the user before installing. Propose installs, never run them unasked.
3. Engines when writing code directly: build123d (Apache-2.0), CadQuery, OpenSCAD (CSG; use nightlies, last tagged release is 2021). `manifold-3d` for fast mesh booleans in Node or the browser.

## Verification laws

1. Dimensions come from the request or researched real-world measurements, held in one parameters block. 1-2 mm error ruins a part.
2. Verification is ground truth; renders are not evidence. Check dimensions, clearances and topology numerically (valid solid, volume, bounding box, wall thickness). A computation that failed is not a pass.
3. Never show or ship geometry that failed a check. Fix the geometry, never loosen the check.
4. Report units, thresholds and untested requirements in plain words.
5. Booleans: avoid coincident faces; overlap cuts about 0.5 mm; build cavities as subtracted blocks, not shell/thicken. Valid is necessary, not sufficient.
6. Look at the real artifact from several angles (about six views) and read every image before saying done.

## Physical actions

NEVER start, upload to, or control a printer. The user starts prints. Slicing settings need the printer model, firmware and filament; never invent them. Baseline PLA recipe to propose only: 0.2 mm layers, 2 walls, 15% infill. Slicers (OrcaSlicer, Bambu Studio) are AGPL GUI tools: CLI flags are unverified here.

## CAD to the web

1. Export STEP for the master and a mesh (GLB or STL) for display; STL carries no colour or units, so state units (metres for three).
2. If STL, import to Blender to name parts, set scale to metres and apply materials, then [blender-export](blender-export.md). If GLB, go straight to [asset-pipeline](asset-pipeline.md).
3. Tessellated CAD is dense: weld, then decimate or simplify to the hero budget; keep one node per movable part and `--keep-leaves true`.
4. Use the pipeline's `inspect` to confirm the bounding box equals the CAD dimensions.

## Traps

- A pretty render of a non-manifold part is the classic false pass.
- `manufacturing-workflow` references a `cad-viewer` skill that text-to-cad has retired; if the route is missing, say so.
- STL to three at millimetre units appears 1000x too large.
