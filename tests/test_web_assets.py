"""Runs the DOM-only web assets (entrance-gate.ts, shader-guard.ts, bridge.ts frame stats) under node.

Each module is transpiled with the repo's typescript and imported by a script that fakes only the
DOM it touches (an EventTarget with attributes, a renderer with `debug` and `info`). The shader guard
also runs on the repo's real three in the installed Chrome (python playwright), where both exist.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "skills" / "3d" / "assets" / "web"

PRELUDE = r"""
import ts from 'typescript'; import fs from 'node:fs';
const load = async (path, name) => {
  const js = ts.transpileModule(fs.readFileSync(path, 'utf8'), { compilerOptions: { module: 'ESNext', target: 'ES2022' } }).outputText;
  const out = new URL('./' + name + '.mjs', import.meta.url); fs.writeFileSync(out, js);
  return import(out.href);
};
"""


def run_node(test: unittest.TestCase, script: str, *args: Path) -> dict:
    node = shutil.which("node")
    if not node or not (ROOT / "node_modules" / "typescript").is_dir():
        test.skipTest("node + repo node_modules (typescript) required: run npm install at the repo root")
    # unique scratch dir inside the repo so node resolves node_modules; no shared file names between runs
    work = Path(tempfile.mkdtemp(prefix=".webtest-", dir=ROOT))
    try:
        (work / "t.mjs").write_text(PRELUDE + script)
        r = subprocess.run([node, str(work / "t.mjs"), *map(str, args)], cwd=work, capture_output=True, text=True, timeout=60)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if r.returncode != 0 and re.search(r"ERR_MODULE_NOT_FOUND|ERR_UNSUPPORTED_RESOLVE_REQUEST|Cannot find (package|module)", r.stderr):
        test.skipTest("node could not resolve typescript here: " + r.stderr.strip().splitlines()[-1][:200])
    test.assertEqual(r.returncode, 0, r.stderr[-1200:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class EntranceGateTests(unittest.TestCase):
    def test_when_entrance_phases_timeout_abort(self):
        script = r"""
const gate = await load(process.argv[2], 'gate');
const r = {};
r.ssr = await gate.whenEntrance('settled');                 // no document: 'none'
r.ssrRead = gate.readEntrance();

let listeners = 0;
class El extends EventTarget {
  attrs = new Map();
  getAttribute(n) { return this.attrs.has(n) ? this.attrs.get(n) : null; }
  setAttribute(n, v) { this.attrs.set(n, String(v)); }
  removeAttribute(n) { this.attrs.delete(n); }
  addEventListener(t, f, o) { if (t === 'entrance:phase') listeners++; super.addEventListener(t, f, o); }
  removeEventListener(t, f, o) { if (t === 'entrance:phase') listeners--; super.removeEventListener(t, f, o); }
}
const html = new El();
globalThis.document = { documentElement: html };
// the publisher's order: attribute first, then the bubbling event
const publish = (el, phase) => { el.setAttribute('data-entrance', phase); el.dispatchEvent(new CustomEvent('entrance:phase', { bubbles: true, detail: { phase } })); };
const tick = () => new Promise((res) => setTimeout(res, 5));
const state = (p) => { let s = 'waiting'; p.then((v) => { s = v; }, (e) => { s = 'rejected:' + (e && e.name); }); return () => s; };

r.absent = await gate.whenEntrance('settled');
html.setAttribute('data-entrance', 'bogus');
r.unknown = await gate.whenEntrance('tail');
r.unknownRead = gate.readEntrance();

html.setAttribute('data-entrance', 'settled');
r.pastTail = await gate.whenEntrance('tail');               // already past: 'phase' at once
r.pastRunning = await gate.whenEntrance('running');

html.setAttribute('data-entrance', 'pending');
r.readPending = gate.readEntrance();
const tail = state(gate.whenEntrance('tail', { timeoutMs: 5000 }));
const settled = state(gate.whenEntrance('settled', { timeoutMs: 5000 }));
publish(html, 'running'); await tick();
r.afterRunning = [tail(), settled()];
publish(html, 'tail'); await tick();
r.afterTail = [tail(), settled()];
publish(html, 'settled'); await tick();
r.afterSettled = [tail(), settled()];
r.listenersAfterPhases = listeners;

