"""Tests for the texturing scripts in skills/3d/assets/blender:
texture_prep.py, material_from_maps.py, bake_maps.py.

Fixtures (textures, a test scene) are generated inside Blender, which ships numpy; no binary files are checked in.
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
BLENDER = shutil.which("blender")

# Run inside Blender: argv after `--` is the output directory.
FIXTURES = r'''
import sys, os
import bpy, numpy as np
out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out + "/sets/cg", exist_ok=True)
os.makedirs(out + "/sets/ph", exist_ok=True)
os.makedirs(out + "/sets/dup", exist_ok=True)
os.makedirs(out + "/sets/noalbedo", exist_ok=True)
n = 128
rng = np.random.default_rng(7)


def blur(a, s):
    fy = np.fft.fftfreq(a.shape[0])[:, None]
    fx = np.fft.fftfreq(a.shape[1])[None, :]
    return np.real(np.fft.ifft2(np.fft.fft2(a) * np.exp(-2 * np.pi ** 2 * s ** 2 * (fx ** 2 + fy ** 2))))


def norm(a):
    return (a - a.min()) / (a.max() - a.min())


def write(path, rgb):
    im = bpy.data.images.new("f", n, n, alpha=False)
    im.colorspace_settings.name = "Non-Color"
    arr = np.ones((n, n, 4), np.float32)
    arr[..., :3] = rgb
    im.pixels.foreach_set(arr.ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


noise = norm(blur(rng.random((n, n)), 2.0))
x = np.linspace(0, 1, n)[None, :]
y = np.linspace(0, 1, n)[:, None]
ramp = 0.55 * noise + 0.45 * (0.6 * x + 0.4 * y)  # organic detail on a ramp: does not tile
write(out + "/raw.png", np.stack([ramp, ramp * 0.8, ramp * 0.6], -1))
gray = np.stack([noise] * 3, -1)
color = np.stack([noise, noise * 0.7, noise * 0.5], -1)
for d, names in (("cg", ("Rock_2K-PNG_Color", "Rock_2K-PNG_NormalDX", "Rock_2K-PNG_Roughness", "Rock_2K-PNG_Metalness")),
                 ("ph", ("rock_diff_2k", "rock_nor_gl_2k", "rock_arm_2k", None))):
    write("%s/sets/%s/%s.png" % (out, d, names[0]), color)
    write("%s/sets/%s/%s.png" % (out, d, names[1]), np.stack([noise * 0.2 + 0.4, noise * 0.2 + 0.4, np.ones((n, n))], -1))
    write("%s/sets/%s/%s.png" % (out, d, names[2]), gray)
    if names[3]:
        write("%s/sets/%s/%s.png" % (out, d, names[3]), gray * 0.0)
    write("%s/sets/%s/notes_scan.png" % (out, d), gray)
write(out + "/sets/dup/rock_diff.png", color)
write(out + "/sets/dup/rock_color.png", color)
write(out + "/sets/noalbedo/rock_rough.png", gray)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2)
c = bpy.context.object
c.name = "Crate"
m = bpy.data.materials.new("M")
m.use_nodes = True
nt = m.node_tree
p = nt.nodes["Principled BSDF"]
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 8
nt.links.new(nz.outputs["Fac"], p.inputs["Roughness"])
p.inputs["Metallic"].default_value = 1.0
p.inputs["Base Color"].default_value = (0.8, 0.2, 0.1, 1)
c.data.materials.append(m)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(5, 0, 0))
hi = bpy.context.object
hi.name = "Hi"
tex = bpy.data.textures.new("t", "CLOUDS")
tex.noise_scale = 0.3
d = hi.modifiers.new("D", "DISPLACE")
d.texture = tex
d.strength = 0.08
bpy.ops.object.modifier_apply(modifier="D")
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8, location=(5, 0, 0))
bpy.context.object.name = "Lo"
bpy.ops.wm.save_as_mainfile(filepath=out + "/scene.blend")
'''

INSPECT = r'''
import json, bpy
mat = bpy.data.materials[%r]
nodes = mat.node_tree.nodes
imgs = {n.label: n.image.colorspace_settings.name for n in nodes if n.bl_idname == "ShaderNodeTexImage"}
mapping = next(n for n in nodes if n.bl_idname == "ShaderNodeMapping")
print(json.dumps({
    "images": imgs,
    "types": sorted({n.bl_idname for n in nodes}),
    "scale": list(mapping.inputs["Scale"].default_value),
    "projections": sorted({n.projection for n in nodes if n.bl_idname == "ShaderNodeTexImage"}),
    "assigned": [o.name for o in bpy.data.objects if any(s.material == mat for s in o.material_slots)],
    "bsdf_links": sorted(l.to_socket.name for l in mat.node_tree.links if l.to_node.bl_idname == "ShaderNodeBsdfPrincipled"),
}))
'''


def last_json(out: str) -> dict:
    lines = [ln for ln in out.splitlines() if ln.startswith("{")]
    return json.loads(lines[-1])


@unittest.skipUnless(BLENDER, "blender not on PATH")
class TextureScripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        gen = cls.tmp / "gen.py"
        gen.write_text(FIXTURES)
        r = cls.bl(None, "--python", str(gen), "--", str(cls.tmp))
        assert r.returncode == 0, r.stdout + r.stderr
        cls.raw = cls.tmp / "raw.png"
        cls.scene = cls.tmp / "scene.blend"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def bl(cls, blend, *args):
        cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1"]
        if blend:
            cmd.append(str(blend))
        cmd += list(args)
        return subprocess.run(cmd, capture_output=True, text=True, cwd=cls.tmp, timeout=900)

    def run_script(self, name, blend, *args):
        return self.bl(blend, "--python", str(BPY / name), "--", *map(str, args))

    # ---- texture_prep ---------------------------------------------------------------------------

    def test_tp_seam_fails_then_tile_passes(self):
        r = self.run_script("texture_prep.py", None, "--seam", self.raw)
        self.assertEqual(r.returncode, 1, r.stdout)
        before = last_json(r.stdout)["seam"]["ratio"]
        self.assertGreater(before, 1.3)
        out = self.tmp / "tp" / "tiled.png"
        r = self.run_script("texture_prep.py", None, "--tile", self.raw, "--out", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertTrue(out.exists())
        self.assertLess(res["seam"]["ratio"], before / 5)
        self.assertLessEqual(res["seam"]["ratio"], 1.3)
        r = self.run_script("texture_prep.py", None, "--seam", out)  # the file on disk, not the intermediate
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_tp_delight_reduces_low_frequency_luma(self):
        out = self.tmp / "tp" / "delit.png"
        r = self.run_script("texture_prep.py", None, "--delight", self.raw, "--out", out)
        res = last_json(r.stdout)
        self.assertTrue(out.exists())
        self.assertLess(res["lowfreq_after"], res["lowfreq_before"] * 0.5, res)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_tp_derive_maps(self):
        tiled = self.tmp / "tp" / "d_tiled.png"
        self.assertEqual(self.run_script("texture_prep.py", None, "--tile", self.raw, "--out", tiled).returncode, 0)
        d = self.tmp / "tp" / "derived"
        r = self.run_script("texture_prep.py", None, "--derive", tiled, "--out-dir", d, "--stem", "rock")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        for k in ("normal", "roughness", "height"):
            self.assertTrue(Path(res["maps"][k]).is_file(), k)
        nx, ny, nz = res["normal_mean"]
        self.assertAlmostEqual(nx, 0.5, delta=0.03)
        self.assertAlmostEqual(ny, 0.5, delta=0.03)
        self.assertGreater(nz, 0.8)
        self.assertLessEqual(res["normal_seam"]["ratio"], 1.3)
        lo, hi = res["roughness_range"]
        self.assertGreaterEqual(lo, 0.4 - 1e-3)
        self.assertLessEqual(hi, 0.9 + 1e-3)
        # the 16-bit normal reads back as a float image
        r = self.run_script("texture_prep.py", None, "--report", res["maps"]["normal"], "--max-seam", 5)
        self.assertTrue(last_json(r.stdout)["float"])

    def test_tp_usage_and_missing_file(self):
        self.assertEqual(self.run_script("texture_prep.py", None, "--bogus").returncode, 2)
        self.assertEqual(self.run_script("texture_prep.py", None).returncode, 2)
        self.assertEqual(self.run_script("texture_prep.py", None, "--tile", self.raw).returncode, 2)  # no --out
        self.assertEqual(self.run_script("texture_prep.py", None, "--help").returncode, 0)
        r = self.run_script("texture_prep.py", None, "--seam", self.tmp / "nope.png")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(last_json(r.stdout)["ok"])

    # ---- material_from_maps ---------------------------------------------------------------------

    def inspect(self, blend, material):
        f = self.tmp / "inspect.py"
        f.write_text(INSPECT % material)
        r = self.bl(blend, "--python", str(f))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return last_json(r.stdout)

    def test_mfm_ambientcg_set_dx_flip_and_preview(self):
        save = self.tmp / "mfm" / "cg.blend"
        prev = self.tmp / "mfm" / "cg.png"
        r = self.run_script("material_from_maps.py", self.scene, "--dir", self.tmp / "sets" / "cg", "--name", "CG",
                            "--object", "Crate", "--tile-m", 2, "--preview", prev, "--samples", 4, "--save", save)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertEqual(set(res["maps"]), {"albedo", "normal", "roughness", "metallic"})
        self.assertEqual(res["normal"], {"convention": "dx", "flipped": True})
        self.assertEqual(res["ignored"], ["notes_scan.png"])
        self.assertTrue(prev.is_file())
        self.assertFalse(res["preview"]["blank"])
        ins = self.inspect(save, "CG")
        self.assertEqual(ins["images"], {"albedo": "sRGB", "normal": "Non-Color", "roughness": "Non-Color",
                                        "metallic": "Non-Color"})
        self.assertIn("ShaderNodeCombineColor", ins["types"])  # the DX green flip
        self.assertIn("ShaderNodeNormalMap", ins["types"])
        self.assertEqual(ins["scale"], [0.5, 0.5, 0.5])
        self.assertEqual(ins["assigned"], ["Crate"])

    def test_mfm_polyhaven_packed_arm_and_box(self):
        save = self.tmp / "mfm" / "ph.blend"
        r = self.run_script("material_from_maps.py", self.scene, "--dir", self.tmp / "sets" / "ph", "--name", "PH",
                            "--box", 0.2, "--save", save)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertEqual(res["normal"], {"convention": "gl", "flipped": False})
        ins = self.inspect(save, "PH")
        self.assertIn("ShaderNodeSeparateColor", ins["types"])  # arm split
        self.assertNotIn("ShaderNodeCombineColor", ins["types"])
        self.assertEqual(ins["projections"], ["BOX"])
        self.assertTrue({"Base Color", "Roughness", "Metallic", "Normal"} <= set(ins["bsdf_links"]), ins)

    def test_mfm_failures(self):
        r = self.run_script("material_from_maps.py", self.scene, "--dir", self.tmp / "sets" / "noalbedo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no albedo", " ".join(last_json(r.stdout)["problems"]))
        r = self.run_script("material_from_maps.py", self.scene, "--dir", self.tmp / "sets" / "dup")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ambiguous", " ".join(last_json(r.stdout)["problems"]))
        self.assertEqual(self.run_script("material_from_maps.py", self.scene).returncode, 2)
        self.assertEqual(self.run_script("material_from_maps.py", self.scene, "--dir", self.tmp / "sets" / "cg",
                                         "--object", "Missing").returncode, 2)
        self.assertEqual(self.run_script("material_from_maps.py", self.scene, "--dir", self.tmp / "sets" / "cg",
                                         "--normal", "bogus").returncode, 2)

    # ---- bake_maps ------------------------------------------------------------------------------

    def bake(self, *args):
        return self.run_script("bake_maps.py", self.scene, "--res", 128, "--samples", 4, *args)

    def test_bake_pbr_maps_and_rebuild_export(self):
        out = self.tmp / "bake" / "crate"
        rebuilt = out / "crate.blend"
        r = self.bake("--object", "Crate", "--maps", "albedo,roughness,metallic,ao", "--out-dir", out,
                      "--rebuild", rebuilt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = last_json(r.stdout)
        maps = res["maps"]
        for k in ("albedo", "roughness", "metallic", "ao"):
            self.assertTrue(Path(maps[k]["path"]).is_file(), k)
        self.assertGreater(maps["roughness"]["std"], 0.01)  # noise-driven, not blank
        self.assertAlmostEqual(maps["metallic"]["mean"][0], maps["metallic"]["coverage"], delta=0.02)  # 1 where covered
        self.assertAlmostEqual(maps["albedo"]["mean"][0], 0.8 ** 0.4545 * maps["albedo"]["coverage"], delta=0.12)
        self.assertEqual(maps["albedo"]["colour_space"], "sRGB")
        self.assertEqual(maps["roughness"]["colour_space"], "Non-Color")
        self.assertEqual(res["rebuild"]["wired"], ["albedo", "roughness", "metallic"])
        self.assertTrue(rebuilt.is_file())
        glb = out / "crate.glb"
        r = self.run_script("export_web.py", rebuilt, "--out", glb, "--root", "Crate")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertGreaterEqual(last_json(r.stdout)["glb"]["images"], 2)

    def test_bake_hi_to_lo_normal(self):
        out = self.tmp / "bake" / "sphere"
        r = self.bake("--object", "Lo", "--high", "Hi", "--maps", "normal", "--out-dir", out,
                      "--extrusion", 0.1, "--ray", 0.2, "--margin", 4)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        n = last_json(r.stdout)["maps"]["normal"]
        self.assertTrue(Path(n["path"]).is_file())
        mx, my, mz = n["mean_covered"]
        self.assertAlmostEqual(mx, 0.5, delta=0.05)
        self.assertAlmostEqual(my, 0.5, delta=0.05)
        self.assertGreater(mz, 0.9)
        self.assertGreater(n["std"], 0.01)

    def test_bake_blank_map_exits_1(self):
        # Lo has no material and Hi's has none either: a base-colour bake is uniform black
        r = self.bake("--object", "Lo", "--maps", "albedo", "--out-dir", self.tmp / "bake" / "blank")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        res = last_json(r.stdout)
        self.assertFalse(res["ok"])
        self.assertIn("flat", " ".join(res["problems"]))
        r = self.bake("--object", "Lo", "--maps", "albedo", "--out-dir", self.tmp / "bake" / "blank2", "--allow-flat")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_bake_usage(self):
        self.assertEqual(self.run_script("bake_maps.py", self.scene).returncode, 2)
        self.assertEqual(self.bake("--object", "Nope", "--out-dir", self.tmp / "x").returncode, 2)
        self.assertEqual(self.bake("--object", "Crate", "--maps", "bogus", "--out-dir", self.tmp / "x").returncode, 2)
        self.assertEqual(self.run_script("bake_maps.py", self.scene, "--help").returncode, 0)

    # ---- shared -------------------------------------------------------------------------------

    def test_scripts_refuse_plain_python(self):
        for name in ("texture_prep.py", "material_from_maps.py", "bake_maps.py"):
            r = subprocess.run(["python3", str(BPY / name)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, name)
            self.assertIn("only inside Blender", r.stderr)


if __name__ == "__main__":
    unittest.main()
