"""Tests for skills/3d/scripts: glb-report, capabilities, ref-extract.

Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "3d" / "scripts"
FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


def run(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True,
                          cwd=cwd, timeout=300)


def png_bytes(w: int, h: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    raw = b"".join(b"\x00" + b"\x80\x40\x20" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def make_glb(path: Path, instances: int = 3, tex: tuple[int, int] = (4, 2)) -> None:
    """A quad (2 triangles, indexed), instanced `instances` times, one embedded PNG texture."""
    positions = struct.pack("<12f", 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0)
    indices = struct.pack("<6H", 0, 1, 2, 0, 2, 3)
    png = png_bytes(*tex)
    blob = positions + indices
    blob += b"\x00" * (-len(blob) % 4)
    png_off = len(blob)
    blob += png + b"\x00" * (-len(png) % 4)
    doc = {
        "asset": {"version": "2.0", "generator": "test"},
        "extensionsUsed": ["KHR_materials_unlit"],
        "scene": 0, "scenes": [{"nodes": list(range(instances))}],
        "nodes": [{"mesh": 0, "translation": [i, 0, 0]} for i in range(instances)],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
        "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
        "textures": [{"source": 0}],
        "images": [{"bufferView": 2, "mimeType": "image/png"}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions)},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(indices)},
            {"buffer": 0, "byteOffset": png_off, "byteLength": len(png)},
        ],
        "buffers": [{"byteLength": len(blob)}],
    }
    js = json.dumps(doc).encode()
    js += b" " * (-len(js) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
                     + struct.pack("<II", len(blob), 0x004E4942) + blob)


class GlbReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_numbers_and_pass(self) -> None:
        glb = self.tmp / "q.glb"
        make_glb(glb)
        res = run("glb-report", str(glb), "--json", "--budget", "hero")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["meshes"], 1)
        self.assertEqual(data["primitives"], 1)
        self.assertEqual(data["unique_triangles"], 2)
        self.assertEqual(data["triangles"], 6)
        self.assertEqual(data["draw_calls"], 3)
        self.assertEqual(data["materials"], 1)
        self.assertEqual(data["extensions_used"], ["KHR_materials_unlit"])
        tex = data["textures"][0]
        self.assertEqual((tex["width"], tex["height"], tex["format"]), (4, 2, "png"))
        self.assertEqual(data["verdict"], "PASS")

    def test_budget_fail_on_size(self) -> None:
        # 3 MB hero limit: pad the file past it via a huge unused buffer chunk
        glb = self.tmp / "big.glb"
        make_glb(glb)
        with glb.open("ab") as fh:
            fh.write(b"\x00" * (3 * 1024 * 1024 + 16))
        res = run("glb-report", str(glb), "--budget", "hero")
        self.assertEqual(res.returncode, 1)
        self.assertIn("FAIL", res.stdout)
        self.assertEqual(run("glb-report", str(glb), "--budget", "none").returncode, 0)

    def test_texture_warn_and_fail(self) -> None:
        glb = self.tmp / "t.glb"
        make_glb(glb, tex=(2048, 2))
        res = run("glb-report", str(glb), "--json", "--budget", "hero")
        self.assertEqual((res.returncode, json.loads(res.stdout)["verdict"]), (0, "WARN"))
        make_glb(glb, tex=(4096, 2))
        res = run("glb-report", str(glb), "--json", "--budget", "hero")
        self.assertEqual((res.returncode, json.loads(res.stdout)["verdict"]), (1, "FAIL"))

    def test_mobile_target_tightens(self) -> None:
        glb = self.tmp / "m.glb"
        make_glb(glb, instances=120)  # 120 draw calls: fine on desktop (<300), over mobile hero's 100
        desk = json.loads(run("glb-report", str(glb), "--json", "--budget", "hero").stdout)
        mob = json.loads(run("glb-report", str(glb), "--json", "--budget", "hero", "--target", "mobile").stdout)
        self.assertEqual(desk["verdict"], "PASS")
        self.assertEqual(mob["verdict"], "WARN")
        self.assertEqual(mob["target"], "mobile")

    def test_bad_file(self) -> None:
        bad = self.tmp / "bad.glb"
        bad.write_bytes(b"not a model")
        self.assertEqual(run("glb-report", str(bad)).returncode, 1)

    @unittest.skipUnless(shutil.which("gltf-transform"), "gltf-transform not installed")
    def test_cross_check_gltf_transform(self) -> None:
        glb = self.tmp / "q.glb"
        make_glb(glb, instances=3)
        res = subprocess.run(["gltf-transform", "inspect", str(glb), "--format", "csv"],
                             capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            self.skipTest(f"gltf-transform inspect failed: {res.stderr.strip()[:100]}")
        lines = res.stdout.splitlines()
        head = next((i for i, ln in enumerate(lines) if ln.startswith("#,name,mode,meshPrimitives")), None)
        if head is None:
            self.skipTest("gltf-transform inspect csv layout changed")
        cols = lines[head].split(",")
        row = lines[head + 1].split(",")
        mine = json.loads(run("glb-report", str(glb), "--json").stdout)
        self.assertEqual(int(row[cols.index("glPrimitives")]), mine["unique_triangles"])
        self.assertEqual(int(row[cols.index("instances")]), mine["draw_calls"])


class CapabilitiesTest(unittest.TestCase):
    def test_temp_project(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "package.json").write_text(json.dumps({
            "dependencies": {"three": "^0.186.0", "@react-three/fiber": "^9.0.0", "left-pad": "1.0.0"},
            "devDependencies": {"gsap": "^3.13.0"}}))
        (tmp / ".mcp.json").write_text(json.dumps({"mcpServers": {
            "blender": {"command": "SECRET-VALUE"}, "other": {"command": "x"}}}))
        res = run("capabilities", "--root", str(tmp), "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["stack"]["deps"]["three"], "^0.186.0")
        self.assertIn("@react-three/fiber", data["stack"]["deps"])
        self.assertIn("gsap", data["stack"]["deps"])
        self.assertNotIn("left-pad", data["stack"]["deps"])
        self.assertIn("python3", {t["cli"] for t in data["tools"] if t["found"]})
        mcp_project = [h for h in data["mcp"] if h["source"] == ".mcp.json"]
        self.assertEqual(mcp_project[0]["servers"], ["blender"])
        md = (tmp / ".3d" / "capabilities.md").read_text()
        self.assertIn("## Machine tools", md)
        self.assertNotIn("SECRET-VALUE", md + res.stdout)


@unittest.skipUnless(FFMPEG, "ffmpeg/ffprobe not installed")
class RefExtractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def ff(self, *args: str) -> None:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True, timeout=120)

    def test_image_and_video(self) -> None:
        img, vid = self.tmp / "ref.png", self.tmp / "clip.mp4"
        self.ff("-f", "lavfi", "-i", "testsrc=size=320x180", "-frames:v", "1", str(img))
        self.ff("-f", "lavfi", "-i", "testsrc=duration=3:size=320x180:rate=15", "-pix_fmt", "yuv420p", str(vid))
        out = self.tmp / "out"
        res = run("ref-extract", str(img), str(vid), "--out", str(out), "--frames", "4")
        self.assertEqual(res.returncode, 0, res.stderr)
        for name in ("meta.json", "contact.jpg", "palette.json", "luma.json"):
            self.assertTrue((out / "ref" / name).is_file(), name)
        for name in ("meta.json", "contact.jpg", "palette.json", "luma.json", "cuts.json", "motion.json"):
            self.assertTrue((out / "clip" / name).is_file(), name)
        self.assertEqual(len(list((out / "clip" / "frames").glob("*.jpg"))), 4)
        pal = json.loads((out / "clip" / "palette.json").read_text())["colors"]
        self.assertTrue(pal and all(c["hex"].startswith("#") and len(c["hex"]) == 7 for c in pal))
        self.assertAlmostEqual(sum(c["weight"] for c in pal), 1.0, places=1)
        luma = json.loads((out / "ref" / "luma.json").read_text())
        self.assertEqual(len(luma["histogram"]), 16)
        self.assertIn(luma["key"], ("low", "mid", "high"))
        motion = json.loads((out / "clip" / "motion.json").read_text())["samples"]
        self.assertGreater(len(motion), 10)

    def test_hard_cut_detected(self) -> None:
        vid = self.tmp / "cut.mp4"
        self.ff("-f", "lavfi", "-i", "color=red:size=160x90:rate=10:duration=1",
                "-f", "lavfi", "-i", "color=blue:size=160x90:rate=10:duration=1",
                "-filter_complex", "[0][1]concat=n=2:v=1:a=0", "-pix_fmt", "yuv420p", str(vid))
        out = self.tmp / "out"
        self.assertEqual(run("ref-extract", str(vid), "--out", str(out), "--frames", "3").returncode, 0)
        cuts = json.loads((out / "cut" / "cuts.json").read_text())["cuts"]
        self.assertTrue(any(0.8 < c < 1.2 for c in cuts), cuts)

    def test_missing_input_exit_1(self) -> None:
        res = run("ref-extract", str(self.tmp / "nope.png"), "--out", str(self.tmp / "o"))
        self.assertEqual(res.returncode, 1)


class RefExtractNoFfmpegTest(unittest.TestCase):
    def test_clear_error(self) -> None:
        import os
        env = {**os.environ, "PATH": "/nonexistent"}
        res = subprocess.run([sys.executable, str(SCRIPTS / "ref-extract"), "x.png"], capture_output=True,
                             text=True, env=env, timeout=60)
        self.assertEqual(res.returncode, 1)
        self.assertIn("ffmpeg", res.stderr)
        self.assertIn("install", res.stderr)


if __name__ == "__main__":
    unittest.main()
