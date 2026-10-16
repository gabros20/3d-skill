#!/usr/bin/env python3
"""Check UV layouts of the loaded Blender scene: overlaps, bounds, density, margin.

Runs only inside Blender (load the .blend before the script):

    blender -b scene.blend --factory-startup --python-exit-code 1 \
        --python <skill>/assets/blender/uv_check.py -- --res 2048 --json .3d/evidence/uv.json

Args after `--` (all optional):
  --objects A,B        mesh objects to check (default: every mesh in the scene)
  --res N              texture size in px used for density and margin (default 2048)
  --layer NAME         UV layer to check (default: the active render layer)
  --lightmap           also require a second UV layer, free of overlaps and out-of-bounds
  --target PX_PER_M    expected texel density; WARN when an object differs by > --tolerance
  --tolerance F        relative tolerance for --target (default 0.25)
  --max-spread F       FAIL when object densities differ by more than this ratio (default 1.3)
  --min-coverage F     WARN below this share of the 0-1 square used (default 0.55)
  --min-margin PX      WARN when islands sit closer than this at --res (default 4)
  --json PATH          write the full report to PATH
Prints one JSON line {"ok":..,"items":[{"level","object","check","message"}],"objects":[..]}.
Levels PASS / WARN / FAIL. Exit 0 no FAIL / 1 any FAIL / 2 usage or not inside Blender.
Overlap is measured between UV islands (rasterised at 1024); a fold inside one island is not counted.
Modifiers are ignored: the base mesh is checked.
"""
from __future__ import annotations

import json
import os
import sys

try:
    import bpy
    import numpy as np
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("uv_check.py runs only inside Blender (see --help in the docstring)\n")
    sys.exit(2)

RASTER = 1024
OVERLAP_PX = 8  # pixels doubly covered before we call it an overlap (edge noise)


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"objects": None, "res": 2048, "layer": None, "lightmap": False, "target": None,
            "tolerance": 0.25, "max_spread": 1.3, "min_coverage": 0.55, "min_margin": 4.0,
            "json": None}
    kinds = {"objects": str, "res": int, "layer": str, "target": float, "tolerance": float,
             "max_spread": float, "min_coverage": float, "min_margin": float, "json": str}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        key = a[2:].replace("-", "_")
        if a == "--lightmap":
            opts["lightmap"] = True
            i += 1
        elif a.startswith("--") and key in kinds and i + 1 < len(argv):
            try:
                opts[key] = kinds[key](argv[i + 1])
            except ValueError:
                sys.stderr.write(__doc__ + "\nbad value for %s\n" % a)
                sys.exit(2)
            i += 2
        else:
            sys.stderr.write(__doc__ + "\nunknown arg: %s\n" % a)
            sys.exit(2)
    return opts


def islands(mesh, uv) -> "np.ndarray":
    """Island id per loop: faces joined when they share an edge with equal UVs at both ends."""
    n_poly = len(mesh.polygons)
    parent = list(range(n_poly))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edge_map: dict = {}
    for p in mesh.polygons:
        n = p.loop_total
        for k in range(n):
            la, lb = p.loop_start + k, p.loop_start + (k + 1) % n
            va, vb = mesh.loops[la].vertex_index, mesh.loops[lb].vertex_index
            ua = (round(uv[la][0], 4), round(uv[la][1], 4))
            ub = (round(uv[lb][0], 4), round(uv[lb][1], 4))
            key = (va, ua, vb, ub) if va < vb else (vb, ub, va, ua)
            if key in edge_map:
                ra, rb = find(edge_map[key]), find(p.index)
                if ra != rb:
                    parent[ra] = rb
            else:
                edge_map[key] = p.index
    return np.array([find(i) for i in range(n_poly)])


