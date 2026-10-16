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


class RoundsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.feas, self.rows, self.techs = self.mod.gold_rounds_fixture()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def verdict(self, n, rows=None, techs=None):
        return self.mod.rounds_verdict(self.feas, (rows or self.rows)[:n], self.techs if techs is None else techs)

    def test_gold_case_stops_at_r4_by_plateau(self):
        for n in (1, 2, 3):
            self.assertEqual(self.verdict(n)["verdict"], "continue", n)
        v = self.verdict(4)
        self.assertEqual((v["verdict"], v["rule"], v["version"]), ("stop", "S2", "v008"))
        self.assertEqual(v["best"], {"version": "v008", "round": 4, "avg": 1.5})
        self.assertEqual(v["failing"], ["lighting", "materials", "motion"])
        self.assertEqual([d["id"] for d in v["open_fixable"]], ["D1", "D2"])  # ranked by gain; D4 (T17) is tried out
        self.assertEqual([d["id"] for d in v["ceiling"]], ["D3"])
        self.assertEqual([t["technique"] for t in v["tried_out"]], ["T17"])

    def test_deterministic(self):
        self.assertEqual(json.dumps(self.verdict(4), sort_keys=True), json.dumps(self.verdict(4), sort_keys=True))

    def test_pass_s0(self):
        rows = [{**self.rows[3], "scores": {c: 2 for c in self.feas["ship_bar"] if c != "avg"}, "avg": 2.0}]
        self.assertEqual(self.verdict(1, rows)["rule"], "S0")
        self.assertEqual(self.verdict(1, rows)["verdict"], "pass")

    def test_s1_nothing_fixable(self):
        d = [{"id": "X", "category": "lighting", "label": "CEILING", "feature": "G1"},
             {"id": "Y", "category": "materials", "label": "ARTEFACT", "ref": "R2"}]
        rows = [{**self.rows[0], "defects": d}]
        self.assertEqual(self.verdict(1, rows)["rule"], "S1")

    def test_s1_when_only_fixable_is_tried_out(self):
        d = [{"id": "Y", "category": "lighting", "label": "FIXABLE", "technique": "T17", "gain": 1}]
        rows = [{**r, "defects": d} for r in self.rows]
        self.assertEqual(self.verdict(2, rows)["rule"], "S1")

    def test_s3_small_or_pipeline_changes(self):
        small = [{"id": "A", "category": "lighting", "label": "FIXABLE", "technique": "T1", "gain": 0.25}]
        self.assertEqual(self.verdict(1, [{**self.rows[0], "defects": small}])["rule"], "S3")
        pipe = [{"id": "A", "category": "lighting", "label": "FIXABLE", "technique": "T4", "gain": 1, "pipeline_change": True}]
        self.assertEqual(self.verdict(1, [{**self.rows[0], "defects": pipe}])["rule"], "S3")

    def test_s4_budget_non_converging(self):
        base = {c: 1 for c in self.feas["ship_bar"] if c != "avg"}
        d = [{"id": "A", "category": "lighting", "label": "FIXABLE", "technique": "T1", "gain": 1}]
        rows = []
        for n, bump in enumerate((0, 0.1, 0.0, 0.05), 1):  # slow creep that never plateaus by S2 (a category rises each time)
            sc = dict(base)
            sc["composition"] = 1 + 0.2 * n
            rows.append({"round": n, "version": f"v{n:03d}", "scores": sc, "defects": d})
        self.feas["budget"] = {"rounds": 3}
        v = self.verdict(4, rows, {})
        self.assertEqual(v["rule"], "S4")
        self.assertEqual(v["non_converging"], 3)

    def test_best_so_far_flag_when_regressing(self):
        rows = [dict(r) for r in self.rows[:4]]
        worse = {**rows[3], "round": 5, "version": "v010", "scores": {**rows[3]["scores"], "colour": 1, "fidelity": 1}, "avg": 1.17}
        v = self.mod.rounds_verdict(self.feas, rows + [worse], self.techs)
        self.assertEqual(v["best"]["version"], "v008")
        self.assertTrue(v["present_best_not_last"])

    def test_technique_that_raised_its_category_is_not_tried_out(self):
        rows = [dict(r) for r in self.rows[:4]]
        rows[1] = {**rows[1], "scores": {**rows[1]["scores"], "lighting": 2}}  # lighting rose in the 2nd version
        v = self.mod.rounds_verdict(self.feas, rows, {"v002": ["T17"], "v004": ["T17"]})
        self.assertEqual(v["tried_out"], [])

    def test_empty_rounds_continue(self):
        v = self.mod.rounds_verdict(self.feas, [], {})
        self.assertEqual((v["verdict"], v["rounds_used"]), ("continue", 0))

    def _write(self, rows=None, feas=None):
        d = self.tmp / ".3d"
        (d / "versions").mkdir(parents=True, exist_ok=True)
        (d / "feasibility.json").write_text(json.dumps(feas or self.feas))
        (d / "rounds.jsonl").write_text("\n".join(json.dumps(r) for r in (rows or self.rows[:4])) + "\n")
        for v, t in self.techs.items():
            (d / "versions" / v).mkdir()
            (d / "versions" / v / "manifest.json").write_text(json.dumps({"version": v, "techniques": t}))

    def test_cli_json_and_text_exit_zero(self):
        self._write()
        r = cli("rounds", "--json", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["rule"], "S2")
        t = cli("rounds", cwd=self.tmp)
        self.assertEqual(t.returncode, 0)
        self.assertTrue(t.stdout.startswith("STOP S2"))
        self.assertIn("tried out T17", t.stdout)

    def test_cli_malformed_exit_one(self):
        self.assertEqual(cli("rounds", cwd=self.tmp).returncode, 1)  # no feasibility.json
        self._write()
        (self.tmp / ".3d" / "rounds.jsonl").write_text("not json\n")
        r = cli("rounds", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("rounds.jsonl:1", r.stderr)
        (self.tmp / ".3d" / "rounds.jsonl").write_text(json.dumps({"round": 1, "scores": {"lighting": 1}}) + "\n")
        self.assertEqual(cli("rounds", cwd=self.tmp).returncode, 1)  # missing categories

    def test_new_version_technique_recorded(self):
        r = cli("new-version", "--technique", "T1,T8", "--technique", "T7", "--note", "x", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        m = json.loads((self.tmp / ".3d" / "versions" / "v001" / "manifest.json").read_text())
        self.assertEqual(m["techniques"], ["T1", "T8", "T7"])
        self.assertEqual(cli("new-version", "--technique", "banana", cwd=self.tmp).returncode, 2)
        self.assertEqual([p.name for p in (self.tmp / ".3d" / "versions").iterdir()], ["v001"])


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

    def _box(self, name: str, bg: str, fg: str, x: int, size: str = "320x180") -> Path:
        p = self.tmp / name
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        f"color=c={bg}:s={size},drawbox=x={x}:y=50:w=100:h=80:color={fg}:t=fill", "-frames:v", "1", str(p)], check=True)
        return p

    def _evidence(self, img: Path, shot: str = "S01", version: str = "v001") -> None:
        d = self.tmp / ".3d" / "evidence" / version
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(img, d / f"{shot}.png")
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"shots": [{"id": shot}]}))

    def test_match_identical_passes_all_metrics(self):
        ref = self._box("ref.png", "black", "white", 100)
        self._evidence(ref)
        r = cli("match", "--ref", str(ref), "--json", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        shot = out["shots"][0]
        self.assertEqual((out["status"], shot["status"]), ("PASS", "PASS"))
        self.assertEqual(set(shot["metrics"]), {"ssim", "edge_ssim", "mask_iou", "luma_p5_err", "luma_p50_err", "luma_p95_err", "delta_e"})
        self.assertAlmostEqual(shot["metrics"]["mask_iou"]["value"], 1.0, places=3)
        self.assertAlmostEqual(shot["metrics"]["delta_e"]["value"], 0.0, places=2)
        self.assertGreater(out["score"], 0.99)

    def test_match_separates_lighting_from_geometry(self):
        ref = self._box("ref.png", "black", "white", 100)
        lit = self._box("lit.png", "0x383838", "0xa8a8a8", 100)   # same geometry, different lighting
        moved = self._box("moved.png", "black", "white", 190)     # same lighting, different geometry
        self._evidence(lit)
        a = json.loads(cli("match", "--ref", str(ref), "--json", cwd=self.tmp).stdout)["shots"][0]["metrics"]
        self._evidence(moved)
        b = json.loads(cli("match", "--ref", str(ref), "--json", cwd=self.tmp).stdout)["shots"][0]["metrics"]
        self.assertEqual(a["mask_iou"]["status"], "PASS")           # silhouette fits
        self.assertGreater(a["edge_ssim"]["value"], 0.99)           # edges fit
        self.assertNotEqual(a["luma_p95_err"]["status"], "PASS")    # but the light level is off
        self.assertNotEqual(a["delta_e"]["status"], "PASS")
        self.assertEqual(b["mask_iou"]["status"], "FAIL")           # geometry is off
        self.assertLess(b["mask_iou"]["value"], a["mask_iou"]["value"])

    def test_match_tolerances_from_feasibility_json(self):
        ref = self._box("ref.png", "black", "white", 100)
        moved = self._box("moved.png", "black", "white", 130)
        self._evidence(moved)
        loose = json.loads(cli("match", "--ref", str(ref), "--json", cwd=self.tmp).stdout)["shots"][0]["metrics"]["mask_iou"]
        (self.tmp / ".3d" / "feasibility.json").write_text(json.dumps({"match_tolerances": {"mask_iou": {"pass": 0.5, "warn": 0.3}}}))
        tuned = json.loads(cli("match", "--ref", str(ref), "--json", cwd=self.tmp).stdout)
        self.assertEqual(tuned["tolerances"]["mask_iou"]["pass"], 0.5)
        self.assertEqual(tuned["shots"][0]["metrics"]["mask_iou"]["status"], "PASS")
        self.assertNotEqual(loose["status"], "PASS")

    def test_match_ref_dir_by_shot_id_and_missing_ref(self):
        ref = self._box("ref.png", "black", "white", 100)
        d = self.tmp / "refs"
        d.mkdir()
        shutil.copy(ref, d / "S01.png")
        self._evidence(ref)
        evd = self.tmp / ".3d" / "evidence" / "v001"
        shutil.copy(ref, evd / "S02.png")
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"shots": [{"id": "S01"}, {"id": "S02"}]}))
        out = json.loads(cli("match", "--ref", str(d), "--json", cwd=self.tmp).stdout)
        self.assertEqual(out["shots"][0]["status"], "PASS")
        self.assertIn("no reference image", out["shots"][1]["error"])
        t = cli("match", "--ref", str(d), cwd=self.tmp)
        self.assertIn("S02: ERROR", t.stdout)

    def test_match_usage_errors(self):
        self.assertEqual(cli("match", "--ref", "nope.png", cwd=self.tmp).returncode, 2)
        ref = self._box("ref.png", "black", "white", 100)
        self.assertEqual(cli("match", "--ref", str(ref), cwd=self.tmp).returncode, 1)  # no captures yet

    def _clip(self, path: Path, seconds: int, size: str = "160x90", rate: int = 10) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=s={size}:r={rate}:d={seconds}",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)

    def _probe(self, path: Path) -> dict:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                              "-of", "json", str(path)], capture_output=True, text=True).stdout
        d = json.loads(out)
        return {"w": d["streams"][0]["width"], "h": d["streams"][0]["height"], "dur": float(d["format"]["duration"])}

    def test_compare_stacks_and_loops_shorter_clip(self):
        a, b = self.tmp / "a.mp4", self.tmp / "b.mp4"
        self._clip(a, 1)
        self._clip(b, 2, "320x180")
        r = cli("compare", str(a), str(b), "--stack", "v", "--loops", "2", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        pr = self._probe(Path(self.tmp, res["file"]))
        self.assertEqual((pr["w"], pr["h"]), (160, 90 + 90))          # B scaled to A's width, stacked vertically
        self.assertAlmostEqual(pr["dur"], 4.0, delta=0.3)              # longer clip (2 s) x 2 loops
        h = json.loads(cli("compare", str(a), str(b), "--stack", "h", "--out", str(self.tmp / "h.mp4"), cwd=self.tmp).stdout)
        ph = self._probe(Path(h["file"]))
        self.assertEqual((ph["w"], ph["h"]), (160 + 160, 90))          # B scaled to A's height
        self.assertAlmostEqual(ph["dur"], 2.0, delta=0.3)

    def test_compare_versions_by_shot(self):
        for v in ("v001", "v002"):
            self._clip(self.tmp / ".3d" / "evidence" / v / "S01_clip.mp4", 1)
        r = cli("compare", "v001", "v002", "--shot", "S01", "--stack", "h", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(Path(self.tmp, json.loads(r.stdout)["file"]).is_file())
        self.assertEqual(cli("compare", "v001", "v009", "--shot", "S01", cwd=self.tmp).returncode, 1)
        self.assertEqual(cli("compare", "v001", "v002", "--loops", "0", cwd=self.tmp).returncode, 2)

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


class ParamsBridgeTests(unittest.TestCase):
    def test_read_params_and_set_params_under_node(self):
        node = shutil.which("node")
        nm = ROOT / "node_modules"
        if not node or not (nm / "typescript").is_dir() or not (nm / "three").is_dir():
            self.skipTest("node + repo node_modules (typescript, three) required")
        script = r"""
import ts from 'typescript'; import fs from 'node:fs'; import * as THREE from 'three';
const js = ts.transpileModule(fs.readFileSync(process.argv[2], 'utf8'), { compilerOptions: { module: 'ESNext', target: 'ES2022' } }).outputText;
const out = new URL('./bridge.mjs', import.meta.url); fs.writeFileSync(out, js);
const { readParams, installBridge } = await import(out.href);
const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const defaults = { key: 2, bloom: { strength: 0.4, radius: 1 }, list: [1, 2] };
const r = {};
r.ssr = readParams(defaults);                                         // no window: defaults (a copy)
r.ssr.bloom.strength = 99; r.ssrUntouched = defaults.bloom.strength;
r.merged = readParams(defaults, '?x=1&p=' + b64({ key: 5, bloom: { strength: 0.9 }, extra: true, list: [9] }));
r.badBase64 = readParams(defaults, '?p=%%%not-base64%%%');
r.badJson = readParams(defaults, '?p=' + Buffer.from('{oops').toString('base64url'));
r.notObject = readParams(defaults, '?p=' + b64([1, 2]));
globalThis.window = { location: { search: '?3d-preview&p=' + b64({ key: 7 }) } }; globalThis.document = { visibilityState: 'visible' };
const P = readParams(defaults);
r.fromWindow = P.key;
const seen = [];
installBridge({ gl: { render() {}, domElement: {}, info: { render: {}, memory: {} }, getContext: () => ({ getExtension: () => null }) },
  scene: new THREE.Scene(), camera: new THREE.PerspectiveCamera(), params: P, onParams: (p) => seen.push(JSON.stringify(p)) });
r.setReturn = window.__3d.setParams({ key: 11, bloom: { radius: 3 } });
r.mutated = { key: P.key, strength: P.bloom.strength, radius: P.bloom.radius };   // P itself changed in place
r.get = window.__3d.getParams().key; r.seen = seen.length; r.info = window.__3d.info().params.key;
console.log(JSON.stringify(r));
"""
        work = Path(tempfile.mkdtemp(prefix=".paramstest-", dir=ROOT))
        try:
            (work / "t.mjs").write_text(script)
            r = subprocess.run([node, str(work / "t.mjs"), str(ROOT / "skills/3d/assets/web/bridge.ts")], cwd=work, capture_output=True, text=True, timeout=60)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        if r.returncode != 0 and re.search(r"ERR_MODULE_NOT_FOUND|ERR_UNSUPPORTED_RESOLVE_REQUEST|Cannot find (package|module)", r.stderr):
            self.skipTest("node could not resolve typescript/three here")
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        o = json.loads(r.stdout.strip().splitlines()[-1])
        base = {"key": 2, "bloom": {"strength": 0.4, "radius": 1}, "list": [1, 2]}
        self.assertEqual(o["ssr"]["key"], 2)
        self.assertEqual(o["ssrUntouched"], 0.4)                       # defaults are copied, never mutated
        self.assertEqual(o["merged"], {"key": 5, "bloom": {"strength": 0.9, "radius": 1}, "list": [9], "extra": True})
        for k in ("badBase64", "badJson", "notObject"):
            self.assertEqual(o[k], base, k)                            # bad ?p= never throws, never changes anything
        self.assertEqual(o["fromWindow"], 7)
        self.assertEqual(o["setReturn"]["key"], 11)
        self.assertEqual(o["mutated"], {"key": 11, "strength": 0.4, "radius": 3})
        self.assertEqual((o["get"], o["seen"], o["info"]), (11, 1, 11))


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

    def _cap(self, *args, **kw):
        r = cli(*args, **kw)
        if r.returncode != 0 and "CDN unreachable" in r.stdout:
            self.skipTest("network down: viewer CDN unreachable")
        return r

    def test_capture_every_shot(self):
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "cube.glb").write_bytes(cube_glb())
        shots = {"schema": "shots.v1", "aspect": "16:9", "shots": [
            {"id": "hero", "focal_mm": 50, "position": [2, 1.5, 2.5], "target": [0, 0, 0], "to": {"position": [-2, 1.5, 2.5], "focal_mm": 85}},
            {"id": "top", "fov": 50, "position": [0, 4, 0.1], "target": [0, 0, 0], "roll_deg": 10},
            {"id": "ortho", "ortho_height": 2.5, "position": [0, 0, 5], "target": [0, 0, 0]}]}
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps(shots))
        r = self._cap("capture", "--size", "640x360", "--settle", "10", "--end", cwd=self.tmp, timeout=180)
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
        r = self._cap("capture", "--size", "480x270", "--settle", "5", cwd=self.tmp, timeout=180)
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
            r = self._cap("capture", "--clip", "1", "--size", "320x180", "--force", cwd=self.tmp, timeout=240)
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
        self.assertEqual(self._cap(*args, cwd=self.tmp, timeout=180).returncode, 0)
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

    def test_pathtrace_twin_or_clear_failure(self):
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "cube.glb").write_bytes(cube_glb())
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"shots": [
            {"id": "hero", "fov": 35, "position": [2, 1.5, 2.5], "target": [0, 0, 0]},
            {"id": "top", "fov": 50, "position": [0, 4, 0.1], "target": [0, 0, 0]}]}))
        r = self._cap("capture", "--pathtrace", "--samples", "16", "--shot", "hero", cwd=self.tmp, timeout=240)
        if r.returncode != 0 and "WebGPU is unavailable" in r.stdout:
            self.skipTest("headless WebGPU unavailable here")
        if r.returncode != 0 and "dynamically imported module" in r.stdout:
            self.skipTest("pinned CDN modules unreachable (offline)")
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr)
        entry = json.loads(r.stdout)["shots"][0]
        print(f"\n[pathtrace] {entry['samples']} spp in {entry['seconds']} s on {entry['renderer']}")
        self.assertEqual((entry["id"], entry["size"]), ("hero_pt", [854, 480]))
        self.assertGreaterEqual(entry["samples"], 16)
        png = self.tmp / ".3d" / "evidence" / "v001" / "hero_pt.png"
        self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreater(entry["luma_stddev"], 1.0)
        self.assertFalse((self.tmp / ".3d" / "evidence" / "v001" / "top_pt.png").exists())  # --shot limited it
        again = self._cap("capture", "--pathtrace", "--samples", "16", "--shot", "hero", cwd=self.tmp, timeout=240)
        self.assertEqual(again.returncode, 1)
        self.assertIn("--force", again.stderr)

    def test_pathtrace_without_webgpu_exits_one_naming_cycles_fallback(self):
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "cube.glb").write_bytes(cube_glb())
        env = {**os.environ, "PREVIEW_TEST_NO_WEBGPU": "1"}
        r = subprocess.run([sys.executable, str(PREVIEW), "capture", "--pathtrace"], cwd=self.tmp, capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(r.returncode, 1)
        self.assertIn("render_shots", r.stderr)
        self.assertIn("--import", r.stderr)
        self.assertIn("WebGPU", r.stderr)

    def test_pathtrace_argument_conflicts(self):
        cli("new-version", cwd=self.tmp)
        self.assertEqual(self._cap("capture", "--pathtrace", "--url", "http://127.0.0.1:1/", cwd=self.tmp).returncode, 2)
        self.assertEqual(self._cap("capture", "--pathtrace", "--clip", "1", cwd=self.tmp).returncode, 2)
        self.assertEqual(self._cap("capture", "--shot", "nope", cwd=self.tmp).returncode, 2)

    def _cube_version(self, shot_extra: dict | None = None) -> None:
        cli("new-version", cwd=self.tmp)
        (self.tmp / ".3d" / "versions" / "v001" / "cube.glb").write_bytes(cube_glb())
        (self.tmp / ".3d" / "shots.json").write_text(json.dumps({"shots": [
            {"id": "hero", "fov": 35, "position": [2, 1.5, 2.5], "target": [0, 0, 0], **(shot_extra or {})}]}))

    def test_capture_params_reach_the_viewer(self):
        self._cube_version()
        r = self._cap("capture", "--size", "320x180", "--settle", "3", "--params", '{"exposure": 0.25, "custom": {"k": 1}}', cwd=self.tmp, timeout=180)
        self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr)
        info = json.loads(r.stdout)["info"]
        self.assertEqual(info["params"], {"exposure": 0.25, "custom": {"k": 1}})
        self.assertEqual(info["exposure"], 0.25)
        dark = (self.tmp / ".3d" / "evidence" / "v001" / "hero.png").read_bytes()
        r = self._cap("capture", "--size", "320x180", "--settle", "3", "--force", cwd=self.tmp, timeout=180)
        self.assertNotEqual(dark, (self.tmp / ".3d" / "evidence" / "v001" / "hero.png").read_bytes())
        self.assertEqual(self._cap("capture", "--params", "[1]", "--force", cwd=self.tmp).returncode, 2)

    def test_sweep_renders_variants_ranks_by_match(self):
        self._cube_version()
        r = self._cap("sweep", "--param", "exposure=0.3,1,2.5", "--param", "toneMapping=Neutral,AgX", "--size", "320x180",
                      "--settle", "3", cwd=self.tmp, timeout=240)
        self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr)
        rank = json.loads(r.stdout)
        sdir = self.tmp / ".3d" / "sweeps" / "v001"
        self.assertEqual(len(rank["variants"]), 6)                      # 3 x 2 cartesian product
        self.assertEqual(rank["variants"][0]["params"], {"exposure": 0.3, "toneMapping": "Neutral"})
        pngs = [(sdir / f"var{i:02d}.png").read_bytes() for i in range(1, 7)]
        self.assertEqual(len(set(pngs)), 6, "variants rendered identically: setParams had no effect")
        self.assertTrue((sdir / "sheet.png").is_file())
        self.assertTrue((sdir / "rank.json").is_file())
        # rank against a reference that equals variant 4: it must come first
        ref = self.tmp / "ref.png"
        shutil.copy(sdir / "var04.png", ref)
        r2 = self._cap("sweep", "--param", "exposure=0.3,1,2.5", "--param", "toneMapping=Neutral,AgX", "--size", "320x180",
                       "--settle", "3", "--ref", str(ref), "--force", cwd=self.tmp, timeout=240)
        self.assertEqual(r2.returncode, 0, r2.stdout[-800:] + r2.stderr)
        rank2 = json.loads(r2.stdout)
        self.assertEqual(rank2["ranked"][0], "var04")
        self.assertEqual(len(rank2["ranked"]), 6)
        self.assertGreaterEqual(rank2["variants"][0]["score"], rank2["variants"][-1]["score"])
        self.assertEqual(self._cap("sweep", "--param", "exposure=1", cwd=self.tmp).returncode, 1)  # refuses to overwrite

    def test_sweep_usage_errors(self):
        self._cube_version()
        self.assertEqual(self._cap("sweep", cwd=self.tmp).returncode, 2)
        self.assertEqual(self._cap("sweep", "--param", "novalue", cwd=self.tmp).returncode, 2)
        many = ["--param", "a=1,2,3,4,5", "--param", "b=1,2,3,4,5"]
        r = self._cap("sweep", *many, cwd=self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("limit", r.stderr)

    def test_capture_clip_bad_seconds(self):
        cli("new-version", cwd=self.tmp)
        self.assertEqual(self._cap("capture", "--clip", "0", cwd=self.tmp).returncode, 2)

    def test_capture_rejects_bad_version(self):
        r = self._cap("capture", "--version", "../../x", cwd=self.tmp)
        self.assertEqual(r.returncode, 2)

    def test_capture_no_versions_exit_one(self):
        r = self._cap("capture", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
