#!/usr/bin/env python3
"""Build a Principled material from a folder of PBR maps: detect suffixes, set colour spaces, wire, assign, preview.

Runs only inside Blender; the loaded .blend is never saved (use --save for a copy):

    blender -b scene.blend --factory-startup --python-exit-code 1 \
        --python <skill>/assets/blender/material_from_maps.py -- \
        --dir textures/rock --name Rock --object Floor --tile-m 2 --preview .3d/evidence/rock.png

Args after `--`:
  --dir DIR          folder of maps; required. Image files only (png jpg tif exr webp)
  --name M           material name (default: the folder name)
  --object NAME      assign to this mesh (repeat the flag or comma-separate for several); replaces its slots
  --tile-m F         metres covered by one tile (default 1.0); Mapping scale = 1/F. UV mode assumes 1 UV unit = 1 m
  --box B            use Object coordinates with BOX projection and blend B (e.g. 0.2): no UVs needed, object
                     scale should be applied. Default: UV coordinates
  --normal gl|dx|auto  normal convention (default auto: from the file name, OpenGL when unmarked); dx inserts a
                     green flip (Separate Color, 1-G, Combine Color)
  --no-height        do not wire a height/displacement map as Bump
  --preview PNG      render a 3 m plane (UV scaled so 1 UV = 1 m) plus a sphere on a temp scene, then remove it
  --engine cycles|eevee   preview engine (default cycles); --samples N (default 32)
  --save COPY.blend  write a copy of the session with the material (images stay file-backed, paths remapped)
Detected by the last name tokens, case-insensitive, resolution tokens (2k, 1024) ignored:
  albedo: albedo basecolor base_color diffuse diff color col | normal: normal nor nrm (+ gl / dx, e.g. nor_gl,
  NormalDX) | roughness: roughness rough | metallic: metalness metallic metal | ao: ambientocclusion occlusion ao
  | packed: arm orm (R=AO G=rough B=metal) | height: height displacement disp bump | emission: emission emissive emit
Wiring: UV|Object -> Mapping -> Image Textures -> Principled; AO multiplies base colour; height -> Bump (distance
0.01 m) chained after the normal map. Albedo and emission are sRGB, all else Non-Color.
Prints one JSON line {"ok","material","maps","normal","ignored","warnings","assigned","preview"?,...}.
Exit 0 ok / 1 problems (no albedo, two different files for one map, unreadable image, blank preview) / 2 usage.
"""
from __future__ import annotations

import json
import os
import re
import sys

try:
    import bpy
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("material_from_maps.py runs only inside Blender (see the docstring)\n")
    sys.exit(2)

EXTS = (".png", ".tif", ".tiff", ".exr", ".jpg", ".jpeg", ".webp")
# synonym -> (category, variant). Longest/most specific first is not needed: lookup is exact on joined tokens.
SYN = {}
for _cat, _names in {
    "albedo": "albedo basecolor diffuse diff color colour col base",
    "roughness": "roughness rough rgh",
    "metallic": "metallic metalness metal mtl",
    "ao": "ambientocclusion occlusion ao",
    "packed": "arm orm",
    "height": "height displacement disp bump",
    "emission": "emission emissive emit",
}.items():
    for _n in _names.split():
        SYN[_n] = (_cat, None)
for _n in "normal nor nrm".split():
    SYN[_n] = ("normal", None)
for _n in "normalgl norgl nrmgl".split():
    SYN[_n] = ("normal", "gl")
for _n in "normaldx nordx nrmdx".split():
    SYN[_n] = ("normal", "dx")
SRGB = ("albedo", "emission")
RES_TOKEN = re.compile(r"^(\d+k|\d{3,5}|png|jpg|jpeg|exr|tif|tiff)$")
VALUED = {"dir", "name", "object", "tile-m", "box", "normal", "preview", "engine", "samples", "save"}


def usage(msg: str = "") -> None:
    sys.stderr.write(__doc__ + ("\n" + msg + "\n" if msg else ""))
    sys.exit(2)


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o: dict = {"objects": []}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        k = a[2:] if a.startswith("--") else ""
        if k == "no-height":
            o["no_height"] = True
            i += 1
        elif k in VALUED and i + 1 < len(argv):
            if k == "object":
                o["objects"] += [x for x in argv[i + 1].split(",") if x]
            else:
                o[k] = argv[i + 1]
            i += 2
        else:
            usage("unknown or incomplete arg: %s" % a)
    if "dir" not in o:
        usage("--dir is required")
    try:
        o["tile_m"] = float(o.get("tile-m", 1.0))
        o["box"] = float(o["box"]) if "box" in o else None
        o["samples"] = int(o.get("samples", 32))
    except ValueError:
        usage("numeric option could not be parsed")
    o["normal_mode"] = o.get("normal", "auto").lower()
    o["engine"] = o.get("engine", "cycles").lower()
    if o["tile_m"] <= 0 or o["normal_mode"] not in ("gl", "dx", "auto") or o["engine"] not in ("cycles", "eevee"):
        usage("--tile-m > 0, --normal gl|dx|auto, --engine cycles|eevee")
    if not os.path.isdir(o["dir"]):
        usage("not a directory: %s" % o["dir"])
    return o