def raster_tri(tri_uv):
    """Pixel-centre coverage of one triangle: (x0, y0, bool mask) or None."""
    px = tri_uv * RASTER
    x0, y0 = np.floor(px.min(axis=0)).astype(int)
    x1, y1 = np.ceil(px.max(axis=0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, RASTER - 1), min(y1, RASTER - 1)
    if x1 < x0 or y1 < y0:
        return None
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    (ax, ay), (bx, by), (cx, cy) = px
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-12:
        return None
    w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
    w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
    w2 = 1.0 - w0 - w1
    inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    return x0, y0, inside


def analyse(ob, layer_name, res):
    mesh = ob.data
    mesh.calc_loop_triangles()
    uvl = mesh.uv_layers.get(layer_name)
    n_loops = len(mesh.loops)
    uv = np.empty(n_loops * 2, dtype=np.float64)
    uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    iso = islands(mesh, uv)
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    mw = np.array(ob.matrix_world)
    wco = co.reshape(-1, 3) @ mw[:3, :3].T
    label = np.zeros((RASTER, RASTER), dtype=np.int32)  # island id + 1, last wins
    owner = np.zeros((RASTER, RASTER), dtype=np.int32)
    overlap = np.zeros((RASTER, RASTER), dtype=bool)
    ids = {int(v): k + 1 for k, v in enumerate(sorted(set(iso.tolist())))}
    per_island: dict = {}
    zero_area = 0
    oob = False
    for t in mesh.loop_triangles:
        loops = list(t.loops)
        tri = uv[loops]
        if tri.min() < -1e-4 or tri.max() > 1 + 1e-4:
            oob = True
        d1, d2 = tri[1] - tri[0], tri[2] - tri[0]
        uv_area = abs(d1[0] * d2[1] - d1[1] * d2[0]) / 2
        w = wco[list(t.vertices)]
        w_area = np.linalg.norm(np.cross(w[1] - w[0], w[2] - w[0])) / 2
        if uv_area < 1e-10 or w_area < 1e-12:
            zero_area += 1
        else:
            per_island.setdefault(int(iso[t.polygon_index]), []).append(
                (res * (uv_area / w_area) ** 0.5, w_area))
        r = raster_tri(tri)
        if r is None:
            continue
        x0, y0, inside = r
        h, wd = inside.shape
        iid = ids[int(iso[t.polygon_index])]
        sl = (slice(y0, y0 + h), slice(x0, x0 + wd))
        own = owner[sl]
        hit = inside & (own != 0) & (own != iid)
        overlap[sl] |= hit
        own[inside] = iid
        label[sl][inside] = iid
    filled = int((label > 0).sum())
    coverage = filled / float(RASTER * RASTER)
    n_overlap = int(overlap.sum())
    # margin: smallest Chebyshev gap between different islands, probed up to k px
    k = max(1, int(round(RASTER / float(res) * 8)))
    min_gap = None
    for gap in range(1, k + 1):
        tight = False
        for dx, dy in ((gap, 0), (0, gap), (gap, gap), (gap, -gap)):
            a = label[max(0, dy):RASTER + min(0, dy), max(0, dx):RASTER + min(0, dx)]
            b = label[max(0, -dy):RASTER + min(0, -dy), max(0, -dx):RASTER + min(0, -dx)]
            if ((a != b) & (a > 0) & (b > 0)).any():
                tight = True
                break
        if tight:
            min_gap = gap
            break
    margin_px = None if min_gap is None else min_gap * res / float(RASTER)
    dens = {}
    for isl, vals in per_island.items():
        arr = np.array(vals)
        dens[isl] = float(np.median(arr[:, 0]))
    all_d = np.array([v for vals in per_island.values() for v, _ in vals]) if per_island else np.array([])
    median_d = float(np.median(all_d)) if all_d.size else 0.0
    return {"layer": layer_name, "islands": len(ids), "overlap_px": n_overlap,
            "out_of_bounds": oob, "coverage": round(coverage, 3), "zero_area_faces": zero_area,
            "density_px_m": round(median_d, 2),
            "island_spread": round(max(dens.values()) / min(dens.values()), 3) if len(dens) > 1 and min(dens.values()) > 0 else 1.0,
            "margin_px": None if margin_px is None else round(margin_px, 2)}


def main() -> int:
    opts = parse_args()
    items: list = []
    out_objects: list = []

    def add(level, obj, check, msg):
        items.append({"level": level, "object": obj, "check": check, "message": msg})

    names = set(opts["objects"].split(",")) if opts["objects"] else None
    meshes = [o for o in bpy.context.scene.objects
              if o.type == "MESH" and (names is None or o.name in names)]
    if names:
        for missing in sorted(names - {o.name for o in meshes}):
            add("FAIL", missing, "object", "not found or not a mesh")
    if not meshes and not items:
        add("FAIL", "-", "object", "no mesh objects to check")
    densities = {}
    for ob in meshes:
        layers = ob.data.uv_layers
        if not len(layers):
            add("FAIL", ob.name, "uv-map", "no UV map")
            continue
        layer_names = [opts["layer"]] if opts["layer"] else [layers.active_render.name if layers.active_render else layers[0].name]
        if opts["layer"] and opts["layer"] not in layers:
            add("FAIL", ob.name, "uv-map", "layer %r missing" % opts["layer"])
            continue
        if opts["lightmap"]:
            if len(layers) < 2:
                add("FAIL", ob.name, "lightmap-uv", "needs a second UV layer for lightmaps")
            else:
                other = [l.name for l in layers if l.name != layer_names[0]][0]
                layer_names.append(other)
        for idx, lname in enumerate(layer_names):
            r = analyse(ob, lname, opts["res"])
            r["object"] = ob.name
            out_objects.append(r)
            tag = ob.name if idx == 0 else "%s [%s]" % (ob.name, lname)
            strict = idx > 0  # the lightmap layer must be clean, the albedo layer may tile/mirror
            if r["overlap_px"] > OVERLAP_PX:
                add("FAIL", tag, "overlap",
                    "%d px of UV islands overlap" % r["overlap_px"])
            else:
                add("PASS", tag, "overlap", "no overlapping islands")
            if r["out_of_bounds"]:
                add("FAIL" if strict else "WARN", tag, "bounds", "UVs outside 0-1 (UDIM or tiling?)")
            else:
                add("PASS", tag, "bounds", "inside 0-1")
            if r["zero_area_faces"]:
                add("WARN", tag, "zero-area", "%d zero-area faces/triangles" % r["zero_area_faces"])
            if r["coverage"] < opts["min_coverage"]:
                add("WARN", tag, "coverage", "uses %.0f%% of 0-1 (< %.0f%%)" % (r["coverage"] * 100, opts["min_coverage"] * 100))
            if r["margin_px"] is not None and r["margin_px"] < opts["min_margin"]:
                add("WARN", tag, "margin", "islands %.1f px apart at %d px (< %g)" % (r["margin_px"], opts["res"], opts["min_margin"]))
            if r["island_spread"] > opts["max_spread"]:
                add("WARN", tag, "island-density", "island density spread x%.2f" % r["island_spread"])
            if idx == 0:
                densities[ob.name] = r["density_px_m"]
    vals = [v for v in densities.values() if v > 0]
    if len(vals) > 1:
        spread = max(vals) / min(vals)
        add("FAIL" if spread > opts["max_spread"] else "PASS", "*", "density-spread",
            "object texel density spread x%.2f (max %g)" % (spread, opts["max_spread"]))
    if opts["target"]:
        for name, d in densities.items():
            if d > 0 and abs(d - opts["target"]) / opts["target"] > opts["tolerance"]:
                add("WARN", name, "target-density", "%.0f px/m vs target %g" % (d, opts["target"]))
    ok = not any(i["level"] == "FAIL" for i in items)
    report = {"ok": ok, "res": opts["res"], "items": items, "objects": out_objects}
    if opts["json"]:
        os.makedirs(os.path.dirname(os.path.abspath(opts["json"])), exist_ok=True)
        with open(opts["json"], "w") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