html.setAttribute('data-entrance', 'running');
const skip = state(gate.whenEntrance('tail', { timeoutMs: 5000 }));
publish(html, 'settled'); await tick();                      // tail skipped by the publisher
r.tailSkipped = skip();

html.setAttribute('data-entrance', 'pending');
const t0 = performance.now();
r.timeout = await gate.whenEntrance('settled', { timeoutMs: 30, since: performance.now() });
r.timeoutWaited = performance.now() - t0 >= 25;
r.zeroTimeout = await gate.whenEntrance('settled', { timeoutMs: 0 });
r.listenersAfterTimeout = listeners;

// The page's clock: the timeout counts from navigation start (performance.now() 0), never from the call. A caller
// that runs at hydration, after the deadline, must not get a fresh one.
let t = performance.now();
r.pastDeadline = await gate.whenEntrance('settled', { timeoutMs: Math.max(0, t - 50) });
r.pastDeadlineMs = performance.now() - t;
t = performance.now();
r.ahead = await gate.whenEntrance('settled', { timeoutMs: t + 60 });   // the deadline is 60 ms after navigation's "now"
r.aheadMs = performance.now() - t;
t = performance.now();
r.since = await gate.whenEntrance('settled', { timeoutMs: 40, since: t });   // a route's own entrance, from its mount
r.sinceMs = performance.now() - t;
const early = state(gate.whenEntrance('settled', { timeoutMs: performance.now() + 5000 }));
publish(html, 'settled'); await tick();                      // the phase still wins before the deadline
r.phaseBeforeDeadline = early();
r.listenersAfterClock = listeners;
html.setAttribute('data-entrance', 'pending');

const ac = new AbortController();
const aborted = state(gate.whenEntrance('settled', { timeoutMs: 5000, signal: ac.signal }));
ac.abort(); await tick();
r.abort = aborted();
r.listenersAfterAbort = listeners;
r.preAborted = await gate.whenEntrance('settled', { signal: AbortSignal.abort() }).then(() => 'resolved', (e) => 'rejected:' + e.name);

const removed = state(gate.whenEntrance('settled', { timeoutMs: 5000 }));
html.removeAttribute('data-entrance'); html.dispatchEvent(new CustomEvent('entrance:phase', { detail: {} })); await tick();
r.removedMidWait = removed();

const section = new El();
section.setAttribute('data-entrance', 'running');
const scoped = state(gate.whenEntrance('settled', { scope: section, timeoutMs: 5000 }));
publish(html, 'settled'); await tick();                      // another scope's phase does not count
r.scopedBefore = scoped();
publish(section, 'settled'); await tick();
r.scopedAfter = scoped();
r.listenersEnd = listeners;
console.log(JSON.stringify(r));
"""
        o = run_node(self, script, WEB / "entrance-gate.ts")
        self.assertEqual(o["ssr"], "none")
        self.assertIsNone(o["ssrRead"])
        self.assertEqual(o["absent"], "none")
        self.assertEqual(o["unknown"], "none")
        self.assertIsNone(o["unknownRead"])
        self.assertEqual((o["pastTail"], o["pastRunning"]), ("phase", "phase"))
        self.assertEqual(o["readPending"], "pending")
        self.assertEqual(o["afterRunning"], ["waiting", "waiting"])
        self.assertEqual(o["afterTail"], ["phase", "waiting"])
        self.assertEqual(o["afterSettled"], ["phase", "phase"])
        self.assertEqual(o["listenersAfterPhases"], 0)
        self.assertEqual(o["tailSkipped"], "phase")
        self.assertEqual(o["timeout"], "timeout")
        self.assertTrue(o["timeoutWaited"])
        self.assertEqual(o["zeroTimeout"], "timeout")
        self.assertEqual(o["listenersAfterTimeout"], 0)
        # the hydration clock: a deadline already past at the call resolves on the next task, not after timeoutMs
        self.assertEqual(o["pastDeadline"], "timeout")
        self.assertLess(o["pastDeadlineMs"], 25)
        self.assertEqual(o["ahead"], "timeout")
        self.assertGreaterEqual(o["aheadMs"], 50)
        self.assertLess(o["aheadMs"], 400)
        self.assertEqual(o["since"], "timeout")
        self.assertGreaterEqual(o["sinceMs"], 35)
        self.assertLess(o["sinceMs"], 400)
        self.assertEqual(o["phaseBeforeDeadline"], "phase")
        self.assertEqual(o["listenersAfterClock"], 0)
        self.assertEqual(o["abort"], "rejected:AbortError")
        self.assertEqual(o["listenersAfterAbort"], 0)
        self.assertEqual(o["preAborted"], "rejected:AbortError")
        self.assertEqual(o["removedMidWait"], "none")
        self.assertEqual(o["scopedBefore"], "waiting")
        self.assertEqual(o["scopedAfter"], "phase")
        self.assertEqual(o["listenersEnd"], 0)

    def test_per_visit_clock_and_standalone_publisher(self):
        script = r"""
