"""Tests for skills/3d/scripts/preview (serve, new-version, capture, diff, feedback)."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "skills" / "3d" / "scripts" / "preview"


def load_module():
    loader = importlib.machinery.SourceFileLoader("preview_cli", str(PREVIEW))
    spec = importlib.util.spec_from_loader("preview_cli", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def cube_glb() -> bytes:
    v = [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5), (-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)]
    i = [0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 3, 6, 2, 3, 7, 6, 0, 4, 7, 0, 7, 3, 1, 2, 6, 1, 6, 5]
    pb = b"".join(struct.pack("<3f", *p) for p in v)
    ib = struct.pack("<%dH" % len(i), *i)
    ib += b"\0" * ((4 - len(ib) % 4) % 4)
    bin_ = pb + ib
    j = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
         "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [.8, .3, .2, 1], "metallicFactor": .2, "roughnessFactor": .4}}],
         "buffers": [{"byteLength": len(bin_)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pb)}, {"buffer": 0, "byteOffset": len(pb), "byteLength": len(i) * 2}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3", "min": [-.5] * 3, "max": [.5] * 3},
                       {"bufferView": 1, "componentType": 5123, "count": len(i), "type": "SCALAR"}]}
    js = json.dumps(j).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(bin_), b"BIN\0") + bin_)


def cli(*args: str, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PREVIEW), *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)


def http(url: str, data: dict | None = None, method: str | None = None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"content-type": "application/json"}, method=method)
    try:
        return urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as e:
        return e


class ServeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()
        cls.tmp = Path(tempfile.mkdtemp())
        cls.root = cls.tmp / ".3d"
        (cls.root / "versions" / "v001").mkdir(parents=True)
        (cls.root / "versions" / "v001" / "manifest.json").write_text(json.dumps({"version": "v001", "files": ["a.glb"]}))
        for name, data in {"a.glb": cube_glb(), "b.ktx2": b"x", "c.hdr": b"x", "d.wasm": b"\0asm", "e.gltf": b"{}", "f.bin": b"x", "g.exr": b"x"}.items():
            (cls.root / "versions" / "v001" / name).write_bytes(data)
        cls.srv = cls.mod.make_server(cls.root, 0)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_binds_loopback_only(self):
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")

    def test_viewer_served_at_root(self):
        r = http(self.base + "/")
        body = r.read().decode()
        self.assertEqual(r.status, 200)
        self.assertIn("text/html", r.headers["Content-Type"])
        self.assertIn("window.__3d", body)
        self.assertIn("three@0.186.1", body)
        self.assertEqual(r.headers["Cache-Control"], "no-store")

    def test_mime_types(self):
        expect = {"a.glb": "model/gltf-binary", "b.ktx2": "image/ktx2", "c.hdr": "application/octet-stream",
                  "d.wasm": "application/wasm", "e.gltf": "model/gltf+json", "f.bin": "application/octet-stream",
                  "g.exr": "application/octet-stream", "manifest.json": "application/json"}
        for name, mime in expect.items():
            r = http(f"{self.base}/versions/v001/{name}")
            self.assertEqual(r.status, 200, name)
            self.assertEqual(r.headers["Content-Type"], mime, name)
            self.assertEqual(r.headers["Cache-Control"], "no-store", name)

    def test_path_traversal_blocked(self):
        for p in ("/../../etc/passwd", "/%2e%2e/%2e%2e/etc/passwd", "/versions/../../preview"):
            r = http(self.base + p)
            self.assertEqual(r.status, 404, p)

    def test_api_state_lists_versions(self):
        st = json.loads(http(self.base + "/api/state").read())
        self.assertEqual([v["id"] for v in st["versions"]], ["v001"])
        self.assertIn("a.glb", st["versions"][0]["files"])

    def test_feedback_round_trip(self):
        r = http(self.base + "/feedback", {"version": "v001", "shot": "hero", "x": 0.31, "y": 0.22, "note": "rim too hot"})
        rec = json.loads(r.read())
        self.assertEqual((rec["version"], rec["shot"], rec["note"], rec["kind"]), ("v001", "hero", "rim too hot", "note"))
        r = http(self.base + "/feedback", {"version": "v001", "shot": "", "status": "approved", "note": ""})
        self.assertEqual(json.loads(r.read())["kind"], "status")
        lines = (self.root / "feedback.jsonl").read_text().splitlines()
        recs = [json.loads(l) for l in lines]
        self.assertEqual([x["id"] for x in recs], ["f0001", "f0002"])
        self.assertEqual((recs[0]["x"], recs[0]["y"]), (0.31, 0.22))
        self.assertEqual(recs[1]["status"], "approved")
        for key in ("ts", "version", "shot", "note"):
            self.assertIn(key, recs[0])
        st = json.loads(http(self.base + "/api/state").read())
        self.assertEqual(len(st["feedback"]), 2)

    def test_feedback_validation(self):
        for bad in ({"version": "x", "note": "n"}, {"version": "v001"}, {"version": "v001", "note": "n", "x": 2, "y": 0.5},
                    {"version": "v001", "status": "maybe"}):
            self.assertEqual(http(self.base + "/feedback", bad).status, 400, bad)

    def test_save_shot_merges_shots_v1(self):
        (self.root / "shots.json").unlink(missing_ok=True)
        r = http(self.base + "/shots", {"id": "hero", "fov": 40, "position": [1, 2, 3], "target": [0, 0, 0]})
        self.assertEqual(r.status, 200)
        http(self.base + "/shots", {"id": "top", "fov": 50, "position": [0, 4, 0], "target": [0, 0, 0], "roll_deg": 5})
        http(self.base + "/shots", {"id": "hero", "fov": 25, "position": [1, 2, 3], "target": [0, 0, 0]})
        data = json.loads((self.root / "shots.json").read_text())
        self.assertEqual((data["schema"], data["aspect"]), ("shots.v1", "16:9"))
        self.assertEqual([s["id"] for s in data["shots"]], ["top", "hero"])
        self.assertEqual(data["shots"][1]["fov"], 25)
        self.assertEqual(data["shots"][0]["roll_deg"], 5)
        self.assertEqual(http(self.base + "/shots", {"id": "../x", "fov": 1, "position": [0, 0, 0], "target": [0, 0, 0]}).status, 400)
        self.assertEqual(http(self.base + "/shots", {"id": "a.b", "fov": 1, "position": [0, 0, 0], "target": [0, 0, 0]}).status, 400)
        self.assertEqual(http(self.base + "/shots", {"id": "ok", "fov": 1, "position": [0, 0], "target": [0, 0, 0]}).status, 400)
        # exactly one lens key
        both = {"id": "ok", "fov": 30, "focal_mm": 50, "position": [0, 0, 1], "target": [0, 0, 0]}
        self.assertEqual(http(self.base + "/shots", both).status, 400)
        self.assertEqual(http(self.base + "/shots", {"id": "ok", "position": [0, 0, 1], "target": [0, 0, 0]}).status, 400)
        self.assertEqual(http(self.base + "/shots", {"id": "orth", "ortho_height": 2, "position": [0, 0, 5], "target": [0, 0, 0]}).status, 200)

    def test_save_shot_keeps_focal_mm_and_authored_fields(self):
        (self.root / "shots.json").write_text(json.dumps({"schema": "shots.v1", "aspect": "21:9", "fps": 30, "shots": [
            {"id": "S01", "purpose": "establish", "focal_mm": 35, "position": [3, 1, 5], "target": [0, 0, 0],
             "to": {"position": [2, 1, 3]}, "ease": "out", "scroll": [0, 0.5]}]}))
        http(self.base + "/shots", {"id": "S01", "fov": 2 * 57.29577951308232 * __import__("math").atan(12 / 50), "position": [9, 9, 9], "target": [0, 1, 0]})
        data = json.loads((self.root / "shots.json").read_text())
        s = data["shots"][0]
        self.assertEqual(data["aspect"], "21:9")
        self.assertNotIn("fov", s)
        self.assertAlmostEqual(s["focal_mm"], 50, places=1)
        self.assertEqual((s["purpose"], s["ease"], s["scroll"], s["to"]), ("establish", "out", [0, 0.5], {"position": [2, 1, 3]}))
        self.assertEqual(s["position"], [9, 9, 9])

    def test_options_cors(self):
        r = http(self.base + "/feedback", method="OPTIONS")
        self.assertEqual(r.status, 204)
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "*")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_help_exit_zero(self):
        r = cli("--help", cwd=self.tmp)
        self.assertEqual(r.returncode, 0)
        for word in ("serve", "new-version", "capture", "diff", "feedback", "swiftshader"):
            self.assertIn(word, r.stdout)

    def test_usage_error_exit_two(self):
        self.assertEqual(cli("bogus", cwd=self.tmp).returncode, 2)

    def test_new_version_layout(self):
        r1 = cli("new-version", "--note", "blockout", cwd=self.tmp)
        r2 = cli("new-version", cwd=self.tmp)
        self.assertEqual((r1.returncode, r2.returncode), (0, 0), r1.stderr + r2.stderr)
        self.assertEqual(json.loads(r1.stdout)["version"], "v001")
        self.assertEqual(json.loads(r2.stdout)["version"], "v002")
        m = json.loads((self.tmp / ".3d" / "versions" / "v001" / "manifest.json").read_text())
        self.assertEqual((m["version"], m["note"], m["files"]), ("v001", "blockout", []))
        self.assertIn("created", m)

    def test_feedback_command_groups(self):
        d = self.tmp / ".3d"
        d.mkdir()
        rows = [{"id": "f0001", "ts": "t", "version": "v001", "shot": "hero", "note": "too dark", "x": 0.5, "y": 0.5, "kind": "note"},
                {"id": "f0002", "ts": "t", "version": "v001", "shot": "", "note": "", "status": "changes", "kind": "status"},
                {"id": "f0003", "ts": "t", "version": "v002", "shot": "top", "note": "ok", "kind": "note"}]
        (d / "feedback.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        out = cli("feedback", cwd=self.tmp).stdout
        self.assertIn("== v001  status: changes", out)
        self.assertIn("[hero]", out)
        self.assertIn("too dark", out)
        self.assertIn("== v002", out)
        only = cli("feedback", "--version", "v002", cwd=self.tmp).stdout
        self.assertNotIn("v001", only)
        self.assertEqual(len(json.loads(cli("feedback", "--json", cwd=self.tmp).stdout)), 3)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe not installed")
class DiffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, name: str, color: str, size: str = "320x180") -> Path:
        p = self.tmp / name
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={size}",
                        "-frames:v", "1", str(p)], check=True)
        return p

    def test_diff_files(self):
        a, b = self.make("a.png", "red"), self.make("b.png", "blue", "640x360")
        r = cli("diff", str(a), str(b), cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        self.assertLess(res["ssim"], 0.9)
        self.assertIsInstance(res["psnr_db"], float)
        for k in ("side_by_side", "blend", "difference"):
            self.assertTrue(Path(self.tmp, res[k]).is_file(), k)

    def test_diff_identical(self):
        a = self.make("a.png", "green")
        res = json.loads(cli("diff", str(a), str(a), cwd=self.tmp).stdout)
        self.assertAlmostEqual(res["ssim"], 1.0, places=3)
        self.assertTrue(res["identical"])
        self.assertIsNone(res["psnr_db"])

    def test_diff_versions(self):
        for v, c in (("v001", "red"), ("v002", "orange")):
            d = self.tmp / ".3d" / "evidence" / v
            d.mkdir(parents=True)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={c}:s=160x90",
                            "-frames:v", "1", str(d / "hero.png")], check=True)
        r = cli("diff", "v001", "v002", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        pairs = json.loads(r.stdout)["pairs"]
        self.assertEqual([p["shot"] for p in pairs], ["hero"])

    def test_missing_file_exit_one(self):
        self.assertEqual(cli("diff", "nope.png", "nada.png", cwd=self.tmp).returncode, 1)


def _chrome_and_playwright() -> str | None:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return "python playwright not installed"
    if not (Path("/Applications/Google Chrome.app").exists() or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
            or shutil.which("chrome")):
        return "Google Chrome not found"
    return None


class CaptureTests(unittest.TestCase):
    def setUp(self):
        reason = _chrome_and_playwright()
        if reason:
            self.skipTest(reason)
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_capture_every_shot(self):
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "cube.glb").write_bytes(cube_glb())
        shots = {"schema": "shots.v1", "aspect": "16:9", "shots": [
            {"id": "hero", "focal_mm": 50, "position": [2, 1.5, 2.5], "target": [0, 0, 0], "to": {"position": [-2, 1.5, 2.5], "focal_mm": 85}},
            {"id": "top", "fov": 50, "position": [0, 4, 0.1], "target": [0, 0, 0], "roll_deg": 10},
            {"id": "ortho", "ortho_height": 2.5, "position": [0, 0, 5], "target": [0, 0, 0]}]}
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps(shots))
        r = cli("capture", "--size", "640x360", "--settle", "10", "--end", cwd=self.tmp, timeout=180)
        if r.returncode != 0 and '"renderer"' in r.stdout and "no WebGL" in r.stdout:
            self.skipTest("headless GL unavailable here: " + r.stdout[-300:])
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr)
        rep = json.loads(r.stdout)
        print(f"\n[capture] renderer={rep['renderer']!r} flags={rep['flags']} software={rep['software']}")
        self.assertTrue(rep["renderer"])
        for sid in ("hero", "hero_end", "top", "ortho"):
            png = self.tmp / ".3d" / "evidence" / "v001" / f"{sid}.png"
            self.assertTrue(png.is_file(), sid)
            self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(rep["info"]["tris"], 12)
        a = (self.tmp / ".3d/evidence/v001/hero.png").read_bytes()
        b = (self.tmp / ".3d/evidence/v001/top.png").read_bytes()
        self.assertNotEqual(a, b, "setShot did not change the camera")
        end = (self.tmp / ".3d/evidence/v001/hero_end.png").read_bytes()
        self.assertNotEqual(a, end, "end pose `to` did not move the camera")
        self.assertEqual(rep["info"]["camera"], "orthographic")

    def test_capture_no_versions_exit_one(self):
        r = cli("capture", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
