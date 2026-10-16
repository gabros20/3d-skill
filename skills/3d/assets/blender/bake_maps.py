#!/usr/bin/env python3
"""Bake PBR maps from the loaded scene's object to image files, then check each map is not blank.

Runs only inside Blender; the loaded .blend is never saved (use --rebuild for an export-ready copy):

    blender -b scene.blend --factory-startup --python-exit-code 1 \
        --python <skill>/assets/blender/bake_maps.py -- \
        --object Hero --maps albedo,roughness,metallic,normal --res 2048 --out-dir .3d/versions/v001/maps

Args after `--`:
  --object NAME      mesh to bake onto (the low-poly when --high is used); required
  --maps LIST        comma list of albedo,roughness,metallic,normal,ao,emit,combined (default albedo,roughness,normal)
  --res N            square map size in px (default 1024)
  --margin PX        edge bleed in px, EXTEND (default 16)
  --samples N        Cycles samples (default 32; denoiser off, CPU)
  --out-dir DIR      required; writes <object>_<map>.png|exr
  --high NAME        bake from this object onto --object (selected to active) -- the hi-to-lo setup
  --extrusion F      cage extrusion in metres when --high is set (default 0.02)
  --ray F            max ray distance in metres when --high is set (default 0.05)
  --cage NAME        explicit cage object (implies use_cage)
  --uv NAME|auto     UV layer to bake into; a missing layer (or `auto` on a mesh without UVs) is created by
                     Smart UV Project and reported. Default: the active layer, created if the mesh has none
  --data-format png16|exr|png   data maps (roughness, metallic, ao, normal), Non-Color, default png16; colour maps
                     (albedo, emit, combined) are always 8-bit sRGB PNG
  --rebuild COPY.blend  save a COPY whose object uses one new material wired to the baked maps (albedo, roughness,
                     metallic, normal, emit). Export that copy with export_web.py; ao and combined are not wired
  --allow-flat       do not fail on a uniform map (a constant roughness over the whole UV square is legitimate)
How: one temp image node per material (restored afterwards); albedo and metallic are baked by routing the
Principled Base Color / Metallic through a temp Emission shader (a DIFFUSE bake of a metal is black). Normals are OpenGL tangent space (green up).
Prints Blender's log, then one JSON line {"ok","object","maps":{name:{path,mean,std,...}},"problems",...}.
Exit 0 ok / 1 problems (a map is flat, NaN, or CANCELLED; normal mean blue < 0.5) / 2 usage.
"""
from __future__ import annotations

import json
import math
import os
import sys

try:
    import bpy
    import numpy as np
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("bake_maps.py runs only inside Blender (see the docstring)\n")
    sys.exit(2)

COLOUR_MAPS = ("albedo", "emit", "combined")
DATA_MAPS = ("roughness", "metallic", "ao", "normal")
ALL_MAPS = ("albedo", "roughness", "metallic", "normal", "ao", "emit", "combined")
BAKE_TYPE = {"albedo": "EMIT", "roughness": "ROUGHNESS", "metallic": "EMIT", "normal": "NORMAL",
             "ao": "AO", "emit": "EMIT", "combined": "COMBINED"}
VALUED = {"object", "maps", "res", "margin", "samples", "out-dir", "high", "extrusion", "ray", "cage", "uv",
          "data-format", "rebuild"}


