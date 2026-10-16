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

    def test_render_shots_t_sets_frame(self):
        """`t` moves the scene clock: a cube animated across the view renders differently at t=0 and t=1."""
        anim = self.tmp / "anim.py"
        anim.write_text("""
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2, location=(-3, 0, 1))
c = bpy.context.object
c.keyframe_insert("location", frame=0)
c.location = (3, 0, 1)
c.keyframe_insert("location", frame=30)
bpy.ops.wm.save_as_mainfile(filepath=%r)
""" % str(self.tmp / "anim.blend"))
        self.bl(None, "--python", str(anim))
        shots = self.tmp / "t.json"
        base = {"focal_mm": 35, "position": [0, 1, 9], "target": [0, 1, 0]}
        shots.write_text(json.dumps({"schema": "shots.v1", "aspect": "16:9", "fps": 30, "shots": [
            dict(base, id="A", t=0), dict(base, id="B", t=1)]}))
        out = self.tmp / "tr"
        r = self.bl(self.tmp / "anim.blend", "--python", str(BPY / "render_shots.py"), "--", "--shots",
                    str(shots), "--out", str(out), "--engine", "workbench", "--res", "160")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotEqual((out / "A.png").read_bytes(), (out / "B.png").read_bytes())

    def test_render_shots_cycles_twin(self):
        """--import GLB + --world HDR renders under Cycles; the GLB light survives the round trip."""
        mk = self.tmp / "mk_twin.py"
        glb, hdr = self.tmp / "twin.glb", self.tmp / "env.hdr"
        mk.write_text("""
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
d = bpy.data.lights.new("Pt", "POINT"); d.energy = 1000
o = bpy.data.objects.new("Pt", d); o.location = (3, -3, 4)
bpy.context.scene.collection.objects.link(o)
bpy.ops.export_scene.gltf(filepath=%r, export_lights=True)
img = bpy.data.images.new("e", 64, 32, float_buffer=True)
img.pixels = [0.6] * (64 * 32 * 4)
img.filepath_raw = %r
img.file_format = "HDR"
img.save()
""" % (str(glb), str(hdr)))
        self.bl(None, "--python", str(mk))
        self.assertTrue(glb.exists() and hdr.exists())
        shots = self.tmp / "twin_shots.json"
        shots.write_text(json.dumps({"schema": "shots.v1", "aspect": "16:9", "fps": 30, "shots": [
            {"id": "T1", "fov": 35, "position": [5, 3, 7], "target": [0, 1, 0]}]}))
        out = self.tmp / "twin"
        r = self.bl(None, "--python", str(BPY / "render_shots.py"), "--", "--shots", str(shots), "--out",
                    str(out), "--engine", "cycles", "--samples", "4", "--res", "128", "--import", str(glb),
                    "--world", str(hdr), "--world-strength", "0.5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertEqual(res["engine"], "CYCLES")
        png = (out / "T1.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreater(len(png), 1500)  # not a blank frame

    def test_render_shots_missing_import_exit_2(self):
        r = self.bl(None, "--python", str(BPY / "render_shots.py"), "--", "--shots", str(SHOTS), "--out",
                    str(self.tmp / "x"), "--import", str(self.tmp / "nope.glb"))
        self.assertEqual(r.returncode, 2)

    def _gn_scene(self, extra=""):
        script = self.tmp / "gn_scene.py"
        blend = self.tmp / "gn_scene.blend"
        script.write_text("""
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=0.2); src = bpy.context.object; src.name = "src"
bpy.ops.mesh.primitive_plane_add(size=0.01); gn = bpy.context.object; gn.name = "GN"
md = gn.modifiers.new("GN", "NODES"); ng = bpy.data.node_groups.new("A", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput")
ml = ng.nodes.new("GeometryNodeMeshLine"); ml.inputs["Count"].default_value = 4
ml.inputs["Offset"].default_value = (0.3, 0, 0)
iop = ng.nodes.new("GeometryNodeInstanceOnPoints"); oi = ng.nodes.new("GeometryNodeObjectInfo")
oi.inputs[0].default_value = src; oi.transform_space = "RELATIVE"
ng.links.new(ml.outputs[0], iop.inputs["Points"]); ng.links.new(oi.outputs["Geometry"], iop.inputs["Instance"])
ng.links.new(iop.outputs[0], go.inputs[0]); md.node_group = ng
m = bpy.data.materials.new("Glass"); m.use_nodes = True
v = m.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
out = [n for n in m.node_tree.nodes if n.type == "OUTPUT_MATERIAL"][0]
m.node_tree.links.new(v.outputs[0], out.inputs["Volume"]); gn.data.materials.append(m)
d = bpy.data.lights.new("Pt", "POINT"); d.energy = 1000
lo = bpy.data.objects.new("Pt", d); bpy.context.scene.collection.objects.link(lo)
cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd)
bpy.context.scene.collection.objects.link(co)
bpy.ops.wm.save_as_mainfile(filepath=%r)
""" % str(blend))
        self.bl(None, "--python", str(script))
        return blend

    def test_export_web_defaults(self):
        """Defaults: COMPAT lights (1000 W -> 79.58), lights and cameras on, warnings for the
        volume material without a Material Output group and for the instance source."""
        blend = self._gn_scene()
        glb = self.tmp / "d" / "defaults.glb"
        r = self.bl(blend, "--python", str(BPY / "export_web.py"), "--", "--out", str(glb))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertEqual(res["glb"]["cameras"], 1)
        self.assertEqual(res["glb"]["lights"], 1)
        text = " ".join(res["warnings"])
        self.assertIn("glTF Material Output", text)
        self.assertIn("instance source", text)
        import struct
        data = glb.read_bytes()
        n = struct.unpack("<I", data[12:16])[0]
        doc = json.loads(data[20:20 + n])
        light = doc["extensions"]["KHR_lights_punctual"]["lights"][0]
        self.assertAlmostEqual(light["intensity"], 1000 / (4 * 3.14159265), delta=0.5)

    def test_export_web_gn_instances(self):
        blend = self._gn_scene()
        glb = self.tmp / "d" / "inst.glb"
        r = self.bl(blend, "--python", str(BPY / "export_web.py"), "--", "--out", str(glb),
                    "--gn-instances", "--no-lights", "--no-cameras", "--lighting", "spec")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertIn("EXT_mesh_gpu_instancing", res["glb"]["extensionsUsed"])
        self.assertEqual(res["glb"]["cameras"], 0)
        self.assertEqual(res["glb"]["lights"], 0)
        self.assertNotIn("instance source", " ".join(res["warnings"]))
        self.assertNotIn("src", res["glb"]["node_names"])  # the source cube is not exported


if __name__ == "__main__":
    unittest.main()
