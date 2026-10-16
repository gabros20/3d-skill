#!/usr/bin/env python3
"""Export the loaded scene to an uncompressed GLB for the web, on a throwaway session.

Runs only inside Blender; never save the .blend afterwards (modifiers get applied):

    blender -b scene.blend --factory-startup --python-exit-code 1 \
        --python <skill>/assets/blender/export_web.py -- --out .3d/versions/v001/hero.glb

Args after `--`:
  --out FILE            required, .glb path
  --apply auto|none|all auto (default): apply shape-defining modifiers (Geometry Nodes,
                        Boolean, Bevel, Mirror, Solidify, Subsurf, Weighted Normal, Decimate,
                        Remesh, Weld, Triangulate, Edge Split, Screw); keep Array/Armature. none: apply nothing.
                        all: apply every non-armature modifier. Meshes with shape keys are
                        never applied (shape keys would be lost) and are reported.
  --root NAME           export only this object and its descendants
  --images auto|webp|jpeg  texture format (default auto = PNG/JPEG as authored)
  --no-lights / --no-cameras  leave them out (default: both exported; punctual lights are
                        written as KHR_lights_punctual and marked required)
  --lighting compat|spec|raw  light unit conversion (default compat: W/4pi, right for
                        HDR-lit web scenes; spec turns 1000 W into 54,351 cd and blows out)
  --gn-instances        keep Geometry Nodes modifiers unapplied so instances export as
                        EXT_mesh_gpu_instancing; instance source objects are hidden and
                        excluded. Default applies GN (realised mesh).
  --cull-backfaces      set backface culling on every material (the exporter writes
                        doubleSided=true otherwise); closed meshes only
  --extras              write custom properties (default on) / --no-extras
Compression is NOT done here (see references/asset-pipeline.md). Prints Blender's own log lines, then one JSON line (the line starting with `{`):
{"ok","out","bytes","applied","skipped","warnings","dropped_kwargs","glb":{...}}.
Exit 0 ok / 1 export failed / 2 usage.
"""
from __future__ import annotations

import json
import os
import struct
import sys

try:
    import bpy
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("export_web.py runs only inside Blender (see docstring)\n")
    sys.exit(2)

SHAPE_MODS = {"NODES", "BOOLEAN", "BEVEL", "MIRROR", "SOLIDIFY", "SUBSURF", "WEIGHTED_NORMAL",
              "DECIMATE", "REMESH", "WELD", "TRIANGULATE", "EDGE_SPLIT", "SCREW"}


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"out": None, "apply": "auto", "root": None, "images": "auto",
         "lights": True, "cameras": True, "extras": True, "lighting": "compat", "gn_instances": False,
         "cull": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--out", "--apply", "--root", "--images") and i + 1 < len(argv):
            o[a[2:]] = argv[i + 1]
            i += 2
        elif a in ("--no-lights", "--no-cameras"):
            o[a[5:]] = False
            i += 1
        elif a == "--lighting" and i + 1 < len(argv):
            o["lighting"] = argv[i + 1].lower()
            i += 2
        elif a == "--gn-instances":
            o["gn_instances"] = True
            i += 1
        elif a == "--cull-backfaces":
            o["cull"] = True
            i += 1
        elif a in ("--extras", "--no-extras"):
            o["extras"] = a == "--extras"
            i += 1
        else:
            sys.stderr.write(__doc__ + "\nunknown arg: %s\n" % a)
            sys.exit(2)
    if not o["out"] or o["apply"] not in ("auto", "none", "all") or \
            o["images"] not in ("auto", "webp", "jpeg") or o["lighting"] not in ("compat", "spec", "raw"):
        sys.stderr.write(__doc__)
        sys.exit(2)
    return o


def collect(root_name):
    if not root_name:
        return list(bpy.context.scene.objects)
    root = bpy.data.objects.get(root_name)
    if root is None:
        sys.stderr.write("no object named %r\n" % root_name)
        sys.exit(2)
    return [root] + list(root.children_recursive)


def gn_instance_sources(objs):
    """Objects fed into Geometry Nodes through Object Info nodes (instancing sources)."""
    sources = set()
    for ob in objs:
        for mod in ob.modifiers:
            if mod.type != "NODES" or mod.node_group is None:
                continue
            for node in mod.node_group.nodes:
                if node.bl_idname == "GeometryNodeObjectInfo" and node.inputs[0].default_value:
                    sources.add(node.inputs[0].default_value)
    return sources


