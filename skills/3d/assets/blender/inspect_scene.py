#!/usr/bin/env python3
"""Inspect the loaded Blender scene and report web-export risks as JSON.

Runs only inside Blender (load the .blend before the script):

    blender -b scene.blend --factory-startup --python-exit-code 1 \
        --python assets/blender/inspect_scene.py -- --json .3d/evidence/scene.json

Args after `--`:  --json PATH   write the full report (default: stdout line only)
                  --help        show this text
Prints one JSON line `{"ok":..,"summary":{..},"warnings":[..]}` on stdout.
Exit 0 ok / 1 problems found (FAIL-level warnings) / 2 usage.
"""
from __future__ import annotations

import json
import sys

try:
    import bpy
    from mathutils import Vector
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("inspect_scene.py runs only inside Blender (see --help in the docstring)\n")
    sys.exit(2)

NON_EXPORTING_NODES = {
    "TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MUSGRAVE", "TEX_GRADIENT", "TEX_MAGIC",
    "TEX_CHECKER", "TEX_BRICK", "VALTORGB", "CURVE_RGB", "BUMP", "DISPLACEMENT",
}


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"json": None}
    i = 0
    while i < len(argv):
        if argv[i] == "--json" and i + 1 < len(argv):
            opts["json"] = argv[i + 1]
            i += 2
        else:
            sys.stderr.write(__doc__ + "\nunknown arg: %s\n" % argv[i])
            sys.exit(2)
    return opts


def material_report(mat) -> dict:
    info = {"name": mat.name, "principled": False, "nonexporting_nodes": [], "images": []}
    tree = mat.node_tree
    if tree is None:
        return info
    for node in tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            info["principled"] = True
        elif node.type == "TEX_IMAGE" and node.image:
            img = node.image
            info["images"].append({"name": img.name, "size": list(img.size),
                                   "colorspace": img.colorspace_settings.name,
                                   "packed": img.packed_file is not None,
                                   "path": img.filepath})
        elif node.type in NON_EXPORTING_NODES:
            info["nonexporting_nodes"].append(node.type)
    return info


def main() -> int:
    opts = parse_args()
    deps = bpy.context.evaluated_depsgraph_get()
    warnings: list[dict] = []
    objects = []
    total_tris = 0
    names = {}

    def warn(level, obj, msg):
        warnings.append({"level": level, "object": obj, "message": msg})

    for ob in bpy.context.scene.objects:
        rec = {"name": ob.name, "type": ob.type, "parent": ob.parent.name if ob.parent else None,
               "hidden_render": ob.hide_render,
               "modifiers": [{"name": m.name, "type": m.type} for m in ob.modifiers]}
        if ob.type in {"MESH", "CURVE", "SURFACE", "FONT"}:
            ev = ob.evaluated_get(deps)
            me = ev.to_mesh()
            try:
                me.calc_loop_triangles()
                tris = len(me.loop_triangles)
                rec.update(tris=tris, verts=len(me.vertices), uv_layers=len(me.uv_layers))
                total_tris += tris
            finally:
                ev.to_mesh_clear()
            corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            lo = [min(c[i] for c in corners) for i in range(3)]
            hi = [max(c[i] for c in corners) for i in range(3)]
            rec["bbox_world"] = {"min": [round(v, 4) for v in lo], "max": [round(v, 4) for v in hi],
                                 "size": [round(h - l, 4) for h, l in zip(hi, lo)]}
            rec["materials"] = [s.material.name for s in ob.material_slots if s.material]
            rec["shape_keys"] = bool(ob.type == "MESH" and ob.data.shape_keys)
            if any(abs(s - 1.0) > 1e-4 for s in ob.scale):
                warn("warn", ob.name, "unapplied scale %s" % [round(s, 4) for s in ob.scale])
            if any(s < 0 for s in ob.scale):
                warn("fail", ob.name, "negative scale")
            if ob.type == "MESH" and rec["uv_layers"] == 0 and any(
                    m for m in rec["materials"]):
                warn("warn", ob.name, "no UV map (fine for untextured materials only)")
            if rec["shape_keys"] and ob.modifiers:
                warn("warn", ob.name, "shape keys + modifiers: export_apply=True would drop the shape keys")
            if any(m.type == "NODES" for m in ob.modifiers):
                warn("warn", ob.name, "Geometry Nodes modifier: must be applied on an export copy")
        key = ob.name.replace(" ", "_").replace(".", "")
        names.setdefault(key, []).append(ob.name)
        objects.append(rec)

    for key, group in names.items():
        if len(group) > 1:
            warn("warn", ", ".join(group), "names collide after glTF sanitising (%s)" % key)

    materials = [material_report(m) for m in bpy.data.materials if m.users]
    for m in materials:
        if not m["principled"]:
            warn("warn", m["name"], "no Principled BSDF: exports as default material")
        if m["nonexporting_nodes"]:
            warn("warn", m["name"], "procedural/unsupported nodes %s: bake to textures"
                 % sorted(set(m["nonexporting_nodes"])))
        for img in m["images"]:
            if max(img["size"]) > 2048:
                warn("warn", m["name"], "texture %s is %dpx (web hero cap 2048)" % (img["name"], max(img["size"])))
            if not img["packed"] and img["size"][0] == 0:
                warn("fail", m["name"], "texture %s missing on disk" % img["name"])

    scene = bpy.context.scene
    summary = {
        "blender": bpy.app.version_string,
        "file": bpy.data.filepath,
        "objects": len(objects),
        "meshes": sum(1 for o in objects if "tris" in o),
        "tris": total_tris,
        "materials": len(materials),
        "actions": len(bpy.data.actions),
        "engine": scene.render.engine,
        "view_transform": scene.view_settings.view_transform,
        "unit_scale": scene.unit_settings.scale_length,
        "fps": scene.render.fps,
        "frame_range": [scene.frame_start, scene.frame_end],
    }
    report = {"ok": not any(w["level"] == "fail" for w in warnings), "summary": summary,
              "warnings": warnings, "objects": objects, "materials": materials}
    if opts["json"]:
        with open(opts["json"], "w") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps({"ok": report["ok"], "summary": summary, "warnings": warnings}))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    if code:
        sys.exit(code)
