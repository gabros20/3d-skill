#!/usr/bin/env python3
"""Check an armature and the meshes it deforms in the loaded Blender scene.

Runs only inside Blender (load the .blend before the script):

    blender -b rig.blend --factory-startup --python-exit-code 1 \
        --python <skill>/assets/blender/rig_check.py -- --max-influences 4 --json .3d/evidence/rig.json

Args after `--` (all optional):
  --armature NAME      armature object to check (default: every armature in the scene)
  --max-influences N   influences allowed per vertex (default 4, the glTF/web limit)
  --max-bones N        WARN above this many bones (default 256)
  --tol F              tolerance for "weights sum to 1" and "scale is 1" (default 0.01)
  --json PATH          write the full report to PATH
Checks: deform vs non-deform bones, bone count, unweighted vertices (FAIL), vertices over N
influences (FAIL), non-normalised weight sums (WARN), empty or bone-less vertex groups (WARN),
missing Armature modifier (FAIL), modifier order (WARN), scale not applied (WARN).
Prints one JSON line {"ok":..,"items":[{"level","object","check","message"}]}; levels PASS/WARN/FAIL.
Exit 0 no FAIL / 1 any FAIL / 2 usage or not inside Blender.
Meshes are matched to an armature by Armature modifier or parent; weights are read from the base mesh.
"""
from __future__ import annotations

import json
import os
import sys

try:
    import bpy
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("rig_check.py runs only inside Blender (see --help in the docstring)\n")
    sys.exit(2)


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"armature": None, "max_influences": 4, "max_bones": 256, "tol": 0.01, "json": None}
    kinds = {"armature": str, "max_influences": int, "max_bones": int, "tol": float, "json": str}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        key = a[2:].replace("-", "_")
        if a.startswith("--") and key in kinds and i + 1 < len(argv):
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


def main() -> int:
    opts = parse_args()
    items: list = []

    def add(level, obj, check, msg):
        items.append({"level": level, "object": obj, "check": check, "message": msg})

    scene = bpy.context.scene
    if opts["armature"]:
        arms = [o for o in scene.objects if o.type == "ARMATURE" and o.name == opts["armature"]]
        if not arms:
            add("FAIL", opts["armature"], "armature", "not found or not an armature")
    else:
        arms = [o for o in scene.objects if o.type == "ARMATURE"]
        if not arms:
            add("FAIL", "-", "armature", "no armature in the scene")
    tol = opts["tol"]

    for arm in arms:
        bones = arm.data.bones
        deform = {b.name for b in bones if b.use_deform}
        add("PASS" if deform else "FAIL", arm.name, "deform-bones",
            "%d deform / %d non-deform bones" % (len(deform), len(bones) - len(deform)))
        add("WARN" if len(bones) > opts["max_bones"] else "PASS", arm.name, "bone-count",
            "%d bones (limit %d)" % (len(bones), opts["max_bones"]))
        if any(abs(s - 1.0) > tol for s in arm.scale):
            add("WARN", arm.name, "scale", "armature scale %s not applied" % [round(s, 3) for s in arm.scale])

        meshes = []
        for ob in scene.objects:
            if ob.type != "MESH":
                continue
            mods = [m for m in ob.modifiers if m.type == "ARMATURE" and m.object == arm]
            if mods or ob.parent == arm:
                meshes.append((ob, mods))
        if not meshes:
            add("WARN", arm.name, "meshes", "no mesh uses this armature (modifier or parent)")

        for ob, mods in meshes:
            if any(abs(s - 1.0) > tol for s in ob.scale):
                add("WARN", ob.name, "scale", "mesh scale %s not applied" % [round(s, 3) for s in ob.scale])
            names = {g.index: g.name for g in ob.vertex_groups}
            if not mods:
                add("FAIL", ob.name, "armature-modifier",
                    "parented to %s but no Armature modifier targets it" % arm.name)
            else:
                add("PASS", ob.name, "armature-modifier", "Armature modifier present")
                types = [m.type for m in ob.modifiers]
                first = types.index("ARMATURE")
                if any(t in ("SUBSURF", "MULTIRES", "SOLIDIFY", "REMESH") for t in types[:first]):
                    add("WARN", ob.name, "modifier-order", "Armature modifier sits after a subdivision/generate modifier")
            if not any(n in deform for n in names.values()):
                add("FAIL", ob.name, "vertex-groups", "no vertex group matches a deform bone")
            for g in ob.vertex_groups:
                if g.name not in bones:
                    add("WARN", ob.name, "vertex-groups", "group %r has no bone" % g.name)
                elif g.name not in deform:
                    add("WARN", ob.name, "vertex-groups", "group %r is a non-deform bone" % g.name)
            unweighted = over = unnorm = 0
            used = set()
            for v in ob.data.vertices:
                ws = [(g.group, g.weight) for g in v.groups
                      if g.weight > 1e-6 and names.get(g.group) in deform]
                used.update(i for i, _ in ws)
                if not ws:
                    unweighted += 1
                    continue
                if len(ws) > opts["max_influences"]:
                    over += 1
                if abs(sum(w for _, w in ws) - 1.0) > tol:
                    unnorm += 1
            n = len(ob.data.vertices)
            add("FAIL" if unweighted else "PASS", ob.name, "unweighted",
                "%d of %d vertices unweighted" % (unweighted, n))
            add("FAIL" if over else "PASS", ob.name, "influences",
                "%d vertices over %d influences" % (over, opts["max_influences"]))
            add("WARN" if unnorm else "PASS", ob.name, "normalised",
                "%d vertices whose weights do not sum to 1" % unnorm)
            empty = [names[i] for i in names if i not in used and names[i] in deform]
            if empty:
                add("WARN", ob.name, "empty-groups", "deform groups with no weight: %s" % ", ".join(sorted(empty)[:8]))

    ok = not any(i["level"] == "FAIL" for i in items)
    report = {"ok": ok, "items": items}
    if opts["json"]:
        os.makedirs(os.path.dirname(os.path.abspath(opts["json"])), exist_ok=True)
        with open(opts["json"], "w") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