const gate = await load(process.argv[2], 'gate');
const r = {};
class El extends EventTarget {
  attrs = new Map();
  getAttribute(n) { return this.attrs.has(n) ? this.attrs.get(n) : null; }
  setAttribute(n, v) { this.attrs.set(n, String(v)); }
  removeAttribute(n) { this.attrs.delete(n); }
}
const html = new El();
const frames = [];
globalThis.document = { documentElement: html, timeline: {} };
globalThis.requestAnimationFrame = (fn) => frames.push(fn);
globalThis.cancelAnimationFrame = () => {};
const flush = () => frames.splice(0).forEach((fn) => fn(0));
const tick = (ms = 5) => new Promise((res) => setTimeout(res, ms));
const state = (p) => { let s = 'waiting'; p.then((v) => { s = v; }, (e) => { s = 'rejected:' + (e && e.name); }); return () => s; };
// the owner's order: the stamp and the attribute first, then the event with the visit
const publish = (phase, visit) => {
  if (phase === 'pending') html.removeAttribute('data-entrance-started');
  if (phase === 'running') html.setAttribute('data-entrance-started', String(performance.now()));
  html.setAttribute('data-entrance', phase);
  if (visit) html.setAttribute('data-visit', String(visit));
  html.dispatchEvent(new CustomEvent('entrance:phase', { bubbles: true, detail: { phase, visit } }));
};

// The owner's stamp is the clock: long after navigation start, a fresh entrance still gets its full timeout.
await tick(60);
html.setAttribute('data-entrance', 'running');
html.setAttribute('data-entrance-started', String(performance.now()));
r.stampedStart = gate.entranceStartedAt() > 50;
let t = performance.now();
r.stamped = await gate.whenEntrance('settled', { timeoutMs: 40 });
r.stampedMs = performance.now() - t;

// A client-side navigation: the owner restarts the phase. Held at pending, no timeout runs.
publish('pending', 2);
r.heldStart = gate.entranceStartedAt();
r.readsNewVisit = gate.readEntrance();
const held = state(gate.whenEntrance('settled', { timeoutMs: 30 }));
await tick(60);
r.heldWaits = held();
publish('running', 2);
await tick(10);
r.runningWaits = held();
await tick(40);
r.afterClock = held();

// A wait open across a visit carries on into the new one.
publish('pending', 3); publish('running', 3);
const open = state(gate.whenEntrance('settled', { timeoutMs: 5000 }));
publish('pending', 4);
await tick();
r.acrossVisit = open();
publish('running', 4); publish('settled', 4);
await tick();
r.acrossVisitSettled = open();

