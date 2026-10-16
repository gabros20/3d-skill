#!/usr/bin/env python3
"""Render stills, shot moves or a seamless turntable from a shots.v1 camera list.

Runs only inside Blender:

    blender -b scene.blend --factory-startup --python-exit-code 1 \
        --python <skill>/assets/blender/render_shots.py -- --shots .3d/shots.json --out .3d/evidence/blender

Reads the canonical `shots.v1` file (schema in references/brief-spec.md): per shot `id`,
exactly one of `focal_mm` (36x24 full-frame) | `fov` (vertical deg) | `ortho_height`,
`position`/`target` in three.js/glTF axes (Y up, metres; converted here to Blender Z up:
x->x, y->z, z->-y), optional `roll_deg`, `duration_s`, `ease`, end pose `to`.
Top-level `aspect` ("W:H") and `fps` are honoured.

Args after `--`:
  --shots FILE   required                 --out DIR   required
  --engine eevee|cycles|workbench  (default eevee; BLENDER_EEVEE)
  --res WIDTH    horizontal pixels (default 1280; height from `aspect`, default 16:9)
  --samples N    (default 32 eevee / 64 cycles)
  --view standard|agx|neutral  colour view transform (default: keep the scene's)
  --moves        also render shots that have `to` + `duration_s` as frames
                 <id>_0001.png ... (eased from start pose to `to`); default: one still per
                 shot at the start pose, <id>.png
  --turntable N  orbit the first shot N frames around its target (camera and lights orbit,
                 the asset never moves; frame N+1 == frame 1): turntable_0001.png ...
Prints one JSON line {"ok","engine","files":[...],"missing":[...]}.
Exit 0 ok / 1 render failed / 2 usage.
"""
from __future__ import annotations

import json
import math
import os
import sys

try:
    import bpy
    from mathutils import Vector
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("render_shots.py runs only inside Blender (see docstring)\n")
    sys.exit(2)

ENGINES = {"eevee": "BLENDER_EEVEE", "cycles": "CYCLES", "workbench": "BLENDER_WORKBENCH"}
VIEWS = {"standard": "Standard", "agx": "AgX", "neutral": "Khronos PBR Neutral"}


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"shots": None, "out": None, "engine": "eevee", "res": "1280", "samples": None,
         "view": None, "turntable": 0, "moves": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--moves":
            o["moves"] = True
            i += 1
        elif a.startswith("--") and a[2:] in o and i + 1 < len(argv):
            o[a[2:]] = argv[i + 1]
            i += 2
        else:
            sys.stderr.write(__doc__ + "\nunknown arg: %s\n" % a)
            sys.exit(2)
    try:
        o["w"] = int(o["res"])
        o["turntable"] = int(o["turntable"])
    except ValueError:
        o["shots"] = None
    if not o["shots"] or not o["out"] or o["engine"] not in ENGINES or \
            (o["view"] and o["view"] not in VIEWS):
        sys.stderr.write(__doc__)
        sys.exit(2)
    return o


def to_blender(p):
    x, y, z = p  # glTF/three Y-up -> Blender Z-up
    return Vector((x, -z, y))


def ease(kind, t):
    if kind == "linear":
        return t
    if kind == "in":
        return t * t
    if kind == "out":
        return 1 - (1 - t) * (1 - t)
    return t * t * (3 - 2 * t)  # inOut


def lens_for(cam_data, pose):
    """Apply focal_mm | fov | ortho_height from a pose dict (sensor fit is vertical, 24 mm)."""
    if "ortho_height" in pose:
        cam_data.type, cam_data.ortho_scale = "ORTHO", float(pose["ortho_height"])
    elif "focal_mm" in pose:
        cam_data.type, cam_data.lens = "PERSP", float(pose["focal_mm"])
    elif "fov" in pose:
        cam_data.type = "PERSP"
        cam_data.lens = cam_data.sensor_height / (2 * math.tan(math.radians(float(pose["fov"])) / 2))


def vfov(pose):
    if "fov" in pose:
        return float(pose["fov"])
    return math.degrees(2 * math.atan(12.0 / float(pose["focal_mm"])))


def place(cam, cam_data, pose):
    cam.location = to_blender(pose["position"])
    aim(cam, to_blender(pose["target"]), float(pose.get("roll_deg", 0)))
    lens_for(cam_data, pose)


