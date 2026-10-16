"""Tests for skills/3d/assets/blender: inspect_scene.py, export_web.py, render_shots.py.

Skipped (with reason) when `blender` is not on PATH. Run: python3 -m unittest discover -s tests
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
SHOTS = ROOT / "skills" / "3d" / "assets" / "templates" / "shots.json"
BLENDER = shutil.which("blender")
GLTF_TRANSFORM = shutil.which("gltf-transform")

BUILD = """
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
a = bpy.context.object; a.name = "Hero Root"
m = a.modifiers.new("Bev", "BEVEL"); m.width = 0.1; m.segments = 3
bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0.5))
b = bpy.context.object; b.name = "Extra"
bpy.ops.object.select_all(action="SELECT")  # Extra stays selected in the saved file
bpy.ops.wm.save_as_mainfile(filepath=%r)
"""


def last_json(out: str) -> dict:
    lines = [ln for ln in out.splitlines() if ln.startswith("{")]
    return json.loads(lines[-1])


@unittest.skipUnless(BLENDER, "blender not on PATH")
class BlenderScripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.blend = cls.tmp / "scene.blend"
        build = cls.tmp / "build.py"
        build.write_text(BUILD % str(cls.blend))
        cls.bl(None, "--python", str(build))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def bl(cls, blend, *args, check=True):
        cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1"]
        if blend:
            cmd.append(str(blend))
        cmd += list(args)
        return subprocess.run(cmd, capture_output=True, text=True, cwd=cls.tmp, timeout=600)

    def test_inspect_scene(self):
        out = self.tmp / "new" / "deep" / "inspect.json"  # parent dirs are created
        r = self.bl(self.blend, "--python", str(BPY / "inspect_scene.py"), "--", "--json", str(out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rep = json.loads(out.read_text())
        self.assertEqual(rep["summary"]["meshes"], 2)
        self.assertGreater(rep["summary"]["tris"], 0)

    def test_inspect_usage_exit_2(self):
        r = self.bl(self.blend, "--python", str(BPY / "inspect_scene.py"), "--", "--bogus")
        self.assertEqual(r.returncode, 2)

    def test_export_web_root_regression(self):
        """--root must export only the root hierarchy even with another object pre-selected."""
        glb = self.tmp / "out" / "hero.glb"
        r = self.bl(self.blend, "--python", str(BPY / "export_web.py"), "--", "--out", str(glb),
                    "--root", "Hero Root")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertTrue(res["ok"])
        self.assertEqual(res["glb"]["meshes"], 1, res)
        self.assertTrue(any("Bev" in a for a in res["applied"]))
        if GLTF_TRANSFORM:
            v = subprocess.run([GLTF_TRANSFORM, "validate", str(glb)], capture_output=True, text=True)
            self.assertIn("No errors found", v.stdout + v.stderr)

    def test_export_web_whole_scene(self):
        glb = self.tmp / "n3" / "x" / "all.glb"
        r = self.bl(self.blend, "--python", str(BPY / "export_web.py"), "--", "--out", str(glb))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(last_json(r.stdout)["glb"]["meshes"], 2)

    def test_export_usage_exit_2(self):
        r = self.bl(self.blend, "--python", str(BPY / "export_web.py"), "--")
        self.assertEqual(r.returncode, 2)

    def test_render_shots_still(self):
        out = self.tmp / "new2" / "render"  # parent dirs are created
        r = self.bl(self.blend, "--python", str(BPY / "render_shots.py"), "--", "--shots", str(SHOTS),
                    "--out", str(out), "--engine", "workbench", "--res", "160")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertTrue(res["ok"], res)
        self.assertEqual(len(res["files"]), 3)
        self.assertTrue((out / "S01.png").exists())


if __name__ == "__main__":
    unittest.main()
