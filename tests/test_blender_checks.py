"""Tests for skills/3d/assets/blender: uv_check.py and rig_check.py.

Each test builds a tiny .blend in a scratch dir that triggers one check, runs the script
headless and reads the JSON line. Skipped (with reason) when `blender` is not on PATH.
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BPY = ROOT / "skills" / "3d" / "assets" / "blender"
BLENDER = shutil.which("blender")

PRE = """
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
def cube(name, loc=(0, 0, 0), size=2):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    ob = bpy.context.object; ob.name = name
    return ob
def unwrap(ob):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.select_set(False)
def rig(mesh, names=("Root", "Tip")):
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.object; arm.name = "Rig"
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    eb[0].name = names[0]; eb[0].head = (0, 0, -1); eb[0].tail = (0, 0, 0)
    b = eb.new(names[1]); b.head = (0, 0, 0); b.tail = (0, 0, 1); b.parent = eb[0]
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm
def weighted_rig(mesh):
    arm = rig(mesh)
    mesh.parent = arm
    mesh.modifiers.new("Armature", "ARMATURE").object = arm
    g0 = mesh.vertex_groups.new(name="Root"); g1 = mesh.vertex_groups.new(name="Tip")
    for v in mesh.data.vertices:
        t = 1.0 if v.co.z > 0 else 0.0
        g0.add([v.index], 1.0 - t, "REPLACE"); g1.add([v.index], t, "REPLACE")
    return arm
"""


def last_json(out: str) -> dict:
    lines = [ln for ln in out.splitlines() if ln.startswith("{")]
    return json.loads(lines[-1])


@unittest.skipUnless(BLENDER, "blender not on PATH")
class BlenderChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def blend(self, name, body):
        """Build a .blend from `body` (bpy code) and return its path."""
        path = self.tmp / (name + ".blend")
        script = self.tmp / (name + "_build.py")
        script.write_text(PRE + body + "\nbpy.ops.wm.save_as_mainfile(filepath=%r)\n" % str(path))
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1",
                            "--python", str(script)], capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-800:])
        return path

    def run_check(self, blend, script, *args):
        cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1"]
        if blend:
            cmd.append(str(blend))
        cmd += ["--python", str(BPY / script), "--"] + list(args)
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp, timeout=300)
        return r, last_json(r.stdout) if '{"ok"' in r.stdout else None

    @staticmethod
    def level(rep, check, obj=None):
        return [i["level"] for i in rep["items"]
                if i["check"] == check and (obj is None or i["object"] == obj)]

    # ---- uv_check ----
    def test_uv_clean_cube_passes(self):
        b = self.blend("uv_ok", "unwrap(cube('A'))")
        r, rep = self.run_check(b, "uv_check.py", "--res", "1024")
        self.assertEqual(r.returncode, 0, r.stdout[-600:])
        self.assertTrue(rep["ok"])
        self.assertEqual(self.level(rep, "overlap"), ["PASS"])
        self.assertEqual(self.level(rep, "bounds"), ["PASS"])

    def test_uv_overlap_fails(self):
        b = self.blend("uv_overlap", """
ob = cube('A'); unwrap(ob)
uv = ob.data.uv_layers.active.data
for p in ob.data.polygons:
    for k, li in enumerate(p.loop_indices):
        uv[li].uv = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)][k]
""")
        r, rep = self.run_check(b, "uv_check.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.level(rep, "overlap"))

    def test_uv_out_of_bounds_warns(self):
        b = self.blend("uv_oob", """
ob = cube('A'); unwrap(ob)
for d in ob.data.uv_layers.active.data:
    d.uv = (d.uv[0] + 2.0, d.uv[1])
""")
        r, rep = self.run_check(b, "uv_check.py")
        self.assertIn("WARN", self.level(rep, "bounds"))

    def test_uv_missing_map_fails(self):
        b = self.blend("uv_none", "o = cube('A')\nwhile o.data.uv_layers: o.data.uv_layers.remove(o.data.uv_layers[0])")
        r, rep = self.run_check(b, "uv_check.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.level(rep, "uv-map"))

    def test_uv_lightmap_needs_second_layer(self):
        b = self.blend("uv_lm", "unwrap(cube('A'))")
        r, rep = self.run_check(b, "uv_check.py", "--lightmap")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.level(rep, "lightmap-uv"))

    def test_uv_density_spread_fails(self):
        b = self.blend("uv_dens", "unwrap(cube('Small')); unwrap(cube('Big', (6, 0, 0), size=6))")
        r, rep = self.run_check(b, "uv_check.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.level(rep, "density-spread"))

    def test_uv_target_density_warns(self):
        b = self.blend("uv_target", "unwrap(cube('A'))")
        r, rep = self.run_check(b, "uv_check.py", "--target", "100000")
        self.assertIn("WARN", self.level(rep, "target-density"))

    def test_uv_margin_warns(self):
        b = self.blend("uv_margin", """