// Standalone: no owner, a CSS entrance. running at once, settled when its animations have finished.
html.removeAttribute('data-visit'); html.removeAttribute('data-entrance-started'); html.setAttribute('data-entrance', 'pending');
let done;
const animation = { playState: 'running', timeline: document.timeline, effect: { getComputedTiming: () => ({ endTime: 1300 }) }, finished: new Promise((res) => { done = res; }) };
const root = { animations: [animation], getAnimations() { return this.animations; } };
const stop = gate.trackEntranceAlone(root);
r.aloneRunning = gate.readEntrance();
flush(); flush(); await tick();
r.aloneStillRunning = gate.readEntrance();
root.animations = []; done(); await tick(); flush(); flush();
r.aloneSettled = gate.readEntrance();
stop();
// With an owner on the page it stands down.
html.setAttribute('data-visit', '5'); html.setAttribute('data-entrance', 'pending');
gate.trackEntranceAlone(root);
r.standsDown = gate.readEntrance();
console.log(JSON.stringify(r));
"""
        o = run_node(self, script, WEB / "entrance-gate.ts")
        self.assertTrue(o["stampedStart"])
        self.assertEqual(o["stamped"], "timeout")
        self.assertGreaterEqual(o["stampedMs"], 35)
        self.assertIsNone(o["heldStart"])
        self.assertEqual(o["readsNewVisit"], "pending")
        self.assertEqual(o["heldWaits"], "waiting")
        self.assertEqual(o["runningWaits"], "waiting")
        self.assertEqual(o["afterClock"], "timeout")
        self.assertEqual(o["acrossVisit"], "waiting")
        self.assertEqual(o["acrossVisitSettled"], "phase")
        self.assertEqual(o["aloneRunning"], "running")
        self.assertEqual(o["aloneStillRunning"], "running")
        self.assertEqual(o["aloneSettled"], "settled")
        self.assertEqual(o["standsDown"], "pending")


class ShaderGuardTests(unittest.TestCase):

    def test_verdict_and_handler(self):
        script = r"""
const g = await load(process.argv[2], 'guard');
const r = {};
r.empty = g.shaderVerdict([], null);
r.clean = g.shaderVerdict([], [{}, { name: 'a', diagnostics: { runnable: true, programLog: 'warning only' } }]);
r.dead = g.shaderVerdict([], [{ name: 'MergedPass', diagnostics: { runnable: false, programLog: '', fragmentShader: { log: "ERROR: 0:58: 'LinearTransferOETF' : function already has a body" } } }]);
r.errorFirst = g.shaderVerdict(['from handler'], [{ diagnostics: { runnable: false, programLog: 'x' } }]);
// Chrome's program log only says a stage failed; the cause is in the shader's log, which must come first
r.causeFirst = g.shaderVerdict([], [{ name: 'Merged', diagnostics: { runnable: false, programLog: 'Fragment shader is not compiled.', fragmentShader: { log: "ERROR: 0:12: 'x' : undeclared identifier" } } }]);