# ---- detection ----------------------------------------------------------------------------------------------


def tokens(stem: str) -> list[str]:
    stem = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem)  # camelCase -> words
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", stem.lower()) if t]
    while len(toks) > 1 and RES_TOKEN.match(toks[-1]):
        toks.pop()
    return toks


def classify(filename: str):
    t = tokens(os.path.splitext(filename)[0])
    for cand in ("".join(t[-2:]), t[-1] if t else ""):
        if cand in SYN:
            return SYN[cand]
    return None


def detect(folder: str):
    found: dict = {}
    ignored: list[str] = []
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith(EXTS):
            continue
        hit = classify(f)
        if hit is None:
            ignored.append(f)
            continue
        found.setdefault(hit[0], []).append((f, hit[1]))
    return found, ignored


def pick(cat: str, items: list, problems: list, warnings: list):
    """One file per category. Same stem in several formats -> prefer png/tif/exr/jpg. nor_gl beats nor_dx."""
    if cat == "normal":
        gl = [x for x in items if x[1] == "gl"]
        if gl and len(gl) < len(items):
            warnings.append("normal: both OpenGL and DirectX files present; using %s" % gl[0][0])
            items = gl
    stems = {os.path.splitext(f)[0].lower() for f, _ in items}
    if len(stems) > 1:
        problems.append("%s: ambiguous, %d different files match (%s)" % (cat, len(stems), ", ".join(f for f, _ in items)))
        return None
    order = {e: n for n, e in enumerate(EXTS)}
    return sorted(items, key=lambda x: order[os.path.splitext(x[0])[1].lower()])[0]


# ---- node helpers -------------------------------------------------------------------------------------------


def sock(node, identifier: str, outputs: bool = False):
    for s in (node.outputs if outputs else node.inputs):
        if s.identifier == identifier:
            return s
    raise KeyError(identifier)


class Builder:
    def __init__(self, mat, uv_scale: float, box):
        self.mat = mat
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.col = 0
        self.row = 0
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.out.location = (800, 0)
        self.bsdf = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.bsdf.location = (500, 0)
        self.nt.links.new(self.bsdf.outputs["BSDF"], self.out.inputs["Surface"])
        coord = self.nt.nodes.new("ShaderNodeTexCoord")
        coord.location = (-900, 0)
        self.mapping = self.nt.nodes.new("ShaderNodeMapping")
        self.mapping.location = (-700, 0)
        self.mapping.inputs["Scale"].default_value = (uv_scale, uv_scale, uv_scale)
        self.nt.links.new(coord.outputs["Object" if box is not None else "UV"], self.mapping.inputs["Vector"])
        self.box = box
        self.images: dict = {}

    def tex(self, cat: str, path: str, colour: bool):
        n = self.nt.nodes.new("ShaderNodeTexImage")
        n.location = (-450, 300 - 280 * self.row)
        self.row += 1
        n.label = cat
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        n.extension = "REPEAT"
        if self.box is not None:
            n.projection = "BOX"
            n.projection_blend = self.box
        self.nt.links.new(self.mapping.outputs["Vector"], n.inputs["Vector"])
        self.images[cat] = n.image
        return n

    def link(self, a, b):
        self.nt.links.new(a, b)