def usage(msg: str = "") -> None:
    sys.stderr.write(__doc__ + ("\n" + msg + "\n" if msg else ""))
    sys.exit(2)


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o: dict = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        k = a[2:] if a.startswith("--") else ""
        if k == "allow-flat":
            o[k] = True
            i += 1
        elif k in VALUED and i + 1 < len(argv):
            o[k] = argv[i + 1]
            i += 2
        else:
            usage("unknown or incomplete arg: %s" % a)
    if "object" not in o or "out-dir" not in o:
        usage("--object and --out-dir are required")
    try:
        o["res"] = int(o.get("res", 1024))
        o["margin"] = int(o.get("margin", 16))
        o["samples"] = int(o.get("samples", 32))
        o["extrusion"] = float(o.get("extrusion", 0.02))
        o["ray"] = float(o.get("ray", 0.05))
    except ValueError:
        usage("numeric option could not be parsed")
    o["maps"] = [m.strip().lower() for m in o.get("maps", "albedo,roughness,normal").split(",") if m.strip()]
    bad = [m for m in o["maps"] if m not in ALL_MAPS]
    if bad or not o["maps"]:
        usage("unknown map(s): %s" % ", ".join(bad or ["(none)"]))
    o["data_format"] = o.get("data-format", "png16").lower()
    if o["data_format"] not in ("png16", "exr", "png") or not 8 <= o["res"] <= 16384:
        usage("--data-format png16|exr|png, --res 8..16384")
    return o


# ---- scene prep ---------------------------------------------------------------------------------------------


def need_object(name: str):
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != "MESH":
        sys.stderr.write("no mesh object named %r\n" % name)
        sys.exit(2)
    return ob


def ensure_uv(ob, want: str | None, margin_px: int, res: int) -> dict:
    """Make `want` (or the active layer) the active+render UV layer, creating it with Smart UV Project."""
    me = ob.data
    layer = me.uv_layers.get(want) if want and want != "auto" else (me.uv_layers.active if me.uv_layers else None)
    created = layer is None
    if created:
        layer = me.uv_layers.new(name=want if want and want != "auto" else "UVMap")
        me.uv_layers.active = layer
        for other in bpy.context.view_layer.objects:
            other.select_set(False)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=max(0.002, 2.0 * margin_px / res))
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
    me.uv_layers.active = layer
    layer.active_render = True
    return {"layer": layer.name, "created": created}


def slot_materials(ob):
    """Every slot gets a node-based material; returns (materials, temp materials we added)."""
    temps = []
    if not ob.material_slots:
        ob.data.materials.append(None)
    for slot in ob.material_slots:
        if slot.material is None:
            m = bpy.data.materials.new("bake_tmp")
            m.use_nodes = True
            slot.material = m
            temps.append(m)
        elif slot.material.node_tree is None:
            slot.material.use_nodes = True
    return [s.material for s in ob.material_slots], temps


def make_image(name: str, res: int, colour: bool, float_buf: bool):
    im = bpy.data.images.new(name, res, res, alpha=False, float_buffer=float_buf)
    im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return im


def principled(mat):
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial" and n.is_active_output), None)
    if out and out.inputs["Surface"].is_linked:
        n = out.inputs["Surface"].links[0].from_node
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            return n
    return next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)


def swap_in(mats, socket: str):
    """Route a Principled input (Metallic or Base Color) through a temp Emission shader; returns the undo list.
    Emission is the only pass that returns the raw input: a DIFFUSE bake of a metal is black."""
    undo = []
    for m in mats:
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial" and n.is_active_output), None)
        if out is None:
            continue
        pr = principled(m)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        inp = pr.inputs[socket] if pr is not None else None
        if inp is not None and inp.is_linked:
            nt.links.new(inp.links[0].from_socket, em.inputs["Color"])
        elif inp is not None and socket == "Base Color":
            em.inputs["Color"].default_value = tuple(inp.default_value)
        else:
            v = float(inp.default_value) if inp is not None else 0.0
            em.inputs["Color"].default_value = (v, v, v, 1.0)
        sock = out.inputs["Surface"]
        prev = sock.links[0].from_socket if sock.is_linked else None
        nt.links.new(em.outputs["Emission"], sock)
        undo.append((nt, out, em, prev))
    return undo


def swap_out(undo):
    for nt, out, em, prev in undo:
        nt.nodes.remove(em)
        if prev is not None:
            nt.links.new(prev, out.inputs["Surface"])