const logged = []; const orig = console.error; console.error = (...a) => logged.push(a.join(' '));
const renderer = { debug: { checkShaderErrors: false, onShaderError: null }, info: { programs: [] } };
const seen = [];
const guard = g.guardShaders(renderer, (reason) => seen.push(reason));
r.checksOn = renderer.debug.checkShaderErrors;
r.beforeFailure = guard.check();
const gl = { getProgramInfoLog: () => 'Fragment shader is not compiled.\n', getShaderInfoLog: (s) => (s === 'fs' ? "  ERROR: 0:64: 'sRGBTransferOETF' : function already has a body\n" : '') };
renderer.debug.onShaderError(gl, {}, 'vs', 'fs');           // three calls this at the program's first use
console.error = orig;
r.seen = seen; r.logged = logged.length === 1 && logged[0].includes('sRGBTransferOETF');
const bare = { getProgramInfoLog: () => '', getShaderInfoLog: () => null };
const quiet = { debug: { checkShaderErrors: true, onShaderError: null }, info: { programs: [] } };
const quietSeen = []; console.error = () => {};
g.guardShaders(quiet, (reason) => quietSeen.push(reason)); quiet.debug.onShaderError(bare, {}, 'vs', 'fs');
console.error = orig;
r.noLogs = quietSeen;
r.afterFailure = guard.check();
const silent = { debug: { checkShaderErrors: true, onShaderError: null }, info: { programs: [{ name: 'p', diagnostics: { runnable: false, programLog: 'link failed' } }] } };
r.diagnosticsOnly = g.guardShaders(silent).check();
guard.dispose(); r.restored = renderer.debug.onShaderError === null;
console.log(JSON.stringify(r));
"""
        o = run_node(self, script, WEB / "shader-guard.ts")
        self.assertEqual(o["empty"], {"ok": True})
        self.assertEqual(o["clean"], {"ok": True})                   # a warning log is not a failure
        self.assertFalse(o["dead"]["ok"])
        self.assertIn("MergedPass", o["dead"]["reason"])
        self.assertIn("function already has a body", o["dead"]["reason"])
        self.assertEqual(o["errorFirst"], {"ok": False, "reason": "from handler"})
        self.assertTrue(o["causeFirst"]["reason"].startswith("Merged: ERROR: 0:12: 'x' : undeclared identifier"))
        self.assertIn("Fragment shader is not compiled.", o["causeFirst"]["reason"])
        self.assertTrue(o["checksOn"])                               # the guard turns checks back on
        self.assertEqual(o["beforeFailure"], {"ok": True})
        # the shader's own log leads; the program's "not compiled" line follows it
        self.assertEqual(o["seen"], ["ERROR: 0:64: 'sRGBTransferOETF' : function already has a body\nFragment shader is not compiled."])
        self.assertEqual(o["noLogs"], ["link failed"])
        self.assertTrue(o["logged"])                                 # the handler replaces three's log, so it logs
        self.assertFalse(o["afterFailure"]["ok"])
        self.assertEqual(o["diagnosticsOnly"], {"ok": False, "reason": "p: link failed"})
        self.assertTrue(o["restored"])


GUARD_PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><script type="importmap">{"imports": {"three": "./three.module.js"}}</script></head>
<body><script type="module">
import * as THREE from 'three'
import { guardShaders } from './shader-guard.js'
const r = { webgl: false }
try {
  const canvas = Object.assign(document.createElement('canvas'), { width: 64, height: 64 })
  document.body.append(canvas)
  const renderer = new THREE.WebGLRenderer({ canvas })
  r.webgl = true
  r.revision = THREE.REVISION
  const seen = []
  const guard = guardShaders(renderer, (reason) => seen.push(reason))
  r.checksOn = renderer.debug.checkShaderErrors
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera()
  camera.position.z = 2
  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial({ color: 0xff8800 })))
  await renderer.compileAsync(scene, camera)
  renderer.render(scene, camera)
  r.valid = guard.check()
  // The field report's bug: three already prefixes colorspace_pars_fragment to every ShaderMaterial.
  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.ShaderMaterial({
    vertexShader: 'void main() { gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: '#include <colorspace_pars_fragment>\nvoid main() { gl_FragColor = vec4(1.0); }',
  })))
  await renderer.compileAsync(scene, camera)
  r.afterCompile = guard.check()            // nothing yet: three checks a program at its first use
  r.seenAfterCompile = seen.length
  renderer.render(scene, camera)             // the warm render: the first use
  r.afterRender = guard.check()
  r.seen = seen
  r.notRunnable = renderer.info.programs.filter((p) => p.diagnostics && !p.diagnostics.runnable).length
} catch (e) {
  r.error = String((e && e.message) || e)
}
window.__result = r
</script></body></html>
"""

# Headless Chrome's own GL first, then software WebGL (the flag set scripts/preview falls back to).
GL_FLAGS = ([], ["--use-gl=angle", "--use-angle=swiftshader-webgl", "--enable-unsafe-swiftshader"])