def build_material(name: str, picks: dict, normal_flip: bool, o: dict):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = Builder(mat, 1.0 / o["tile_m"], o["box"])
    nt = b.nt
    colour_out = None
    if "albedo" in picks:
        colour_out = b.tex("albedo", picks["albedo"], True).outputs["Color"]
    ao_out = None
    if "ao" in picks:
        ao_out = b.tex("ao", picks["ao"], False).outputs["Color"]
    if "packed" in picks and ("roughness" in picks or "metallic" in picks or "ao" in picks):
        del picks["packed"]  # separate files win; reported by the caller
    if "packed" in picks:
        t = b.tex("packed", picks["packed"], False)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.location = (-200, -200)
        b.link(t.outputs["Color"], sep.inputs["Color"])
        ao_out = sep.outputs["Red"]
        b.link(sep.outputs["Green"], b.bsdf.inputs["Roughness"])
        b.link(sep.outputs["Blue"], b.bsdf.inputs["Metallic"])
    if ao_out is not None:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.location = (150, 250)
        sock(mix, "Factor_Float").default_value = 1.0
        b.link(colour_out, sock(mix, "A_Color"))
        b.link(ao_out, sock(mix, "B_Color"))
        colour_out = sock(mix, "Result_Color", outputs=True)
    if colour_out is not None:
        b.link(colour_out, b.bsdf.inputs["Base Color"])
    if "roughness" in picks:
        b.link(b.tex("roughness", picks["roughness"], False).outputs["Color"], b.bsdf.inputs["Roughness"])
    if "metallic" in picks:
        b.link(b.tex("metallic", picks["metallic"], False).outputs["Color"], b.bsdf.inputs["Metallic"])
    if "emission" in picks:
        b.link(b.tex("emission", picks["emission"], True).outputs["Color"], b.bsdf.inputs["Emission Color"])
        b.bsdf.inputs["Emission Strength"].default_value = 1.0
    normal_src = None
    if "normal" in picks:
        t = b.tex("normal", picks["normal"], False).outputs["Color"]
        if normal_flip:
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            inv = nt.nodes.new("ShaderNodeMath")
            inv.operation = "SUBTRACT"
            inv.inputs[0].default_value = 1.0
            com = nt.nodes.new("ShaderNodeCombineColor")
            sep.location, inv.location, com.location = (-250, -450), (-80, -520), (90, -450)
            b.link(t, sep.inputs["Color"])
            b.link(sep.outputs["Green"], inv.inputs[1])
            b.link(sep.outputs["Red"], com.inputs["Red"])
            b.link(inv.outputs["Value"], com.inputs["Green"])
            b.link(sep.outputs["Blue"], com.inputs["Blue"])
            t = com.outputs["Color"]
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.space = "TANGENT"
        nm.location = (250, -450)
        b.link(t, nm.inputs["Color"])
        normal_src = nm.outputs["Normal"]
    if "height" in picks and not o.get("no_height"):
        bump = nt.nodes.new("ShaderNodeBump")
        bump.location = (300, -650)
        bump.inputs["Distance"].default_value = 0.01
        b.link(b.tex("height", picks["height"], False).outputs["Color"], bump.inputs["Height"])
        if normal_src is not None:
            b.link(normal_src, bump.inputs["Normal"])
        normal_src = bump.outputs["Normal"]
    if normal_src is not None:
        b.link(normal_src, b.bsdf.inputs["Normal"])
    return mat, b.images


# ---- preview ------------------------------------------------------------------------------------------------


def render_preview(mat, o: dict) -> dict:
    import bmesh
    import numpy as np

    sc = bpy.data.scenes.new("mfm_preview")
    made = []  # (collection of datablocks, datablock)

    def link(ob):
        sc.collection.objects.link(ob)
        made.append((bpy.data.objects, ob))

    me = bpy.data.meshes.new("mfm_plane")
    me.from_pydata([(-1.5, 0, -1.5), (1.5, 0, -1.5), (1.5, 0, 1.5), (-1.5, 0, 1.5)], [], [(0, 1, 2, 3)])
    uvl = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        x, _, z = me.vertices[loop.vertex_index].co
        uvl.data[loop.index].uv = (x + 1.5, z + 1.5)  # 1 UV unit = 1 m
    me.materials.append(mat)
    made.append((bpy.data.meshes, me))
    plane = bpy.data.objects.new("mfm_plane", me)
    plane.location = (-2.0, 0, 0)
    link(plane)

    bm = bmesh.new()
    uvlayer = bm.loops.layers.uv.verify()
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0, calc_uvs=True)
    for f in bm.faces:
        f.smooth = True
        for lp in f.loops:
            lp[uvlayer].uv = lp[uvlayer].uv * 3.0
    sme = bpy.data.meshes.new("mfm_sphere")
    bm.to_mesh(sme)
    bm.free()
    sme.materials.append(mat)
    made.append((bpy.data.meshes, sme))
    sph = bpy.data.objects.new("mfm_sphere", sme)
    sph.location = (1.4, 0, 0)
    link(sph)

    cam_d = bpy.data.cameras.new("mfm_cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = 6.6
    made.append((bpy.data.cameras, cam_d))
    cam = bpy.data.objects.new("mfm_cam", cam_d)
    cam.location = (-0.55, -8, 0)
    cam.rotation_euler = (1.5707963, 0, 0)
    link(cam)
    sun_d = bpy.data.lights.new("mfm_sun", "SUN")
    sun_d.energy = 3.0
    made.append((bpy.data.lights, sun_d))
    sun = bpy.data.objects.new("mfm_sun", sun_d)
    sun.rotation_euler = (0.8, 0.2, -0.5)
    link(sun)

    world = bpy.data.worlds.new("mfm_world")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.55, 0.55, 0.55, 1)
    bg.inputs["Strength"].default_value = 1.0
    made.append((bpy.data.worlds, world))
    sc.world = world
    sc.camera = cam
    r = sc.render
    r.engine = "CYCLES" if o["engine"] == "cycles" else "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1024, 512, 100
    r.image_settings.file_format = "PNG"
    r.filepath = o["preview"]
    sc.view_settings.view_transform = "Standard"
    if o["engine"] == "cycles":
        sc.cycles.device = "CPU"
        sc.cycles.samples = o["samples"]
        sc.cycles.use_denoising = False
    os.makedirs(os.path.dirname(os.path.abspath(o["preview"])), exist_ok=True)
    info: dict = {"path": o["preview"], "engine": r.engine}
    try:
        res = bpy.ops.render.render(write_still=True, scene=sc.name)
        info["result"] = sorted(res)
        im = bpy.data.images.load(o["preview"])
        im.colorspace_settings.name = "Non-Color"
        buf = np.empty(im.size[0] * im.size[1] * 4, np.float32)
        im.pixels.foreach_get(buf)
        bpy.data.images.remove(im)
        px = buf.reshape(-1, 4)[:, :3]
        info["mean"] = round(float(px.mean()), 4)
        info["std"] = round(float(px.std()), 4)
        info["blank"] = bool(px.std() < 1e-3)
    finally:
        bpy.data.scenes.remove(sc)
        for coll, d in made:
            try:
                coll.remove(d)
            except (ReferenceError, RuntimeError):
                pass
    return info