def setup_scene(o):
    sc = bpy.context.scene
    sc.render.engine = ENGINES[o["engine"]]
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = o["w"], o["h"], 100
    sc.render.fps = o["fps"]
    samples = int(o["samples"]) if o["samples"] else (64 if o["engine"] == "cycles" else 32)
    if o["engine"] == "cycles":
        sc.cycles.samples = samples
    elif o["engine"] == "eevee":
        sc.eevee.taa_render_samples = samples
    try:  # 5.x: media_type must be set before file_format
        sc.render.image_settings.media_type = "IMAGE"
    except (AttributeError, TypeError):
        pass
    sc.render.image_settings.file_format = "PNG"
    if o["view"]:
        try:
            sc.view_settings.view_transform = VIEWS[o["view"]]
        except TypeError:
            sys.stderr.write("view transform %r unavailable in this Blender\n" % VIEWS[o["view"]])
    if not any(ob.type == "LIGHT" for ob in sc.objects):
        data = bpy.data.lights.new("render_shots_key", "AREA")
        data.energy, data.size = 800, 3
        key = bpy.data.objects.new("render_shots_key", data)
        key.location = (3, -3, 4)
        sc.collection.objects.link(key)
        world = sc.world or bpy.data.worlds.new("World")
        sc.world = world
        world.color = (0.05, 0.05, 0.05)
    return sc


def aim(cam, target, roll_deg=0.0):
    direction = target - cam.location
    q = direction.to_track_quat("-Z", "Y")
    if roll_deg:
        from mathutils import Quaternion
        q = q @ Quaternion((0, 0, 1), math.radians(roll_deg))
    cam.rotation_euler = q.to_euler()


def render(sc, path, animation=False):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=not animation, animation=animation)


def main() -> int:
    o = parse_args()
    with open(o["shots"]) as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or data.get("schema") != "shots.v1" or not data.get("shots"):
        sys.stderr.write("shots file must be schema shots.v1 with a non-empty shots list\n")
        return 2
    shots = data["shots"]
    try:
        aw, ah = (float(v) for v in str(data.get("aspect", "16:9")).split(":"))
    except ValueError:
        aw, ah = 16.0, 9.0
    o["h"] = max(1, round(o["w"] * ah / aw))
    o["fps"] = int(data.get("fps", 30))
    os.makedirs(o["out"], exist_ok=True)
    sc = setup_scene(o)
    cam_data = bpy.data.cameras.new("render_shots_cam")
    cam = bpy.data.objects.new("render_shots_cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_data.sensor_fit, cam_data.sensor_height = "VERTICAL", 24.0
    files = []
    first = None
    for shot in shots:
        sid = str(shot["id"])
        place(cam, cam_data, shot)
        if first is None:
            first = (cam.location.copy(), to_blender(shot["target"]))
        end = shot.get("to")
        frames = round(float(shot.get("duration_s", 0)) * o["fps"])
        if o["moves"] and end and frames > 1:
            for f in range(frames):
                t = ease(shot.get("ease", "inOut"), f / (frames - 1))
                pose = dict(shot)
                for k in ("position", "target"):
                    if k in end:
                        pose[k] = [a + (b - a) * t for a, b in zip(shot[k], end[k])]
                for k in ("roll_deg", "ortho_height"):
                    if k in end:
                        pose[k] = float(shot.get(k, 0)) + (float(end[k]) - float(shot.get(k, 0))) * t
                if "focal_mm" in end or "fov" in end:  # mix as vertical fov so mixed lens keys work
                    f0, f1 = vfov(shot), vfov(end)
                    pose.pop("focal_mm", None)
                    pose["fov"] = f0 + (f1 - f0) * t
                place(cam, cam_data, pose)
                path = os.path.join(o["out"], "%s_%04d.png" % (sid, f + 1))
                render(sc, path)
                files.append(path)
        else:
            path = os.path.join(o["out"], sid + ".png")
            render(sc, path)
            files.append(path)

    if o["turntable"] > 0 and first:
        n = o["turntable"]
        pivot = bpy.data.objects.new("render_shots_pivot", None)
        sc.collection.objects.link(pivot)
        pivot.location = first[1]
        place(cam, cam_data, shots[0])
        if bpy.data.actions:
            sys.stderr.write("warning: scene has animation; turntable frames also play it\n")
        for ob in [cam] + [x for x in sc.objects if x.type == "LIGHT"]:
            mw = ob.matrix_world.copy()
            ob.parent = pivot
            ob.matrix_parent_inverse = pivot.matrix_world.inverted()
            ob.matrix_world = mw
        pivot.rotation_mode = "XYZ"
        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert("rotation_euler", index=2, frame=1)
        pivot.rotation_euler = (0, 0, 2 * math.pi)
        pivot.keyframe_insert("rotation_euler", index=2, frame=n + 1)
        action = pivot.animation_data.action
        try:  # 5.x slotted actions: channels live in layers/strips/channelbags
            fcurves = [fc for layer in action.layers for strip in layer.strips
                       for bag in strip.channelbags for fc in bag.fcurves]
        except AttributeError:
            fcurves = list(action.fcurves)
        for fc in fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        sc.frame_start, sc.frame_end = 1, n
        render(sc, os.path.join(o["out"], "turntable_"), animation=True)
        files += [os.path.join(o["out"], "turntable_%04d.png" % f) for f in range(1, n + 1)]

    missing = [f for f in files if not os.path.exists(f)]
    print(json.dumps({"ok": not missing, "engine": sc.render.engine, "files": files, "missing": missing}))
    return 1 if missing else 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    if code:
        sys.exit(code)