def bake_kwargs(o: dict, kind: str, with_high: bool) -> dict:
    """Operator kwargs, filtered through the operator's own property list."""
    props = {p.identifier for p in bpy.ops.object.bake.get_rna_type().properties}
    kw = {"type": BAKE_TYPE[kind], "margin": o["margin"], "margin_type": "EXTEND", "use_clear": True,
          "use_selected_to_active": with_high, "normal_space": "TANGENT"}
    if kind == "combined":
        kw["pass_filter"] = {"DIRECT", "INDIRECT", "DIFFUSE", "GLOSSY", "TRANSMISSION", "EMIT"}
    else:
        kw["pass_filter"] = set()
    if with_high:
        kw["cage_extrusion"] = o["extrusion"]
        kw["max_ray_distance"] = o["ray"]
        if o.get("cage"):
            kw["use_cage"] = True
            kw["cage_object"] = o["cage"]
    return {k: v for k, v in kw.items() if k in props}


# ---- io / checks --------------------------------------------------------------------------------------------


def pixels(im):
    w, h = im.size
    buf = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(buf)
    return buf.reshape(h, w, 4)


def write_image(im, path: str, kind: str, data_format: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if kind in COLOUR_MAPS or data_format == "png":
        # bytes as baked; data maps at 8-bit go through the same raw path with Non-Color
        if im.is_float:
            tmp = bpy.data.images.new("bake_out8", im.size[0], im.size[1], alpha=False)
            tmp.colorspace_settings.name = im.colorspace_settings.name
            tmp.pixels.foreach_set(np.clip(pixels(im), 0, 1).ravel())
            tmp.filepath_raw = path
            tmp.file_format = "PNG"
            tmp.save()
            bpy.data.images.remove(tmp)
        else:
            im.filepath_raw = path
            im.file_format = "PNG"
            im.save()
        return path
    s = bpy.context.scene
    ims = s.render.image_settings
    ims.file_format = "OPEN_EXR" if data_format == "exr" else "PNG"
    ims.color_depth = "32" if data_format == "exr" else "16"
    ims.color_mode = "RGB"
    ims.color_management = "OVERRIDE"
    ims.view_settings.view_transform = "Raw"
    ims.linear_colorspace_settings.name = "Non-Color"
    im.save_render(path, scene=s)
    return path


def check_map(kind: str, arr, allow_flat: bool) -> tuple[dict, list]:
    rgb = arr[..., :3]
    probs = []
    stats = {"mean": [round(float(v), 4) for v in rgb.reshape(-1, 3).mean(axis=0)],
             "std": round(float(rgb.reshape(-1, 3).std(axis=0).max()), 5),
             "coverage": round(float((rgb.max(axis=-1) > 1e-6).mean()), 4)}
    if not np.isfinite(arr).all():
        probs.append("%s: NaN or inf pixels" % kind)
    if stats["std"] < 2e-3 and not allow_flat:
        probs.append("%s: map is flat (std %.2g): the bake hit nothing, the UVs are degenerate, or the input is uniform "
                     "(--allow-flat if uniform is intended)" % (kind, stats["std"]))
    if kind == "normal":
        cov = rgb[..., 2] > 0
        blue = float(rgb[..., 2][cov].mean()) if cov.any() else 0.0
        stats["mean_covered"] = [round(float(rgb[..., c][cov].mean()), 4) if cov.any() else 0.0 for c in range(3)]
        if blue < 0.5:
            probs.append("normal: mean blue %.2f < 0.5 (inverted ray direction, wrong --high, or no cage)" % blue)
    return stats, probs


# ---- rebuild ------------------------------------------------------------------------------------------------


def rebuild(ob, paths: dict, out_blend: str) -> dict:
    mat = bpy.data.materials.new(ob.name + "_baked")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    used = []

    def tex(kind, colour):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(paths[kind], check_existing=False)
        n.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        n.label = kind
        used.append(kind)
        return n

    if "albedo" in paths:
        nt.links.new(tex("albedo", True).outputs["Color"], bsdf.inputs["Base Color"])
    if "roughness" in paths:
        nt.links.new(tex("roughness", False).outputs["Color"], bsdf.inputs["Roughness"])
    if "metallic" in paths:
        nt.links.new(tex("metallic", False).outputs["Color"], bsdf.inputs["Metallic"])
    if "normal" in paths:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.space = "TANGENT"
        nt.links.new(tex("normal", False).outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if "emit" in paths:
        nt.links.new(tex("emit", True).outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    os.makedirs(os.path.dirname(os.path.abspath(out_blend)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, copy=True)
    return {"path": out_blend, "material": mat.name, "wired": used,
            "not_wired": [k for k in paths if k not in used]}


# ---- main ---------------------------------------------------------------------------------------------------


def main() -> None:
    o = parse_args()
    ob = need_object(o["object"])
    high = need_object(o["high"]) if o.get("high") else None
    if o.get("cage"):
        need_object(o["cage"])

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = o["samples"]
    scene.cycles.use_denoising = False

    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = ob
    uv = ensure_uv(ob, o.get("uv"), o["margin"], o["res"])
    if high is not None:
        high.select_set(True)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

    mats, temps = slot_materials(ob)
    high_mats = [m for m in (s.material for s in high.material_slots) if m is not None and m.node_tree] if high else []
    stem = ob.name.replace(" ", "_")
    result = {"object": ob.name, "res": o["res"], "samples": o["samples"], "uv": uv, "hi_to_lo": high.name if high else None}
    problems: list[str] = []
    maps: dict = {}
    paths: dict = {}
    temp_images = []
    nodes = []  # (tree, node)
    try:
        for m in mats:
            n = m.node_tree.nodes.new("ShaderNodeTexImage")
            n.label = "bake_target"
            nodes.append((m.node_tree, n))
        for kind in o["maps"]:
            colour = kind in COLOUR_MAPS
            im = make_image("bake_%s_%s" % (stem, kind), o["res"], colour, float_buf=not colour)
            temp_images.append(im)
            for nt, n in nodes:
                n.image = im
                nt.nodes.active = n
            socket = {"metallic": "Metallic", "albedo": "Base Color"}.get(kind)
            undo = swap_in(mats + (high_mats if high is not None else []), socket) if socket else []
            try:
                r = bpy.ops.object.bake(**bake_kwargs(o, kind, high is not None))
            except RuntimeError as e:
                r = {"ERROR"}
                problems.append("%s: bake raised %s" % (kind, str(e).strip().splitlines()[-1][:160]))
            finally:
                swap_out(undo)
            if "FINISHED" not in r:
                if not any(p.startswith(kind + ":") for p in problems):
                    problems.append("%s: bake returned %s" % (kind, sorted(r)))
                maps[kind] = {"path": None, "baked": False}
                continue
            ext = "exr" if (not colour and o["data_format"] == "exr") else "png"
            path = write_image(im, os.path.join(o["out-dir"], "%s_%s.%s" % (stem, kind, ext)), kind, o["data_format"])
            stats, probs = check_map(kind, pixels(im), bool(o.get("allow-flat")))
            maps[kind] = dict(path=path, baked=True, colour_space="sRGB" if colour else "Non-Color", **stats)
            paths[kind] = path
            problems += probs
        result["maps"] = maps
        if o.get("rebuild") and paths and not problems:
            for nt, n in nodes:
                nt.nodes.remove(n)
            nodes = []
            result["rebuild"] = rebuild(ob, paths, o["rebuild"])
        elif o.get("rebuild"):
            problems.append("rebuild skipped: fix the bake problems first")
    finally:
        for nt, n in nodes:
            nt.nodes.remove(n)
        for im in temp_images:
            bpy.data.images.remove(im)
        for m in temps:
            if m.users <= 1 and not o.get("rebuild"):
                for s in ob.material_slots:
                    if s.material == m:
                        s.material = None
                bpy.data.materials.remove(m)
    result["problems"] = problems
    result["ok"] = not problems
    print(json.dumps(result))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
