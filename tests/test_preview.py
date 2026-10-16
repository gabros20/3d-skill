"""Tests for skills/3d/scripts/preview (serve, new-version, capture, diff, feedback)."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import socket
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


def animated_cube_glb() -> bytes:
    """The cube plus a 1 s translation animation (x: 0 -> 3) on its node."""
    base = cube_glb()
    jlen = struct.unpack("<I", base[12:16])[0]
    j = json.loads(base[20:20 + jlen])
    binoff = 20 + jlen + 8
    blen = struct.unpack("<I", base[20 + jlen:24 + jlen])[0]
    bin_ = base[binoff:binoff + blen]
    extra = struct.pack("<2f", 0.0, 1.0) + struct.pack("<6f", 0, 0, 0, 3, 0, 0)
    off = len(bin_)
    bin_ += extra
    j["buffers"][0]["byteLength"] = len(bin_)
    j["bufferViews"] += [{"buffer": 0, "byteOffset": off, "byteLength": 8}, {"buffer": 0, "byteOffset": off + 8, "byteLength": 24}]
    j["accessors"] += [{"bufferView": 2, "componentType": 5126, "count": 2, "type": "SCALAR", "min": [0.0], "max": [1.0]},
                       {"bufferView": 3, "componentType": 5126, "count": 2, "type": "VEC3"}]
    j["animations"] = [{"samplers": [{"input": 2, "output": 3, "interpolation": "LINEAR"}],
                        "channels": [{"sampler": 0, "target": {"node": 0, "path": "translation"}}]}]
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


class AppServeTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / ".3d"
        self.root.mkdir()
        (self.root / "secret.txt").write_text("project secret")
        self.app = self.tmp / "dist"
        (self.app / "sub").mkdir(parents=True)
        (self.app / "index.html").write_text("<title>app</title>")
        (self.app / "sub" / "x.js").write_text("export const a = 1")
        (self.tmp / "outside.txt").write_text("outside")
        self.srv = self.mod.make_server(self.root, 0, app_dir=self.app)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_serves_app_index_and_assets(self):
        r = http(self.base + "/app/")
        self.assertEqual((r.status, r.read()), (200, b"<title>app</title>"))
        r = http(self.base + "/app/sub/x.js")
        self.assertEqual((r.status, r.headers["Content-Type"]), (200, "text/javascript; charset=utf-8"))
        self.assertEqual(http(self.base + "/app/sub/").status, 404)
        self.assertEqual(http(self.base + "/").status, 200)  # viewer still at /

    def test_app_has_no_escape(self):
        for p in ("/app/../outside.txt", "/app/%2e%2e/outside.txt", "/app/..%2foutside.txt", "/app/%2e%2e/.3d/secret.txt", "/app/%00"):
            self.assertEqual(http(self.base + p).status, 404, p)
        self.assertEqual(http(self.base + "/app/secret.txt").status, 404)  # .3d is not part of the app dir

    def test_app_host_guard(self):
        self.assertEqual(http(self.base + "/app/", headers={"Host": "evil.example"}).status, 403)

    def test_app_absent_without_flag(self):
        tmp = Path(tempfile.mkdtemp())
        srv = self.mod.make_server(tmp, 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            self.assertEqual(http(f"http://127.0.0.1:{srv.server_address[1]}/app/").status, 404)
        finally:
            srv.shutdown()
            srv.server_close()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_serve_app_requires_index(self):
        r = cli("serve", "--app", str(self.tmp / "sub-missing"), cwd=self.tmp)
        self.assertEqual(r.returncode, 2)


class LookStateTests(unittest.TestCase):
    def test_state_exposes_look_json(self):
        mod = load_module()
        tmp = Path(tempfile.mkdtemp())
        (tmp / "look.json").write_text(json.dumps({"schema": "look.v1", "toneMapping": "agx", "exposure": 0.9,
                                                    "environment": "room", "background": "#101010"}))
        srv = mod.make_server(tmp, 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            st = json.loads(http(f"http://127.0.0.1:{srv.server_address[1]}/api/state").read())
            self.assertEqual(st["look"]["toneMapping"], "agx")
            (tmp / "look.json").unlink()
            st = json.loads(http(f"http://127.0.0.1:{srv.server_address[1]}/api/state").read())
            self.assertIsNone(st["look"])
        finally:
            srv.shutdown()
            srv.server_close()
            shutil.rmtree(tmp, ignore_errors=True)


class ServeStopTests(unittest.TestCase):
    def test_pidfile_and_stop(self):
        import time
        tmp = Path(tempfile.mkdtemp())
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0))
            port = sk.getsockname()[1]
        proc = subprocess.Popen([sys.executable, str(PREVIEW), "serve", "--port", str(port)], cwd=tmp,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            pf = tmp / ".3d" / "preview.pid"
            for _ in range(300):
                if pf.exists():
                    break
                time.sleep(0.1)
            info = json.loads(pf.read_text())
            self.assertEqual((info["pid"], info["port"]), (proc.pid, port))
            for _ in range(100):  # server may still be binding under load
                try:
                    if http(f"http://127.0.0.1:{port}/api/state").status == 200:
                        break
                except OSError:
                    time.sleep(0.1)
            r = cli("stop", cwd=tmp, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("stopped", r.stdout)
            proc.wait(timeout=30)
            self.assertFalse(pf.exists())
            out = proc.stdout.read()
            self.assertIn(str(proc.pid), out)
            self.assertIn(f"127.0.0.1:{port}", out)
            with self.assertRaises(OSError):
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state", timeout=2)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stdout.close()
            proc.stderr.close()
            shutil.rmtree(tmp, ignore_errors=True)

    def _start_serve(self, tmp: Path):
        import time
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0))
            port = sk.getsockname()[1]
        proc = subprocess.Popen([sys.executable, str(PREVIEW), "serve", "--port", str(port)], cwd=tmp,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(300):
            try:
                if http(f"http://127.0.0.1:{port}/api/state").status == 200:
                    break
            except OSError:
                time.sleep(0.1)
        return proc, port

    def _reap(self, *procs):
        for p in procs:
            if p.poll() is None:
                p.kill()
            p.wait()
            for f in (p.stdout, p.stderr):
                if f:
                    f.close()

    @unittest.skipUnless(shutil.which("lsof"), "lsof not installed")
    def test_stop_recovers_without_pid_file(self):
        tmp = Path(tempfile.mkdtemp())
        proc, port = self._start_serve(tmp)
        try:
            (tmp / ".3d" / "preview.pid").unlink()
            r = cli("stop", "--port", str(port), cwd=tmp, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("found by port", r.stdout)
            proc.wait(timeout=30)
            # same via a stale pid file and a port named in 3D.md instead of --port
            proc2, port2 = self._start_serve(tmp)
            (tmp / ".3d" / "preview.pid").write_text(json.dumps({"pid": 999999, "port": port2}))
            (tmp / "3D.md").write_text(f"preview at http://127.0.0.1:{port2}/\n")
            r = cli("stop", cwd=tmp, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("stale", r.stdout)
            proc2.wait(timeout=30)
            self._reap(proc2)
        finally:
            self._reap(proc)
            shutil.rmtree(tmp, ignore_errors=True)

    @unittest.skipUnless(shutil.which("lsof"), "lsof not installed")
    def test_stop_never_kills_unrelated_processes(self):
        tmp = Path(tempfile.mkdtemp())
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0))
            port = sk.getsockname()[1]
        impostor_src = (
            "import http.server, json, sys\n"
            "class H(http.server.BaseHTTPRequestHandler):\n"
            "    def do_GET(self):\n"
            "        b = json.dumps({'versions': [], 'shots': [], 'feedback': []}).encode()\n"
            "        self.send_response(200); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)\n"
            "    def log_message(self, *a): pass\n"
            f"http.server.HTTPServer(('127.0.0.1', {port}), H).serve_forever()\n")
        impostor = subprocess.Popen([sys.executable, "-c", impostor_src])
        sleeper = subprocess.Popen(["sleep", "60"])
        try:
            import time
            for _ in range(100):
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state", timeout=1)
                    break
                except OSError:
                    time.sleep(0.1)
            r = cli("stop", "--port", str(port), cwd=tmp, timeout=60)  # looks like a preview server, is not
            self.assertEqual(r.returncode, 1)
            self.assertIn("not touching it", r.stderr)
            self.assertIsNone(impostor.poll())
            # stale pid file pointing at a live unrelated process (pid reuse): left alone, file removed
            (tmp / ".3d").mkdir(exist_ok=True)
            (tmp / ".3d" / "preview.pid").write_text(json.dumps({"pid": sleeper.pid, "port": 1}))
            r = cli("stop", "--port", "1", cwd=tmp, timeout=60)
            self.assertEqual(r.returncode, 0)
            self.assertIsNone(sleeper.poll())
            self.assertFalse((tmp / ".3d" / "preview.pid").exists())
        finally:
            self._reap(impostor, sleeper)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_stop_without_server_and_stale_pid(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            self.assertEqual(cli("stop", "--port", "1", cwd=tmp).returncode, 0)
            (tmp / ".3d").mkdir()
            (tmp / ".3d" / "preview.pid").write_text(json.dumps({"pid": 999999, "port": 1}))
            r = cli("stop", "--port", "1", cwd=tmp)
            self.assertEqual(r.returncode, 0)
            self.assertFalse((tmp / ".3d" / "preview.pid").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


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
        for word in ("serve", "new-version", "capture", "diff", "feedback", "board", "stop", "--selftest", "swiftshader",
                     "--dir", "needs network"):
            self.assertIn(word, r.stdout)
        self.assertNotIn("--root", r.stdout)
        self.assertNotIn("skill root", r.stdout)

    def test_root_flag_is_gone(self):
        self.assertEqual(cli("new-version", "--root", "x", cwd=self.tmp).returncode, 2)

    def test_dir_flag_redirects_output(self):
        r = cli("new-version", "--dir", "work", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.tmp / "work" / "versions" / "v001" / "manifest.json").is_file())

    def test_selftest(self):
        r = cli("--selftest", cwd=self.tmp)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "preview selftest ok"), r.stderr)

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

    def test_new_version_snapshot(self):
        (self.tmp / "dist" / "assets").mkdir(parents=True)
        (self.tmp / "dist" / "index.html").write_text("x")
        (self.tmp / "dist" / "assets" / "a.js").write_text("y")
        (self.tmp / "model.glb").write_bytes(b"glTF")
        r = cli("new-version", "--note", "snap", "--snapshot", "model.glb", "dist", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        vdir = self.tmp / ".3d" / "versions" / "v001"
        self.assertTrue((vdir / "model.glb").is_file())
        self.assertTrue((vdir / "dist" / "assets" / "a.js").is_file())
        m = json.loads((vdir / "manifest.json").read_text())
        self.assertEqual(m["files"], ["dist/assets/a.js", "dist/index.html", "model.glb"])
        self.assertEqual(m["note"], "snap")

    def test_new_version_snapshot_missing_path_creates_nothing(self):
        r = cli("new-version", "--snapshot", "nope.glb", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertFalse((self.tmp / ".3d" / "versions").exists())

    def test_new_version_is_atomic_on_failure(self):
        (self.tmp / "ok.txt").write_text("x")
        (self.tmp / "bad").mkdir()
        os.symlink(self.tmp / "nowhere", self.tmp / "bad" / "dangling")  # copytree raises on the broken link
        r = cli("new-version", "--snapshot", "ok.txt", "bad", cwd=self.tmp)
        self.assertNotEqual(r.returncode, 0)
        vroot = self.tmp / ".3d" / "versions"
        self.assertEqual(sorted(p.name for p in vroot.iterdir()), [])  # no vNNN, no .tmp-vNNN
        ok = cli("new-version", cwd=self.tmp)
        self.assertEqual(json.loads(ok.stdout)["version"], "v001")

    def test_new_version_ignores_incomplete_dirs_for_numbering(self):
        vroot = self.tmp / ".3d" / "versions"
        (vroot / "v001").mkdir(parents=True)
        (vroot / "v001" / "manifest.json").write_text("{}")
        (vroot / "v002").mkdir()  # empty leftover with no manifest
        r = cli("new-version", cwd=self.tmp)
        self.assertEqual(json.loads(r.stdout)["version"], "v002")
        self.assertTrue((vroot / "v002" / "manifest.json").is_file())
        (vroot / "v003").mkdir()
        (vroot / "v003" / "stray.txt").write_text("x")  # non-empty, no manifest: refuse rather than clobber
        r = cli("new-version", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertTrue((vroot / "v003" / "stray.txt").exists())

    def test_new_version_sigint_leaves_nothing(self):
        import signal
        import time
        big = self.tmp / "big"
        big.mkdir()
        for i in range(400):
            (big / f"f{i}.bin").write_bytes(os.urandom(200_000))
        proc = subprocess.Popen([sys.executable, str(PREVIEW), "new-version", "--snapshot", str(big)], cwd=self.tmp,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        tmpdir = self.tmp / ".3d" / "versions" / ".tmp-v001"
        for _ in range(300):
            if tmpdir.exists() or proc.poll() is not None:
                break
            time.sleep(0.01)
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
        out, err = proc.communicate(timeout=60)
        vroot = self.tmp / ".3d" / "versions"
        names = sorted(p.name for p in vroot.iterdir())
        if proc.returncode == 0:  # finished before the signal landed: must be complete, never partial
            self.assertEqual(names, ["v001"])
            self.assertTrue((vroot / "v001" / "manifest.json").is_file())
        else:
            self.assertEqual(names, [], err)

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

    def test_diff_edges_ignores_lighting_not_geometry(self):
        def box(name: str, bg: str, fg: str, x: int) -> Path:
            p = self.tmp / name
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            f"color=c={bg}:s=320x180,drawbox=x={x}:y=50:w=100:h=80:color={fg}:t=fill", "-frames:v", "1", str(p)], check=True)
            return p
        a = box("a.png", "black", "white", 100)
        lit = box("b.png", "0x303030", "0xc0c0c0", 100)   # same geometry, different lighting
        moved = box("c.png", "black", "white", 170)        # same lighting, different geometry
        same = json.loads(cli("diff", "--edges", str(a), str(lit), "--out", str(self.tmp / "o1"), cwd=self.tmp).stdout)
        diff = json.loads(cli("diff", "--edges", str(a), str(moved), "--out", str(self.tmp / "o2"), cwd=self.tmp).stdout)
        self.assertTrue(same["edges"])
        self.assertGreater(same["ssim"], 0.99)  # identical edge maps
        self.assertLess(diff["ssim"], same["ssim"] - 0.005)  # a moved box changes the edges
        self.assertTrue(Path(same["difference"]).is_file())
        self.assertIn("edges", Path(same["difference"]).parts)
        plain = json.loads(cli("diff", str(a), str(lit), "--out", str(self.tmp / "o3"), cwd=self.tmp).stdout)
        self.assertFalse(plain["edges"])
        self.assertLess(plain["ssim"], 0.5)  # pixel diff is hurt by lighting; edge diff is not

    def test_board_contact_sheet_and_legend(self):
        for sid, c in (("S01", "red"), ("S02", "green"), ("S03", "blue"), ("S04", "yellow")):
            d = self.tmp / ".3d" / "evidence" / "v001"
            d.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={c}:s=320x180",
                            "-frames:v", "1", str(d / f"{sid}.png")], check=True)
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"shots": [{"id": i} for i in ("S04", "S01", "S02", "S03")]}))
        rows = [{"id": "f0001", "version": "v001", "shot": "S01", "note": "too red", "kind": "note", "x": 0.2, "y": 0.3},
                {"id": "f0002", "version": "v001", "shot": "S02", "note": "dull", "kind": "note"},
                {"id": "f0003", "version": "v001", "shot": "S02", "note": "fixed", "kind": "resolved", "refs": ["f0002"]},
                {"id": "f0004", "version": "v002", "shot": "S01", "note": "other version", "kind": "note"}]
        (self.tmp / ".3d" / "feedback.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        r = cli("board", "--version", "v001", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        legend = json.loads(r.stdout)
        png = self.tmp / ".3d" / "boards" / "v001.png"
        self.assertTrue(png.is_file())
        self.assertEqual([s["id"] for s in legend["shots"]], ["S04", "S01", "S02", "S03"])  # shots.json order
        self.assertEqual((legend["columns"], legend["rows"]), (3, 2))
        self.assertEqual([n["id"] for n in legend["open_notes"]], ["f0001"])
        self.assertTrue((self.tmp / ".3d" / "boards" / "v001.json").is_file())
        w, h = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(png)],
                                               capture_output=True, text=True).stdout.strip().split("x"))
        self.assertEqual((w, h), (3 * 480, 2 * 270))

    def test_board_without_evidence_exit_one(self):
        cli("new-version", cwd=self.tmp)
        self.assertEqual(cli("board", cwd=self.tmp).returncode, 1)

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
const times = [];
installBridge({ gl, scene: new THREE.Scene(), camera, controls, setTime: (t) => times.push(t), shots: [{ id: 'a', position: [0, 0, 5], target: [0, 0, 0], fov: 30, roll_deg: 20, t: 2, to: { roll_deg: 40, t: 4 } }, { id: 'b', position: [0, 0, 5], target: [0, 0, 0], fov: 30 }] });
window.__3d.setShot('a'); window.__3d.frame(5); window.__3d.capture();
window.__3d.setShot('a', 1); window.__3d.frame(5);
const after = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
window.__3d.setShot('b');
console.log(JSON.stringify({ times, rolls, afterRoll: Math.atan2(-after.x, after.y) * 180 / Math.PI }));
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
        self.assertEqual(out["times"], [2, 4])                   # setTime hook: start t, then end t; shot b has no t


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

    def test_capture_applies_shot_t_to_gltf_animation(self):
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "anim.glb").write_bytes(animated_cube_glb())
        cam = {"position": [0, 0, 8], "target": [1.5, 0, 0], "fov": 40}
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"schema": "shots.v1", "shots": [
            {"id": "t0", "t": 0, **cam}, {"id": "t1", "t": 1, **cam}, {"id": "hold", **cam}]}))
        r = cli("capture", "--size", "480x270", "--settle", "5", cwd=self.tmp, timeout=180)
        self.assertEqual(r.returncode, 0, r.stdout[-1200:] + r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual({e["id"]: e.get("t_seconds") for e in rep["shots"]}, {"t0": 0, "t1": 1, "hold": None})
        ev = self.tmp / ".3d" / "evidence" / "v001"
        self.assertNotEqual((ev / "t0.png").read_bytes(), (ev / "t1.png").read_bytes(), "t did not move the animation")

    def test_capture_clip_is_deterministic_and_steps_time(self):
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "anim.glb").write_bytes(animated_cube_glb())
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"schema": "shots.v1", "fps": 8, "shots": [
            {"id": "S01", "position": [0, 0, 8], "target": [1.5, 0, 0], "fov": 40}]}))
        frames = self.tmp / ".3d" / "evidence" / "v001" / "S01_clip"
        runs = []
        for _ in range(2):
            r = cli("capture", "--clip", "1", "--size", "320x180", "--force", cwd=self.tmp, timeout=240)
            self.assertEqual(r.returncode, 0, r.stdout[-1200:] + r.stderr)
            entry = json.loads(r.stdout)["shots"][0]
            self.assertEqual((entry["id"], entry["frames"], entry["fps"]), ("S01_clip", 8, 8))
            runs.append([f.read_bytes() for f in sorted(frames.glob("frame_*.png"))])
        self.assertEqual(len(runs[0]), 8)
        self.assertEqual(runs[0], runs[1], "clip capture is not deterministic")
        self.assertNotEqual(runs[0][0], runs[0][-1], "setTime did not step the animation")
        mp4 = self.tmp / ".3d" / "evidence" / "v001" / "S01_clip.mp4"
        self.assertTrue(mp4.is_file())
        if shutil.which("ffprobe"):
            out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                                  "stream=nb_read_frames,r_frame_rate", "-of", "json", str(mp4)], capture_output=True, text=True).stdout
            st = json.loads(out)["streams"][0]
            self.assertEqual((st["nb_read_frames"], st["r_frame_rate"]), ("8", "8/1"))

    def test_capture_refuses_to_overwrite_evidence(self):
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "cube.glb").write_bytes(cube_glb())
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"shots": [{"id": "S01", "position": [2, 1, 3], "target": [0, 0, 0], "fov": 35}]}))
        args = ("capture", "--size", "320x180", "--settle", "3")
        self.assertEqual(cli(*args, cwd=self.tmp, timeout=180).returncode, 0)
        shot = self.tmp / ".3d" / "evidence" / "v001" / "S01.png"
        before = shot.stat().st_mtime_ns
        r = cli(*args, cwd=self.tmp, timeout=180)
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stderr)
        self.assertIn("new version", r.stderr)
        self.assertEqual(shot.stat().st_mtime_ns, before)
        self.assertEqual(cli(*args, "--force", cwd=self.tmp, timeout=180).returncode, 0)
        self.assertGreater(shot.stat().st_mtime_ns, before)
        # clips are guarded separately: stills do not block the first clip, the second clip is refused
        clip = ("capture", "--clip", "0.25", "--fps", "4", "--size", "320x180")
        self.assertEqual(cli(*clip, cwd=self.tmp, timeout=180).returncode, 0)
        r = cli(*clip, cwd=self.tmp, timeout=180)
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stderr)

    def test_capture_clip_bad_seconds(self):
        cli("new-version", cwd=self.tmp)
        self.assertEqual(cli("capture", "--clip", "0", cwd=self.tmp).returncode, 2)

    def test_capture_rejects_bad_version(self):
        r = cli("capture", "--version", "../../x", cwd=self.tmp)
        self.assertEqual(r.returncode, 2)

    def test_capture_no_versions_exit_one(self):
        r = cli("capture", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
