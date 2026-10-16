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

    def test_gltf_external_bytes_counted(self) -> None:
        (self.tmp / "big.bin").write_bytes(b"\x00" * (4 * 1024 * 1024))
        doc = {"asset": {"version": "2.0"}, "buffers": [{"uri": "big.bin", "byteLength": 4 * 1024 * 1024},
                                                       {"uri": "gone.bin", "byteLength": 8}]}
        g = self.tmp / "m.gltf"
        g.write_text(json.dumps(doc))
        res = run("glb-report", str(g), "--json", "--budget", "hero")
        data = json.loads(res.stdout)
        self.assertEqual(data["external_bytes"], 4 * 1024 * 1024)
        self.assertEqual(data["missing_files"], ["gone.bin"])
        self.assertEqual(data["verdict"], "FAIL")  # 4 MiB > 3 MiB hero
        self.assertEqual(res.returncode, 1)

    def test_gltf_uri_cannot_escape_dir(self) -> None:
        outside = self.tmp / "outside.bin"
        outside.write_bytes(b"\x00" * 100)
        sub = self.tmp / "sub"
        sub.mkdir()
        g = sub / "m.gltf"
        g.write_text(json.dumps({"asset": {"version": "2.0"}, "buffers": [{"uri": "../outside.bin", "byteLength": 100}]}))
        data = json.loads(run("glb-report", str(g), "--json", "--budget", "none").stdout)
        self.assertEqual(data["external_bytes"], 0)
        self.assertEqual(data["missing_files"], ["../outside.bin"])

    def test_malformed_json_clean_exit(self) -> None:
        for name, body in (("list.gltf", "[1,2]"), ("null.gltf", '{"meshes": null}'), ("junk.gltf", "{nope")):
            f = self.tmp / name
            f.write_text(body)
            res = run("glb-report", str(f))
            self.assertEqual(res.returncode, 1, name)
            self.assertNotIn("Traceback", res.stderr, name)
            self.assertIn("glb-report:", res.stderr, name)

    def test_non_object_json_in_glb_and_truncated_chunk(self) -> None:
        js = b"[1]  "
        f = self.tmp / "arr.glb"
        f.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(js)) + struct.pack("<II", len(js), 0x4E4F534A) + js)
        res = run("glb-report", str(f))
        self.assertEqual(res.returncode, 1)
        self.assertNotIn("Traceback", res.stderr)
        t = self.tmp / "trunc.glb"
        make_glb(t)
        t.write_bytes(t.read_bytes()[:-40])
        res = run("glb-report", str(t))
        self.assertEqual(res.returncode, 1)
        self.assertIn("truncated", res.stderr)

    def test_cycle_rejected(self) -> None:
        g = self.tmp / "cyc.gltf"
        g.write_text(json.dumps({"asset": {"version": "2.0"}, "scenes": [{"nodes": [0]}],
                                 "nodes": [{"children": [1]}, {"children": [0]}]}))
        res = run("glb-report", str(g))
        self.assertEqual(res.returncode, 1)
        self.assertIn("cycle", res.stderr)

    def test_gpu_instancing_multiplies_triangles(self) -> None:
        doc = {"asset": {"version": "2.0"}, "scenes": [{"nodes": [0]}],
               "nodes": [{"mesh": 0, "extensions": {"EXT_mesh_gpu_instancing": {"attributes": {"TRANSLATION": 2}}}}],
               "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
               "accessors": [{"count": 4}, {"count": 6}, {"count": 50}]}
        g = self.tmp / "inst.gltf"
        g.write_text(json.dumps(doc))
        data = json.loads(run("glb-report", str(g), "--json").stdout)
        self.assertEqual((data["triangles"], data["draw_calls"]), (100, 1))

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


class CapabilitiesRobustnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_bad_package_json_exit_0(self) -> None:
        for body in ("[1]", "{nope", '"str"', "null"):
            proj = self.tmp / "p"
            proj.mkdir(exist_ok=True)
            (proj / "package.json").write_text(body)
            res = run("capabilities", "--root", str(proj), "--json")
            self.assertEqual(res.returncode, 0, body + res.stderr)
            self.assertNotIn("Traceback", res.stderr)
            data = json.loads(res.stdout)
            self.assertTrue(data["stack"].get("error"), body)
            self.assertIn("ignored", (proj / ".3d" / "capabilities.md").read_text())

    def test_mcp_secret_values_never_printed(self) -> None:
        home = self.tmp / "home"
        (home / ".codex").mkdir(parents=True)
        (home / ".claude.json").write_text(json.dumps({
            "mcpServers": {"blender-user": {"command": "SECRETVAL1", "env": {"TOKEN": "SECRETVAL2"}}},
            "projects": {"/x": {"mcpServers": {"spline-proj": {"url": "https://SECRETVAL3"}}}}}))
        (home / ".codex" / "config.toml").write_text(
            '[mcp_servers.blender-codex]\ncommand = "SECRETVAL4"\n[mcp_servers.other]\ncommand = "SECRETVAL5"\n')
        proj = self.tmp / "proj"
        proj.mkdir()
        import os
        res = subprocess.run([sys.executable, str(SCRIPTS / "capabilities"), "--root", str(proj), "--json"],
                             capture_output=True, text=True, timeout=120, env={**os.environ, "HOME": str(home)})
        self.assertEqual(res.returncode, 0, res.stderr)
        md = (proj / ".3d" / "capabilities.md").read_text()
        for out in (res.stdout, res.stderr, md):
            self.assertNotIn("SECRETVAL", out)
        names = {n for h in json.loads(res.stdout)["mcp"] for n in h["servers"]}
        self.assertEqual(names, {"blender-user", "spline-proj", "blender-codex"})

    def test_no_package_json(self) -> None:
        res = run("capabilities", "--root", str(self.tmp), "--json")
        self.assertEqual(res.returncode, 0)
        self.assertFalse(json.loads(res.stdout)["stack"]["package_json"])


TEMPLATES = ROOT / "skills" / "3d" / "assets" / "templates"


class SpecCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def variant(self, template: str, mutate) -> Path:
        doc = json.loads((TEMPLATES / template).read_text())
        mutate(doc)
        out = self.tmp / template
        out.write_text(json.dumps(doc))
        return out

    def fails(self, path: Path, needle: str) -> None:
        res = run("spec-check", str(path))
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn(needle, res.stdout)

    def test_templates_pass(self) -> None:
        for t in ("refspec.example.json", "shots.json"):
            res = run("spec-check", str(TEMPLATES / t))
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_shot_time_t_accepted(self) -> None:
        path = self.variant("shots.json", lambda d: d["shots"][0].update(t=2.5))
        self.assertEqual(run("spec-check", str(path)).returncode, 0)

    def test_look_valid_and_broken(self) -> None:
        look = self.tmp / "look.json"
        base = {"schema": "look.v1", "toneMapping": "agx", "exposure": 1.1,
                "environment": "https://cdn.example.com/x/venice.hdr?v=1", "background": "environment"}
        look.write_text(json.dumps(base))
        self.assertEqual(run("spec-check", str(look)).returncode, 0)
        look.write_text(json.dumps({**base, "environment": "room", "background": "#0b0d12"}))
        self.assertEqual(run("spec-check", str(look)).returncode, 0)
        look.write_text(json.dumps({**base, "environment": "maps/studio.exr"}))
        self.assertEqual(run("spec-check", str(look)).returncode, 0)
        look.write_text(json.dumps({**base, "mood": "x"}))
        res = run("spec-check", str(look))
        self.assertEqual(res.returncode, 0)
        self.assertIn("WARN $.mood", res.stdout)
        look.write_text(json.dumps({"schema": "look.v1", "toneMapping": "filmic", "exposure": 0,
                                    "environment": "pic.png", "background": "red"}))
        res = run("spec-check", str(look))
        self.assertEqual(res.returncode, 1)
        for path in ("$.toneMapping", "$.exposure", "$.environment", "$.background"):
            self.assertIn(path, res.stdout)

    def test_shots_broken(self) -> None:
        self.fails(self.variant("shots.json", lambda d: d["shots"][1].update(position=[1, 2])), "$.shots[1].position")
        self.fails(self.variant("shots.json", lambda d: d["shots"][0].update(fov=40)), "$.shots[0]: needs exactly one")
        self.fails(self.variant("shots.json", lambda d: d["shots"][1].update(id="S01")), "duplicate id")
        self.fails(self.variant("shots.json", lambda d: d["shots"][1].update(scroll=[0.2, 0.5])), "overlaps")
        self.fails(self.variant("shots.json", lambda d: d["shots"][0].update(ease="bounce")), "$.shots[0].ease")
        self.fails(self.variant("shots.json", lambda d: d["shots"][0].update(id="a b")), "$.shots[0].id")
        self.fails(self.variant("shots.json", lambda d: d["shots"][0].update(t=-1)), "$.shots[0].t")
        self.fails(self.variant("shots.json", lambda d: d["shots"][0].update(t="3")), "$.shots[0].t")
        self.fails(self.variant("shots.json", lambda d: d.update(aspect="wide")), "$.aspect")
        self.fails(self.variant("shots.json", lambda d: d["shots"][0]["to"].update(colour="x")), "$.shots[0].to.colour")

    def test_refspec_broken(self) -> None:
        self.fails(self.variant("refspec.example.json", lambda d: d.update(anchors=["a"])), "$.anchors")
        self.fails(self.variant("refspec.example.json", lambda d: d.update(hidden_or_unknown=[])), "$.hidden_or_unknown")
        self.fails(self.variant("refspec.example.json", lambda d: d["refs"].append(dict(d["refs"][0]))), "duplicate id")
        self.fails(self.variant("refspec.example.json",
                                lambda d: d["camera"]["angle"].update(evidence="inferred", value=5)),
                   "$.camera.angle.value")
        self.fails(self.variant("refspec.example.json", lambda d: d["camera"]["angle"].update(confidence="sure")),
                   "$.camera.angle.confidence")
        self.fails(self.variant("refspec.example.json", lambda d: d["colour"]["palette"][0].update(hex="red")),
                   "$.colour.palette[0].hex")

    def test_bad_inputs(self) -> None:
        junk = self.tmp / "junk.json"
        junk.write_text("{nope")
        self.assertEqual(run("spec-check", str(junk)).returncode, 1)
        junk.write_text('{"schema": "mystery.v9"}')
        self.fails(junk, "$.schema")
        self.assertEqual(run("spec-check", str(self.tmp / "missing.json")).returncode, 2)


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
        self.assertTrue(0 <= luma["p5"] <= luma["p50"] <= luma["p95"] <= 1, luma)
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

    def test_pan_direction_in_motion(self) -> None:
        vid = self.tmp / "pan.mp4"
        self.ff("-f", "lavfi", "-i", "testsrc=duration=3:size=640x180:rate=15",
                "-vf", "crop=320:180:x='t*100':y=0", "-pix_fmt", "yuv420p", str(vid))
        out = self.tmp / "out"
        self.assertEqual(run("ref-extract", str(vid), "--out", str(out), "--frames", "2").returncode, 0)
        samples = json.loads((out / "pan" / "motion.json").read_text())["samples"]
        for key in ("dx", "dy", "speed_w_pct_s", "speed_h_pct_s"):
            self.assertIn(key, samples[0])
        dxs = [x["dx"] for x in samples]
        self.assertLess(sum(dxs), 0, dxs)          # content moves left while the crop window pans right
        self.assertTrue(all(abs(x["dy"]) <= 1 for x in samples))
        self.assertGreater(max(x["speed_w_pct_s"] for x in samples), 0)

    def test_dash_name_and_stale_frames(self) -> None:
        vid = self.tmp / "-odd name.mp4"
        self.ff("-f", "lavfi", "-i", "testsrc=duration=2:size=160x90:rate=10", "-pix_fmt", "yuv420p", str(vid))
        out = self.tmp / "out"
        stale = out / "odd-name" / "frames" / "frame_099.jpg"
        stale.parent.mkdir(parents=True)
        stale.write_bytes(b"x")
        res = subprocess.run([sys.executable, str(SCRIPTS / "ref-extract"), vid.name, "--out", str(out), "--frames", "2"],
                             capture_output=True, text=True, cwd=self.tmp, timeout=120)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse(stale.exists())

    def test_regions_and_kymo(self) -> None:
        vid = self.tmp / "blink.mp4"
        # top-left quarter blinks white at 1 Hz; everything else is static black
        self.ff("-f", "lavfi", "-i", "color=black:size=320x180:rate=15:duration=6",
                "-vf", "drawbox=x=0:y=0:w=160:h=90:color=white:t=fill:enable='lt(mod(t,1),0.5)'",
                "-pix_fmt", "yuv420p", str(vid))
        out = self.tmp / "out"
        res = run("ref-extract", str(vid), "--out", str(out), "--frames", "2", "--regions", "2", "--kymo-at", "0.25,0.25")
        self.assertEqual(res.returncode, 0, res.stderr)
        reg = json.loads((out / "blink" / "regions.json").read_text())
        self.assertEqual((reg["n"], len(reg["cells"])), (2, 4))
        self.assertEqual(len(reg["cells"][0]["energy"]), len(reg["t"]))
        tl = reg["cells"][0]
        self.assertGreater(tl["mean"], 10 * max(c["mean"] for c in reg["cells"][1:]) + 1e-9)
        self.assertIsNotNone(tl["period_s"])
        self.assertAlmostEqual(tl["period_s"], 1.0, delta=0.15)
        self.assertTrue(all(c["period_s"] is None for c in reg["cells"][1:]))
        for name, dims in (("kymo-rows.png", None), ("kymo-cols.png", None)):
            data = (out / "blink" / name).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n", name)
            w, h = struct.unpack(">II", data[16:24])
            if name == "kymo-rows.png":
                self.assertEqual(w, 480)
                self.assertGreater(h, 30)
            else:
                self.assertEqual(h, 270)
                self.assertGreater(w, 30)

    def test_bad_regions_usage(self) -> None:
        self.assertEqual(run("ref-extract", "x.mp4", "--regions", "20").returncode, 2)
        self.assertEqual(run("ref-extract", "x.mp4", "--kymo-at", "3,1").returncode, 2)

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