def browser_skip_reason() -> str | None:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return "python playwright not installed"
    if not (Path("/Applications/Google Chrome.app").exists() or shutil.which("google-chrome")
            or shutil.which("google-chrome-stable") or shutil.which("chrome")):
        return "Google Chrome not found"
    if not (ROOT / "node_modules" / "three" / "build" / "three.core.js").is_file():
        return "repo node_modules (three) required: run npm install at the repo root"
    if not shutil.which("node") or not (ROOT / "node_modules" / "typescript").is_dir():
        return "node + repo node_modules (typescript) required"
    return None


def transpile(path: Path) -> str:
    script = ("const ts = require('typescript'), fs = require('fs');"
              "process.stdout.write(ts.transpileModule(fs.readFileSync(process.argv[1], 'utf8'),"
              " { compilerOptions: { module: 'ESNext', target: 'ES2022' } }).outputText)")
    r = subprocess.run([shutil.which("node"), "-e", script, str(path)], cwd=ROOT, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    return r.stdout


class ShaderGuardInChromeTests(unittest.TestCase):
    """The forced shader error on real three (the repo's r186) in the installed Chrome: compileAsync alone reports
    nothing, the warm render's first use trips the guard with the shader's own log, and three's console error is
    replaced by the guard's. SceneCanvas turns that verdict into data-scene-mode="error" (its source contract above)."""

    def test_forced_shader_error_trips_the_guard_after_the_warm_render(self):
        reason = browser_skip_reason()
        if reason:
            self.skipTest(reason)
        build = ROOT / "node_modules" / "three" / "build"
        files = {
            "index.html": (GUARD_PAGE.encode(), "text/html"),
            "shader-guard.js": (transpile(WEB / "shader-guard.ts").encode(), "text/javascript"),
            "three.module.js": ((build / "three.module.js").read_bytes(), "text/javascript"),
            "three.core.js": ((build / "three.core.js").read_bytes(), "text/javascript"),
        }
        from playwright.sync_api import sync_playwright

        def serve(route) -> None:
            name = route.request.url.rsplit("/", 1)[-1]
            body, ctype = files.get(name, (b"", "text/plain"))
            route.fulfill(status=200 if name in files else 404, body=body, content_type=ctype)

        result, console = {"webgl": False}, []
        with sync_playwright() as p:
            for flags in GL_FLAGS:
                browser = p.chromium.launch(channel="chrome", headless=True, args=flags)
                try:
                    page = browser.new_page()
                    console = []
                    page.on("console", lambda m: console.append(m.text))
                    page.route("http://guard.test/**", serve)
                    page.goto("http://guard.test/index.html")
                    page.wait_for_function("window.__result !== undefined", timeout=30000)
                    result = page.evaluate("window.__result")
                finally:
                    browser.close()
                if result.get("webgl"):
                    break
        if not result.get("webgl"):
            self.skipTest("no WebGL in headless Chrome here: " + str(result.get("error", ""))[:200])
        self.assertNotIn("error", result, result.get("error"))
        self.assertTrue(result["checksOn"])
        self.assertEqual(result["valid"], {"ok": True})
        self.assertEqual(result["afterCompile"], {"ok": True})        # compileAsync never fills diagnostics
        self.assertEqual(result["seenAfterCompile"], 0)
        self.assertFalse(result["afterRender"]["ok"])
        self.assertIn("function already has a body", result["afterRender"]["reason"])
        self.assertFalse(result["afterRender"]["reason"].startswith("Fragment shader is not compiled"))
        self.assertTrue(result["seen"] and "function already has a body" in result["seen"][0])
        self.assertGreaterEqual(result["notRunnable"], 1)
        self.assertTrue(any("[scene] shader program failed" in text for text in console))
        self.assertFalse(any("THREE.WebGLProgram: Shader Error" in text for text in console))  # replaced, not doubled


def code_only(source: str) -> str:
    """The TSX with its comments removed (the file has no '//' or '/*' inside a string)."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"(?m)//.*$", "", source)


class SceneCanvasRevealPathTests(unittest.TestCase):
    """r3f/SceneCanvas.tsx can't render under node (no react-dom here), so this guards the source's contract:
    the poster path downloads no three, nothing on the reveal path goes through React.lazy (React 19 holds a shown
    fallback's reveal ~300 ms, FALLBACK_THROTTLE_MS), and the failsafe counts from navigation start, not mount."""

    @classmethod
    def setUpClass(cls):
        cls.code = code_only((WEB / "r3f" / "SceneCanvas.tsx").read_text(encoding="utf-8"))

    def test_poster_path_downloads_no_three(self):
        static = re.findall(r"(?m)^import\s+(?!type\b)[^;]*?from\s+'([^']+)'", self.code)
        self.assertNotIn("three", static)
        self.assertNotIn("@react-three/fiber", static)
        self.assertIn("import('three')", self.code)
        self.assertIn("import('@react-three/fiber')", self.code)

    def test_no_suspense_hold_on_the_reveal(self):
        lazies = re.findall(r"(\w+)\s*=\s*lazy\(", self.code)
        self.assertEqual(lazies, ["LazyDriver"])              # only the driver's fallback outside a SceneCanvas
        self.assertEqual(self.code.count("<Suspense"), 1)      # the one inside the Canvas, for asset children
        self.assertIn("setLoaded({ Live, Scene:", self.code)    # the loaded modules render from state
        self.assertRegex(self.code, r"<Canvas[\s\S]*<Suspense fallback=\{null\}>[\s\S]*</Suspense>[\s\S]*</Canvas>")

    def test_failsafe_counts_from_the_entrance_start(self):
        self.assertNotRegex(self.code, r"performance\.now\(\)\s*\+")
        self.assertNotIn("deadline", self.code)
        self.assertIn("whenEntrance(phase, { timeoutMs: entranceTimeoutMs, signal })", self.code)

    def test_a_held_route_change_is_mid_entrance(self):
        self.assertIn("getAttribute('data-entrance-held') === 'pause'", self.code)
        self.assertRegex(self.code, r"phase === 'running' \|\| phase === 'tail' \|\| routeHeld \? wait\('settled', signal\)")

    def test_composer_compiles_the_target_variant(self):
        self.assertIn("compileFor(three, gl, scene, camera, composer)", self.code)
        self.assertRegex(self.code, r"gl\.setRenderTarget\(target\)\s*compiling = gl\.compileAsync\(scene, camera\)")


class BridgeFrameStatsTests(unittest.TestCase):
    def test_draw_calls_cover_every_pass(self):
        script = r"""
globalThis.window = { location: { search: '?3d-preview' } }; globalThis.document = { visibilityState: 'visible' };
const b = await load(process.argv[2], 'bridge');
// a renderer whose info auto-resets per render call, like three's
const info = { autoReset: true, render: { calls: 0, triangles: 0 }, memory: {}, reset() { this.render.calls = 0; this.render.triangles = 0; } };
const gl = { info, domElement: { width: 1, height: 1, toDataURL: () => '' }, getContext: () => ({ getExtension: () => null }),
  render() { if (info.autoReset) info.reset(); info.render.calls += 2; info.render.triangles += 100; } };
const composer = () => { gl.render(); gl.render(); gl.render(); };    // scene pass + two fullscreen passes
b.installBridge({ gl, scene: {}, camera: { rotateZ() {}, updateMatrixWorld() {} }, render: composer });
const r = {};
r.before = window.__3d.info().drawCalls;                             // nothing drawn by the bridge yet: the renderer's last
window.__3d.frame();
r.calls = window.__3d.info().drawCalls; r.tris = window.__3d.info().tris; r.autoResetRestored = info.autoReset;
console.log(JSON.stringify(r));
"""
        o = run_node(self, script, WEB / "bridge.ts")
        self.assertEqual(o["before"], 0)
        self.assertEqual(o["calls"], 6)          # all three passes, not just the last one (2)
        self.assertEqual(o["tris"], 300)
        self.assertTrue(o["autoResetRestored"])


if __name__ == "__main__":
    unittest.main()
