"""Tests for skills/3d/scripts/preview (serve, new-version, capture, diff, feedback)."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import re
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


def http(url: str, data: dict | str | None = None, method: str | None = None, headers: dict | None = None):
    raw = data if isinstance(data, str) else (json.dumps(data) if data is not None else None)
    h = {"content-type": "application/json", **(headers or {})}
    h = {k: v for k, v in h.items() if v is not None}
    req = urllib.request.Request(url, data=raw.encode() if raw is not None else None, headers=h, method=method)
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
        cls.srv.server_close()
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
        (self.root / "feedback.jsonl").unlink(missing_ok=True)
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

    def test_save_shot_keeps_authored_fields_and_replaces_lens(self):
        (self.root / "shots.json").write_text(json.dumps({"schema": "shots.v1", "aspect": "21:9", "fps": 30, "shots": [
            {"id": "S01", "purpose": "establish", "focal_mm": 35, "position": [3, 1, 5], "target": [0, 0, 0],
             "to": {"position": [2, 1, 3]}, "ease": "out", "scroll": [0, 0.5]}]}))
        http(self.base + "/shots", {"id": "S01", "fov": 31.5, "position": [9, 9, 9], "target": [0, 1, 0]})
        data = json.loads((self.root / "shots.json").read_text())
        s = data["shots"][0]
        self.assertEqual((data["aspect"], data["fps"], data["schema"]), ("21:9", 30, "shots.v1"))
        self.assertNotIn("focal_mm", s)
        self.assertEqual(s["fov"], 31.5)
        self.assertEqual((s["purpose"], s["ease"], s["scroll"], s["to"]), ("establish", "out", [0, 0.5], {"position": [2, 1, 3]}))
        self.assertEqual(s["position"], [9, 9, 9])

    def test_name_alias_dropped(self):
        (self.root / "shots.json").write_text(json.dumps({"shots": [{"name": "x", "fov": 30, "position": [0, 0, 1], "target": [0, 0, 0]}]}))
        ids = [s["id"] for s in json.loads(http(self.base + "/api/state").read())["shots"]]
        self.assertEqual(ids, ["shot1"])

    def test_no_wildcard_cors_and_preflight_refused(self):
        r = http(self.base + "/api/state")
        self.assertIsNone(r.headers.get("Access-Control-Allow-Origin"))
        r = http(self.base + "/feedback", method="OPTIONS", headers={"Origin": "http://evil.example"})
        self.assertEqual(r.status, 403)
        self.assertIsNone(r.headers.get("Access-Control-Allow-Origin"))

    def test_host_rebinding_rejected(self):
        self.assertEqual(http(self.base + "/api/state", headers={"Host": "evil.example"}).status, 403)
        self.assertEqual(http(self.base + "/", headers={"Host": "evil.example:80"}).status, 403)
        port = self.srv.server_address[1]
        self.assertEqual(http(self.base + "/api/state", headers={"Host": f"localhost:{port}"}).status, 200)

    def test_cross_origin_post_rejected(self):
        body = {"version": "v001", "note": "x"}
        before = (self.root / "feedback.jsonl").read_text() if (self.root / "feedback.jsonl").exists() else ""
        r = http(self.base + "/feedback", body, headers={"Origin": "http://evil.example"})
        self.assertEqual(r.status, 403)
        r = http(self.base + "/feedback", body, headers={"Content-Type": "text/plain"})
        self.assertEqual(r.status, 415)
        after = (self.root / "feedback.jsonl").read_text() if (self.root / "feedback.jsonl").exists() else ""
        self.assertEqual(before, after)
        port = self.srv.server_address[1]
        ok = http(self.base + "/feedback", body, headers={"Origin": f"http://127.0.0.1:{port}"})
        self.assertEqual(ok.status, 200)

    def test_non_finite_json_rejected(self):
        for raw in ('{"id":"nan1","fov":30,"position":[1,2,Infinity],"target":[0,0,0]}',
                    '{"id":"nan2","fov":NaN,"position":[1,2,3],"target":[0,0,0]}',
                    '{"id":"nan3","fov":30,"position":[1,2,1e999],"target":[0,0,0]}'):
            self.assertEqual(http(self.base + "/shots", raw).status, 400, raw)
        sp = self.root / "shots.json"
        self.assertTrue(not sp.exists() or "Infinity" not in sp.read_text() and "NaN" not in sp.read_text())
        self.assertEqual(http(self.base + "/feedback", '{"version":"v001","note":"n","x":NaN,"y":0.5}').status, 400)

    def test_oversized_post_rejected(self):
        big = '{"version":"v001","note":"' + "a" * (21 * 1024 * 1024) + '"}'
        try:
            r = http(self.base + "/feedback", big)
            self.assertEqual(r.status, 413)
        except (urllib.error.URLError, ConnectionError, OSError):
            pass  # server closed the connection before we finished sending: also a rejection

    def test_nul_in_path_does_not_crash(self):
        self.assertEqual(http(self.base + "/%00").status, 404)
        self.assertEqual(http(self.base + "/api/state").status, 200)


class AllowOriginTests(unittest.TestCase):
    def test_opt_in_exact_origin(self):
        mod = load_module()
        tmp = Path(tempfile.mkdtemp())
        srv = mod.make_server(tmp, 0, allow_origin="http://localhost:3000")
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            r = http(base + "/feedback", method="OPTIONS", headers={"Origin": "http://localhost:3000"})
            self.assertEqual((r.status, r.headers["Access-Control-Allow-Origin"]), (204, "http://localhost:3000"))
            r = http(base + "/feedback", {"version": "v001", "note": "hi"}, headers={"Origin": "http://localhost:3000"})
            self.assertEqual((r.status, r.headers["Access-Control-Allow-Origin"]), (200, "http://localhost:3000"))
            r = http(base + "/feedback", {"version": "v001", "note": "hi"}, headers={"Origin": "http://localhost:3001"})
            self.assertEqual(r.status, 403)
        finally:
            srv.shutdown()
            srv.server_close()
            shutil.rmtree(tmp, ignore_errors=True)


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


class BridgeTests(unittest.TestCase):
    """Runs bridge.ts (transpiled with the repo's typescript) against real three cameras under node."""

    def test_roll_survives_frame_and_controls_update(self):
        node = shutil.which("node")
        nm = ROOT / "node_modules"
        if not node or not (nm / "typescript").is_dir() or not (nm / "three").is_dir():
            self.skipTest("node + repo node_modules (typescript, three) required: run npm install at the repo root")
        script = r"""
import ts from 'typescript'; import fs from 'node:fs'; import * as THREE from 'three';
const src = fs.readFileSync(process.argv[2], 'utf8');
const js = ts.transpileModule(src, { compilerOptions: { module: 'ESNext', target: 'ES2022' } }).outputText;
globalThis.window = { location: { search: '?3d-preview' } };
globalThis.document = { visibilityState: 'visible' };
const out = new URL('./bridge.mjs', import.meta.url);
fs.writeFileSync(out, js);
const { installBridge } = await import(out.href);
const camera = new THREE.PerspectiveCamera(35, 16 / 9, 0.1, 100);
const rolls = [];
const gl = { render: (s, c) => { const up = new THREE.Vector3(0, 1, 0).applyQuaternion(c.quaternion); rolls.push(Math.atan2(-up.x, up.y) * 180 / Math.PI); },
  domElement: { toDataURL: () => 'data:image/png;base64,', width: 1, height: 1 }, info: { render: {}, memory: {} }, getContext: () => ({}) };
const target = new THREE.Vector3();
const controls = { target: { set: (x, y, z) => target.set(x, y, z) }, update: () => camera.lookAt(target) }; // like OrbitControls: re-aims, drops roll
installBridge({ gl, scene: new THREE.Scene(), camera, controls, shots: [{ id: 'a', position: [0, 0, 5], target: [0, 0, 0], fov: 30, roll_deg: 20, to: { roll_deg: 40 } }] });
window.__3d.setShot('a'); window.__3d.frame(5); window.__3d.capture();
window.__3d.setShot('a', 1); window.__3d.frame(5);
const after = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
console.log(JSON.stringify({ rolls, afterRoll: Math.atan2(-after.x, after.y) * 180 / Math.PI }));
"""
        # unique scratch dir inside the repo so node resolves node_modules; no shared file names between runs
        work = Path(tempfile.mkdtemp(prefix=".rolltest-", dir=ROOT))
        try:
            (work / "roll.mjs").write_text(script)
            r = subprocess.run([node, str(work / "roll.mjs"), str(ROOT / "skills/3d/assets/web/bridge.ts")], cwd=work,
                               capture_output=True, text=True, timeout=60)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        if r.returncode != 0 and re.search(r"ERR_MODULE_NOT_FOUND|ERR_UNSUPPORTED_RESOLVE_REQUEST|Cannot find (package|module)", r.stderr):
            self.skipTest("node could not resolve typescript/three here: " + r.stderr.strip().splitlines()[-1][:200])
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertGreaterEqual(len(out["rolls"]), 3)
        self.assertAlmostEqual(out["rolls"][0], 20, delta=0.5)   # rendered with roll after setShot + frame(5)
        self.assertAlmostEqual(out["rolls"][-1], 40, delta=0.5)  # end pose roll at t=1
        self.assertAlmostEqual(out["afterRoll"], 0, delta=0.5)   # roll is undone after drawing (not accumulated)


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

    def test_capture_rejects_bad_version(self):
        r = cli("capture", "--version", "../../x", cwd=self.tmp)
        self.assertEqual(r.returncode, 2)

    def test_capture_no_versions_exit_one(self):
        r = cli("capture", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