# ---- main ---------------------------------------------------------------------------------------------------


def main() -> None:
    o = parse_args()
    objs = []
    for n in o["objects"]:
        ob = bpy.data.objects.get(n)
        if ob is None or ob.type != "MESH":
            sys.stderr.write("no mesh object named %r\n" % n)
            sys.exit(2)
        objs.append(ob)

    problems: list[str] = []
    warnings: list[str] = []
    found, ignored = detect(o["dir"])
    picks: dict = {}
    normal_variant = None
    for cat, items in found.items():
        chosen = pick(cat, items, problems, warnings)
        if chosen:
            picks[cat] = os.path.join(o["dir"], chosen[0])
            if cat == "normal":
                normal_variant = chosen[1]
    if "albedo" not in picks and not any("albedo" in p for p in problems):
        problems.append("no albedo map found (looked for albedo/basecolor/diffuse/diff/color/col in %s)" % o["dir"])
    if "packed" in picks and any(k in picks for k in ("roughness", "metallic", "ao")):
        warnings.append("packed arm/orm ignored: separate roughness/metallic/ao files are present")
    if problems:
        print(json.dumps({"ok": False, "dir": o["dir"], "maps": {k: os.path.basename(v) for k, v in picks.items()},
                          "ignored": ignored, "problems": problems, "warnings": warnings}))
        sys.exit(1)

    conv = o["normal_mode"] if o["normal_mode"] != "auto" else (normal_variant or "gl")
    if "normal" in picks and o["normal_mode"] == "auto" and normal_variant is None:
        warnings.append("normal map is not marked gl/dx; assumed OpenGL (use --normal dx if bumps look inverted)")
    name = o.get("name") or os.path.basename(os.path.abspath(o["dir"])) or "Material"
    try:
        mat, images = build_material(name, picks, conv == "dx", o)
    except RuntimeError as e:
        print(json.dumps({"ok": False, "problems": ["could not load an image: %s" % str(e).strip()[:200]]}))
        sys.exit(1)

    mat.use_fake_user = True  # survives --save even when no --object is given
    for ob in objs:
        ob.data.materials.clear()
        ob.data.materials.append(mat)

    result = {
        "material": mat.name, "dir": o["dir"],
        "maps": {k: {"file": os.path.basename(v),
                     "colour_space": images[k].colorspace_settings.name} for k, v in picks.items() if k in images},
        "normal": {"convention": conv, "flipped": bool(conv == "dx" and "normal" in picks)},
        "mapping": {"scale": round(1.0 / o["tile_m"], 6), "coords": "Object+BOX" if o["box"] is not None else "UV",
                    "box_blend": o["box"]},
        "ignored": ignored, "assigned": [ob.name for ob in objs], "warnings": warnings,
    }
    if o.get("save"):
        os.makedirs(os.path.dirname(os.path.abspath(o["save"])), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=o["save"], copy=True)
        result["saved"] = o["save"]
    if o.get("preview"):
        try:
            result["preview"] = render_preview(mat, o)
        except RuntimeError as e:
            problems.append("preview render failed: %s" % str(e).strip()[:200])
        else:
            if result["preview"].get("blank"):
                problems.append("preview is blank (uniform image); check UVs / lighting")
    result["problems"] = problems
    result["ok"] = not problems
    print(json.dumps(result))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