def material_warnings():
    """Materials using volume / thin film need a 'glTF Material Output' group to export them."""
    out = []
    for mat in bpy.data.materials:
        tree = mat.node_tree if mat.users else None
        if tree is None:
            continue
        has_group = any(n.type == "GROUP" and n.node_tree and n.node_tree.name.startswith("glTF Material Output")
                        for n in tree.nodes)
        needs = []
        for n in tree.nodes:
            if n.type == "OUTPUT_MATERIAL" and n.inputs["Volume"].is_linked:
                needs.append("volume")
            if n.type == "BSDF_PRINCIPLED" and "Thin Film Thickness" in n.inputs and \
                    n.inputs["Thin Film Thickness"].default_value > 0:
                needs.append("thin film (iridescence)")
        if needs and not has_group:
            out.append("material %r uses %s but has no 'glTF Material Output' node group: "
                       "volume/thickness/dispersion/iridescence will not export" % (mat.name, ", ".join(needs)))
    return out


def apply_modifiers(objs, mode, keep_gn=False):
    applied, skipped = [], []
    if mode == "none":
        return applied, skipped
    for ob in objs:
        if ob.type != "MESH" or not ob.modifiers:
            continue
        if ob.data.shape_keys:
            skipped.append({"object": ob.name, "reason": "shape keys"})
            continue
        if ob.data.users > 1:
            skipped.append({"object": ob.name, "reason": "linked duplicate: left unapplied to keep instances"})
            continue
        for mod in list(ob.modifiers):
            if mod.type == "ARMATURE" or (keep_gn and mod.type == "NODES"):
                continue
            if mode == "auto" and mod.type not in SHAPE_MODS:
                continue
            mname = mod.name
            with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
                try:
                    bpy.ops.object.modifier_apply(modifier=mname)
                    applied.append("%s:%s" % (ob.name, mname))
                except RuntimeError as exc:
                    skipped.append({"object": ob.name, "modifier": mname, "reason": str(exc).strip()})
    return applied, skipped


def glb_summary(path):
    with open(path, "rb") as fh:
        magic, _ver, _len = struct.unpack("<4sII", fh.read(12))
        clen, ctype = struct.unpack("<II", fh.read(8))
        doc = json.loads(fh.read(clen)) if ctype == 0x4E4F534A else {}
    return {"cameras": len(doc.get("cameras", [])),
            "lights": len(doc.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
            "double_sided": sum(1 for m in doc.get("materials", []) if m.get("doubleSided")),
            "meshes": len(doc.get("meshes", [])), "materials": len(doc.get("materials", [])),
            "images": len(doc.get("images", [])), "animations": len(doc.get("animations", [])),
            "nodes": len(doc.get("nodes", [])), "node_names": [n.get("name") for n in doc.get("nodes", [])], "extensionsUsed": doc.get("extensionsUsed", [])}


def main() -> int:
    o = parse_args()
    objs = collect(o["root"])
    warnings = material_warnings()
    sources = gn_instance_sources(objs)
    if o["gn_instances"]:
        for src in sources:
            src.hide_set(True)
    else:
        warnings += ["instance source %r is exported as its own node (hide_render does not exclude it); "
                     "delete it after applying or use --gn-instances" % src.name for src in sources]
    if o["cull"]:
        for mat in bpy.data.materials:
            mat.use_backface_culling = True
    applied, skipped = apply_modifiers(objs, o["apply"], keep_gn=o["gn_instances"])

    wanted = dict(
        filepath=os.path.abspath(o["out"]), export_format="GLB", export_yup=True,
        export_apply=False, use_selection=bool(o["root"]),
        export_cameras=o["cameras"], export_lights=o["lights"], export_extras=o["extras"],
        export_gpu_instances=True, export_gn_mesh=True, export_animations=True,
        use_visible=bool(o["gn_instances"]),
        export_import_convert_lighting_mode=o["lighting"].upper(),
        export_image_format={"auto": "AUTO", "webp": "WEBP", "jpeg": "JPEG"}[o["images"]],
        export_draco_mesh_compression_enable=False, export_meshopt_compression_enable=False,
    )
    props = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    kwargs = {k: v for k, v in wanted.items() if k in props}
    dropped = sorted(k for k in wanted if k not in props)

    if o["root"]:
        for ob in bpy.context.view_layer.objects:  # no active object in -b: do not use select_all
            ob.select_set(False)
        for ob in objs:
            ob.select_set(True)
    os.makedirs(os.path.dirname(kwargs["filepath"]) or ".", exist_ok=True)
    try:
        res = bpy.ops.export_scene.gltf(**kwargs)
    except Exception as exc:  # operator errors surface as RuntimeError
        print(json.dumps({"ok": False, "error": str(exc), "dropped_kwargs": dropped}))
        return 1
    ok = "FINISHED" in res and os.path.exists(kwargs["filepath"])
    out = {"ok": ok, "out": kwargs["filepath"], "applied": applied, "skipped": skipped, "warnings": warnings,
           "dropped_kwargs": dropped}
    if ok:
        out["bytes"] = os.path.getsize(kwargs["filepath"])
        out["glb"] = glb_summary(kwargs["filepath"])
    print(json.dumps(out))
    return 0 if ok else 1


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    if code:
        sys.exit(code)