ob = cube('A')
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(island_margin=0.0)
bpy.ops.object.mode_set(mode="OBJECT")
""")
        r, rep = self.run_check(b, "uv_check.py", "--min-margin", "40")
        self.assertIn("WARN", self.level(rep, "margin"))

    def test_uv_usage_exit_2(self):
        r, _ = self.run_check(None, "uv_check.py", "--bogus")
        self.assertEqual(r.returncode, 2)

    def test_uv_json_file_in_new_dir(self):
        b = self.blend("uv_json", "unwrap(cube('A'))")
        out = self.tmp / "new" / "deep" / "uv.json"
        self.run_check(b, "uv_check.py", "--json", str(out))
        self.assertTrue(json.loads(out.read_text())["ok"])

    # ---- rig_check ----
    def test_rig_clean_passes(self):
        b = self.blend("rig_ok", "weighted_rig(cube('Body'))")
        r, rep = self.run_check(b, "rig_check.py")
        self.assertEqual(r.returncode, 0, r.stdout[-800:])
        self.assertEqual(self.level(rep, "unweighted"), ["PASS"])
        self.assertEqual(self.level(rep, "armature-modifier"), ["PASS"])
        self.assertEqual(self.level(rep, "deform-bones"), ["PASS"])

    def test_rig_unweighted_fails(self):
        b = self.blend("rig_unw", """
m = cube('Body'); weighted_rig(m)
for vg in m.vertex_groups:
    vg.remove(list(range(0, 3)))
""")
        r, rep = self.run_check(b, "rig_check.py")
        self.assertEqual(r.returncode, 1)
        msg = [i["message"] for i in rep["items"] if i["check"] == "unweighted"][0]
        self.assertTrue(msg.startswith("3 of"), msg)

    def test_rig_over_influences_fails(self):
        b = self.blend("rig_inf", """
m = cube('Body'); weighted_rig(m)
for i in range(5):
    m.vertex_groups.new(name="Extra%d" % i).add([0], 0.2, "REPLACE")
arm = bpy.data.objects['Rig']
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for i in range(5):
    e = arm.data.edit_bones.new("Extra%d" % i); e.head = (0, 0, i); e.tail = (0, 0, i + .5)
bpy.ops.object.mode_set(mode="OBJECT")
""")
        r, rep = self.run_check(b, "rig_check.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.level(rep, "influences"))
        r2, rep2 = self.run_check(b, "rig_check.py", "--max-influences", "8")
        self.assertEqual(self.level(rep2, "influences"), ["PASS"])

    def test_rig_non_normalised_warns(self):
        b = self.blend("rig_norm", """
m = cube('Body'); weighted_rig(m)
m.vertex_groups['Root'].add([0, 1], 1.0, "REPLACE")
m.vertex_groups['Tip'].add([0, 1], 1.0, "REPLACE")
""")
        r, rep = self.run_check(b, "rig_check.py")
        self.assertIn("WARN", self.level(rep, "normalised"))

    def test_rig_missing_modifier_fails(self):
        b = self.blend("rig_nomod", """
m = cube('Body'); weighted_rig(m)
m.modifiers.clear()
""")
        r, rep = self.run_check(b, "rig_check.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.level(rep, "armature-modifier"))

    def test_rig_scale_and_nondeform(self):
        b = self.blend("rig_scale", """
m = cube('Body'); arm = weighted_rig(m)
m.scale = (2, 2, 2)
arm.data.bones['Root'].use_deform = False
""")
        r, rep = self.run_check(b, "rig_check.py")
        self.assertIn("WARN", self.level(rep, "scale", "Body"))
        self.assertTrue(any(i["check"] == "vertex-groups" and "non-deform" in i["message"]
                            for i in rep["items"]))
        msg = [i["message"] for i in rep["items"] if i["check"] == "deform-bones"][0]
        self.assertTrue(msg.startswith("1 deform / 1 non-deform"), msg)

    def test_rig_no_armature_fails_and_usage(self):
        b = self.blend("rig_none", "cube('A')")
        r, rep = self.run_check(b, "rig_check.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", self.level(rep, "armature"))
        r, _ = self.run_check(None, "rig_check.py", "--bogus")
        self.assertEqual(r.returncode, 2)


@unittest.skipUnless(BLENDER, "blender not on PATH")
class Help(unittest.TestCase):
    def test_help_exit_0(self):
        for s in ("uv_check.py", "rig_check.py"):
            r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", str(BPY / s),
                                "--", "--help"], capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, s)
            self.assertIn("Args after", r.stdout)


if __name__ == "__main__":
    unittest.main()
