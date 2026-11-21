"""Runs the DOM-only web assets (entrance-gate.ts, shader-guard.ts, bridge.ts frame stats) under node.

Each module is transpiled with the repo's typescript and imported by a script that fakes only the
DOM it touches (an EventTarget with attributes, a renderer with `debug` and `info`).
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
const t0 = Date.now();
r.timeout = await gate.whenEntrance('settled', { timeoutMs: 30 });
r.timeoutWaited = Date.now() - t0 >= 25;
r.zeroTimeout = await gate.whenEntrance('settled', { timeoutMs: 0 });
r.listenersAfterTimeout = listeners;

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
        self.assertEqual(o["abort"], "rejected:AbortError")
        self.assertEqual(o["listenersAfterAbort"], 0)
        self.assertEqual(o["preAborted"], "rejected:AbortError")
        self.assertEqual(o["removedMidWait"], "none")
        self.assertEqual(o["scopedBefore"], "waiting")
        self.assertEqual(o["scopedAfter"], "phase")
        self.assertEqual(o["listenersEnd"], 0)


class ShaderGuardTests(unittest.TestCase):
    def test_verdict_and_handler(self):
        script = r"""
const g = await load(process.argv[2], 'guard');
const r = {};
r.empty = g.shaderVerdict([], null);
r.clean = g.shaderVerdict([], [{}, { name: 'a', diagnostics: { runnable: true, programLog: 'warning only' } }]);
r.dead = g.shaderVerdict([], [{ name: 'MergedPass', diagnostics: { runnable: false, programLog: '', fragmentShader: { log: "ERROR: 0:58: 'LinearTransferOETF' : function already has a body" } } }]);
r.errorFirst = g.shaderVerdict(['from handler'], [{ diagnostics: { runnable: false, programLog: 'x' } }]);

const logged = []; const orig = console.error; console.error = (...a) => logged.push(a.join(' '));
const renderer = { debug: { checkShaderErrors: false, onShaderError: null }, info: { programs: [] } };
const seen = [];
const guard = g.guardShaders(renderer, (reason) => seen.push(reason));
r.checksOn = renderer.debug.checkShaderErrors;
r.beforeFailure = guard.check();
const gl = { getProgramInfoLog: () => '', getShaderInfoLog: (s) => (s === 'fs' ? "  ERROR: 0:64: 'sRGBTransferOETF' : function already has a body\n" : '') };
renderer.debug.onShaderError(gl, {}, 'vs', 'fs');           // three calls this at the program's first use
console.error = orig;
r.seen = seen; r.logged = logged.length === 1 && logged[0].includes('sRGBTransferOETF');
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
        self.assertTrue(o["checksOn"])                               # the guard turns checks back on
        self.assertEqual(o["beforeFailure"], {"ok": True})
        self.assertEqual(o["seen"], ["ERROR: 0:64: 'sRGBTransferOETF' : function already has a body"])
        self.assertTrue(o["logged"])                                 # the handler replaces three's log, so it logs
        self.assertFalse(o["afterFailure"]["ok"])
        self.assertEqual(o["diagnosticsOnly"], {"ok": False, "reason": "p: link failed"})
        self.assertTrue(o["restored"])


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
