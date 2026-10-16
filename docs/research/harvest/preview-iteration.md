# R10: Preview + iterate-with-user tooling for the `3d` skill

Researched 2026-10-16. Grades: [V] official, [B] measured locally, [P] practitioner, [U] unverified/untested.
Nothing was installed, no servers started, no browser launched. Everything marked [B] is a local version check or a HEAD request.

## 0. Verdict

Build ONE static file, `viewer.html` (~600-900 lines, no build step), plus a ~120-line Python stdlib `serve.py`. Load three r186.1 from jsDelivr through an importmap. Do not vendor or fork any existing viewer. Borrow patterns and, where licences allow, ideas from three-gltf-viewer (MIT) and the czlonkowski template (check licence). No existing viewer has compare, shot list, versions and feedback, and all the plausible bases need Vite or a submodule build.

- Mode A (standalone assets): `serve.py` serves `.3d/preview/` from the project, so the viewer opens `http://localhost:<port>/viewer.html`. The skill's own server is the agent's to start. It is not the user's dev server.
- Mode B (live scene in the user's app): the agent never starts or kills the dev server (project CLAUDE.md, memory `dev-server-is-users-to-run`). Two options, both tell the user what to do:
  1. Drop-in `3d-preview-bridge.js` (a ~60-line module). The user's app imports it behind `?3d-preview`. It exposes `window.__3d = { shots, setShot(name), frame(n), capture(name) }` and a floating notes widget. Notes POST to the skill's `serve.py` (CORS enabled).
  2. Zero-edit fallback: the agent asks the user for the dev URL and a scroll/URL contract, then captures through Playwright (section 3) against the user's already running server. Read-only use of their server is fine.
- Feedback is a JSONL file the agent reads back with `tail`. It is not a database.

Plain-language rationale for "single file + importmap": three's own editor does exactly this (importmap, CDN for Draco) but depends on repo-relative `../build/` paths and a service worker, so it cannot be lifted as-is [P, fetched 2026-10-16 raw.githubusercontent.com/mrdoob/three.js/dev/editor/index.html].

## 1. Existing viewers: borrow vs build

| Candidate | Licence | What it gives | Why not a base | Source / grade |
|---|---|---|---|---|
| donmccurdy/three-gltf-viewer | MIT | Drag-drop GLB, three.js, dat.gui, gltf-validator, simple-dropzone | Vite 6 app, three ^0.176 (stale vs r186), no compare/shots/notes. Borrow: gltf-validator integration idea, camera-fit code | github.com/donmccurdy/three-gltf-viewer, package.json fetched 2026-10-16 [V] |
| Khronos glTF-Sample-Viewer | Apache-2.0 | Reference-quality PBR, tone-mapping, debug channels, HDR env, validator, URL params `model`, `noUI`, `yaw`, `pitch`, `distance`, downloads rendering + camera properties | Own WebGL2 renderer via submodule, Vite build, no releases. Its renderer is NOT three.js, so it shows "reference PBR", not what the user's three app will draw. Useful as an optional "ground truth" cross-check link only | github.com/KhronosGroup/glTF-Sample-Viewer [V] |
| Google model-viewer 4.4.0 | Apache-2.0 | Web component; AR (Quick Look / Scene Viewer); loads from `cdn.jsdelivr.net/npm/@google/model-viewer@4.4.0/dist/model-viewer.min.js` (200 OK) | Own three fork internally; no raw access to a user's three scene; no stats. Useful as optional Mode A "send to phone AR" (`ar` attribute), not core | npm view + HEAD [B]; docs page returned no feature text via fetch, so attribute names (`camera-orbit`, `exposure`, `tone-mapping`, `toBlob`) are [P]/[U] until read from modelviewer.dev |
| three.js editor | MIT | Full editor, scene graph, import | Repo-relative paths, service worker, far too heavy for preview | [P] |
| gltf.report (donmccurdy) | MIT (author's repo, not re-checked) | Stats, texture/material inspector, optimisation | Hosted service; cannot be scripted; good for the user as a link in the final handoff, not part of the loop | [U] licence not re-checked |
| Babylon Sandbox | Apache-2.0 | Drop GLB, inspector | Different engine; skip | [P] |
| czlonkowski blender-web-3d viewer template | check `LICENSE` in upstream repo (the scan copy has no LICENSE; `SOURCE.txt` pins commit 858762f, 2026-09-23) | Vite + three r186, AgX, Draco+KTX2+meshopt registered, `?stats`, `?debug`, `?quality`, `window.__viewer.frame(n)`, fixed-dt capture | Vite project; ideas only. Copy nothing until licence confirmed | local `docs/research/community-scan/sources/github/czlonkowski__blender-web-3d-skill__blender-web-3d/assets/viewer/README.md` [B] |

Hard-won trap from the czlonkowski reference (valuable, adopt it): when the page is hidden/occluded, `requestAnimationFrame` never fires, `THREE.Timer` delta is 0, and screenshots show a stale or black frame with no errors. Check `document.visibilityState` first. Fix: a debug hook that drives N frames synchronously with fixed dt 1/60, with `preserveDrawingBuffer: true` in debug mode, then `canvas.toBlob` (reference file `references/threejs-viewer.md`, "occluded-window trap" section) [P, local].

### Verified CDN assets (HTTP 200, 2026-10-16) [B]

Pin everything to `three@0.186.1` (npm latest on 2026-10-16; modified 2026-09-24).

```html
<script type="importmap">{"imports":{
 "three":"https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js",
 "three/addons/":"https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/"
}}</script>
```

- GLTFLoader, OrbitControls, RGBELoader (or HDRLoader, whichever r186 names it; check export in `examples/jsm/loaders/`), KTX2Loader, DRACOLoader, `utils/BufferGeometryUtils.js`, `environments/RoomEnvironment.js` (200).
- Decoders: `.../examples/jsm/libs/draco/gltf/` (`draco_decoder.wasm` 200 `application/wasm`, `draco_wasm_wrapper.js` 200), `.../libs/basis/` (`basis_transcoder.wasm` 200), `.../libs/meshopt_decoder.module.js` (200). Set `dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/libs/draco/gltf/')` and `ktx2Loader.setTranscoderPath('.../libs/basis/')`.
- unpkg mirror of three also 200. Keep unpkg as a documented fallback; jsDelivr is primary.
- HDRI: three's example textures are NOT in the npm package. Working: `https://cdn.jsdelivr.net/gh/mrdoob/three.js@r170/examples/textures/equirectangular/royal_esplanade_1k.hdr` (200; pinned to r170, file unlikely to change) and `https://threejs.org/examples/textures/equirectangular/venice_sunset_1k.hdr` (200). Poly Haven CC0: `https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_03_1k.hdr` (200). The `raw.githubusercontent.com` dev/r186 paths returned 404, so do not use them. Ship `RoomEnvironment` (procedural, zero download) as the default so the viewer works offline-ish; HDRIs are a dropdown of 3 and a local `env/` folder drop-in.
- `file://` does not work (ES modules + importmap need an origin) [P], hence `serve.py`.
- Offline: the skill should cache the CDN files into `.3d/preview/vendor/` on first run (`serve.py --vendor`, plain urllib download) and rewrite the importmap. Make this optional; the default is CDN.

## 2. Serving: `serve.py` (stdlib only)

Python 3.12 is present [B]. Subclass `http.server.SimpleHTTPRequestHandler` in a `ThreadingHTTPServer`, bind `127.0.0.1` only, default port 5183 (avoid Next's 3000 and Vite's 5173/5178).

Required behaviour:
- MIME map: `.glb` `model/gltf-binary`, `.gltf` `model/gltf+json`, `.hdr` `application/octet-stream`, `.ktx2` `image/ktx2`, `.wasm` `application/wasm` (needed for streaming compile; Python 3.12's `mimetypes` already knows wasm, but set explicitly), `.mjs`/`.js` `text/javascript`, `.jsonl` `text/plain`.
- `Cache-Control: no-store` on everything. Otherwise v2 of `model.glb` is served from cache; this is the same class of stale-asset failure as the project's stale stylesheet. Versions use distinct filenames (`v001.glb`, `v002.glb`) so cache would be fine, but `manifest.json` and `feedback.jsonl` are mutable.
- CORS `Access-Control-Allow-Origin: *`, `Allow-Methods: GET, POST, OPTIONS`, `Allow-Headers: content-type`, and an `OPTIONS` handler returning 204. Needed only for Mode B (the user's app on another port POSTs to the skill server).
- `POST /feedback` appends one JSON line (with server-side `ts`, `id`) to `feedback.jsonl`, `fsync`. `POST /shot/<version>/<name>.png` writes a capture. `GET /manifest.json` is just a file. Cap body at 20 MB, validate names with `^[a-z0-9_-]+$` (no path traversal).
- `GET /api/versions` optional; simpler: the agent writes `manifest.json` and the viewer reads it.
- Print the URL on start, write the PID to `.3d/preview/serve.pid`. Agent starts this server (it is the skill's, not the dev server) and stops it when done.

Grade: standard library behaviour [P]; the exact `mimetypes` coverage for `.glb`, `.ktx2`, `.hdr` on 3.12 was not checked, hence the explicit map.

## 3. Headless capture of every shot

### Recipe (confidence-graded)

Environment found [B]: Chrome 155.0.8059.80 at `/Applications/Google Chrome.app`; Python `playwright` 1.60.0 CLI present at `/Library/Frameworks/Python.framework/Versions/3.12/bin/playwright`; no Playwright browser cache (`~/.cache/ms-playwright`, `~/Library/Caches/ms-playwright` absent); `npx playwright` not installed (npx wanted to download 1.64.1, so it would install: do not run it). `ffmpeg` 8.0.1 present with `ssim`, `psnr`, `blend`, `hstack`, `tile`, `xfade` filters; Pillow 12.2.0 present; node v24.16.0.

So: drive the user's installed Chrome through Playwright with `channel="chrome"` (no browser download) from Python or Node, whichever the project already has. If neither is available, preflight proposes `pip install playwright` or uses CLI fallback.

```python
# capture.py (sketch)
from playwright.sync_api import sync_playwright
ARGS_MAC   = ["--use-angle=metal", "--ignore-gpu-blocklist", "--enable-webgl"]            # try first on Apple silicon
ARGS_SOFT  = ["--use-gl=angle", "--use-angle=swiftshader-webgl", "--enable-unsafe-swiftshader"]  # Linux/CI or if Metal fails
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=ARGS_MAC)
    pg = b.new_page(viewport={"width":1280,"height":720}, device_scale_factor=1)
    pg.goto(url + "?debug&shots=1")
    info = pg.evaluate("""() => { const c=document.createElement('canvas');
        const gl=c.getContext('webgl2'); if(!gl) return null;
        const e=gl.getExtension('WEBGL_debug_renderer_info');
        return e? gl.getParameter(e.UNMASKED_RENDERER_WEBGL):'webgl2-ok' }""")
    assert info, "no WebGL context; retry with ARGS_SOFT"
    pg.wait_for_function("window.__3d && window.__3d.ready")
    for name in pg.evaluate("__3d.shotNames()"):
        pg.evaluate("n => __3d.setShot(n)", name)
        pg.evaluate("__3d.frame(120)")              # fixed dt 1/60, settles damping/intro
        data_url = pg.evaluate("__3d.capture()")    # canvas.toDataURL('image/png') right after frame()
        # write to .3d/shots/<version>/<name>.png
```

Confidence:
- Flag spelling for the software path. `--use-gl=angle --use-angle=swiftshader-webgl --enable-unsafe-swiftshader` is the documented WebGL fallback; `--use-angle=swiftshader` is a different (GLES driver) route and the two are not interchangeable [P: macmyths.com/how-to-capture-webgl-without-a-gpu, fetched 2026-10-16]. Remotion's flag docs cover the same family (remotion.dev/docs/chromium-flags; surfaced in search, not read) [U].
- SwiftShader on macOS. A 2016 Chromium commit says SwiftShader headless was not supported on macOS and the physical GPU is used instead (chromium.googlesource.com commit d99a9664, surfaced in search, 2016, stale) [P/stale]. So on a Mac, expect real GPU via Metal-ANGLE in headless; software flags may be ignored. Grade of "ARGS_MAC works headless on Apple silicon with Chrome 155": [U]. First thing the skill should do is probe, not assume.
- Launching does not guarantee a WebGL context; always create a context and read the renderer string, and reject all-black or constant canvases (stddev check) [P, macmyths].
- Headless detection concerns (SwiftShader renderer string as a bot tell) are irrelevant to localhost but mean do not use this recipe against third-party sites [P].
- Capture method: `canvas.toDataURL` immediately after a synchronous `frame(n)` with `preserveDrawingBuffer: true` avoids the occluded-window and rAF problems entirely [P: czlonkowski `references/threejs-viewer.md`, local]. `page.screenshot` only for full-page Mode B (DOM + canvas) and then needs a settle wait; the scroll-animation skill's rule applies: scroll to progress, not pixel offset, wait ~2.5 s, then screenshot (`~/Documents/Personal/Projects/scroll-animation-skill/skills/scroll-animation/references/verification.md` sections 1) [P, local].
- WebGPU/TSL canvases: headless screenshots of WebGPU may be black or unsupported (agent-browser.dev/webgpu, surfaced in search only) [U]. Make the viewer default to WebGLRenderer; flag WebGPU as "capture not guaranteed".
- Headed fallback: `headless=False` with a visible, un-occluded window always works for WebGL on macOS [P]. Ask the user only if the probe fails twice.

### CLI-only fallbacks (no browser)
1. Blender headless `blender -b file.blend -o //out -F PNG -f 1` per camera in the shot list (EEVEE Next or Cycles). This is not the web renderer; label it "Blender reference render". Good for comparing against the reference image.
2. For GLB: Blender import then render, or `model-viewer`'s Node screenshot is not available offline [U]. No `npx` tool for GLB thumbnails was verified; do not recommend one.
3. For image sequences / video loops: `ffmpeg` contact sheet `-vf "select='not(mod(n,10))',scale=320:-1,tile=6x4"` [P], and `ffprobe` for fps/size.

### Diff and metrics
| Tool | Licence | Install | Use |
|---|---|---|---|
| `ffmpeg -i a.png -i b.png -lavfi "ssim=stats_file=ssim.log;[0][1]psnr" -f null -` | present [B] | none | primary: zero-install SSIM/PSNR score per shot |
| `ffmpeg ... -filter_complex "blend=all_mode=difference"` | present [B] | none | difference image for visual diff |
| Pillow `ImageChops.difference` | HPND | present [B] | heatmap, bbox of change, threshold counts |
| pixelmatch 8.0.0 | ISC [B npm] | npm | optional JS tool with anti-aliasing tolerance |
| odiff-bin 4.5.0 | MIT [B npm] | npm | optional, faster, native |
Recommendation: ffmpeg + Pillow, nothing to install. Score is a hint for the agent; the user judges. Never gate on pixel equality (GPU differences between machines make cross-machine baselines unreliable [P]); gate on same-machine, same-flags version-to-version comparisons.

## 4. Iteration UX: minimal subset

Evidence is thin: the search returned only a comparison article (morphic.com/resources/alternatives/syncsketch-alternatives, 2026) saying Frame.io has frame-specific, range and pinned comments with drawing, share-link commenting without sign-up, and version stacks for side-by-side; Wipster pins time-coded comments to a point/box and lets reviewers mark each version approved or not [P, secondary source]. I could not verify ftrack or Figma specifics, so the following is a design judgement [U]:

What gives most value per effort, in order:
1. Notes tied to (version, shot). Free text, one tap. This is the 80% case.
2. Per-version status: `approved` / `changes` (two buttons). Gives the agent a clear stop signal and keeps "which version is good" out of chat.
3. A pin on the image at (x,y) normalised to the canvas with the note. Cheap (a click handler and a dot) and removes "the left edge, near the top" ambiguity. Store `pin:[x,y]` in 0..1.
4. Severity tag (`must`/`nice`) as optional single field.
Skip: threaded replies, drawing tools, time-coded ranges (only needed for video loops, add `t` seconds then), user accounts, realtime sync.

Agent read-back: the agent runs `tail -n +<last-seen> feedback.jsonl`, summarises notes grouped by shot, replies in chat, and writes `resolved` entries (append-only, mirrors the project-context convention). Every iteration ends with the agent saying which note ids the new version addresses.

## 5. Data formats

```
.3d/preview/
  viewer.html           # single static file, importmap, no build
  serve.py              # stdlib server + POST handlers
  manifest.json         # versions + shots + refs index (agent writes)
  shots.json            # from the brief
  versions/v001/model.glb  v001/meta.json  v001/shots/<name>.png
  versions/v002/...
  refs/<name>.jpg       # user reference images
  env/                  # optional local HDRIs
  feedback.jsonl        # append-only, user writes via viewer, agent reads
```

`shots.json` (single source for viewer, capture script, and the brief's shot list):
```json
{"viewport":[1280,720],
 "shots":[{"name":"hero","fov":35,"position":[2.4,1.2,3.1],"target":[0,0.6,0],
           "ref":"refs/hero.jpg","env":"studio","exposure":1.0,"toneMapping":"ACESFilmic",
           "pose":{"animation":null,"t":0}, "notes":"low angle, rim light left"}]}
```
Mode B shots use `{"name":..,"url":"/?3d-preview","scroll":0.5}` (progress, not pixels) instead of position/target.

`manifest.json`:
```json
{"versions":[{"id":"v001","glb":"versions/v001/model.glb","created":"2026-10-16T12:00:00Z",
  "summary":"blockout","status":"changes","stats":{"tris":48210,"drawCalls":23,"texMB":18.4,"glbKB":1320}}],
 "current":"v002"}
```
`feedback.jsonl` (one object per line, append-only):
```json
{"id":"f_20261016_001","ts":"...","version":"v002","shot":"hero","kind":"note|status|resolved",
 "text":"rim light too hot","pin":[0.31,0.22],"severity":"must","status":null,"refs":["f_..."]}
```
Corrections are new lines referencing earlier ids; never rewrite history.

Stats source: `renderer.info.render.triangles`, `.calls`; texture memory estimated from `texture.image` width x height x 4 x 1.33 (mip) or from KTX2 container size when compressed; GLB size from `Content-Length`/HEAD. Texture memory is an estimate; label it so [P].

## 6. Features ranked by value / cost

| # | Feature | Value | Cost | Notes |
|---|---|---|---|---|
| 1 | Load current version + version dropdown (v1..vN) | high | low | manifest.json |
| 2 | Named camera presets from shots.json (hotkeys 1-9) | high | low | FOV, position, target |
| 3 | Screenshot of every shot (headless + button) | high | med | section 3 |
| 4 | Notes per (version, shot), status approve/changes | high | low | section 4-5 |
| 5 | Reference compare: side-by-side, opacity overlay slider, split wipe | high | low | CSS: ref `<img>` over canvas with `opacity` / `clip-path: inset(0 X% 0 0)`; match aspect by letterboxing |
| 6 | Stats panel (tris, calls, tex MB, GLB size) | high | low | `renderer.info` |
| 7 | A/B between two versions (same camera) | high | med | two canvases or render-to-texture; simplest: two renderers sharing one camera state |
| 8 | Exposure + tone-mapping toggles (None, Linear, Reinhard, Cineon, ACES, AgX, Neutral) | med | low | `renderer.toneMapping` |
| 9 | Environment switch (Room, 3 HDRIs, local) | med | low | PMREM |
| 10 | Turntable (auto-rotate) | med | low | OrbitControls `autoRotate` |
| 11 | Pin-on-image annotation | med | low-med | normalised coords |
| 12 | Onion-skin for image sequences / video loops | med | med | stack frames at 40% opacity, or `blend` in ffmpeg offline |
| 13 | Wireframe / normals / UV-checker / overdraw debug | med | med | material override |
| 14 | Contact sheet of all shots per version (ffmpeg `tile` or Pillow) | med | low | evidence artifact |
| 15 | SSIM/PSNR score + diff image vs reference or previous version | med | low | ffmpeg |
| 16 | gltf-validator report | med | med | `gltf-validator` npm 2.0.0-dev.3.10 is what three-gltf-viewer uses [V]; offer as optional |
| 17 | AR hand-off via model-viewer | low | low | Mode A only |

Build 1-10 in the first cut; 11-15 next; 16-17 optional.

## 7. How the user's own skills preview things (reuse)

- scroll-animation-skill: drive a real headless browser from a script and read numbers; scroll to progress; wait for glides to settle; tile screenshots into a contact sheet; read state (`getAnimations()`, `getBoundingClientRect`, `data-scene-state`) rather than eyeballing; scripts resolve Playwright from the project's `node_modules`, then a skill-local install, then print an install hint; exit codes `0` pass, `1` check failed, `2` usage/unavailable [P, local `references/verification.md`]. Adopt the same resolution order and exit codes in `capture.py`/`capture.mjs`. Adopt `?motion-debug`-style opt-in: `?3d-preview`.
- site-capture: explicitly "knowledge, not a pipeline", ships no scripts (`~/.claude/skills/site-capture/SKILL.md`) [B local]. Its stance matches this: the skill should ship small templates (`viewer.html`, `serve.py`, `capture.py`), not a framework.
- generate-image / generate-video: not read in this pass (only listed in `~/.claude/skills`). Gap: confirm whether they already write outputs to a conventional folder the 3d skill can reuse for refs.
- scroll-driven-video skill: its own note says final judgement needs real Safari/iOS, not headless Chromium [P, local SKILL.md line ~109]. Carry over: Mode B captures are evidence of layout/progress, not of Safari rendering.

## 8. Mode B specifics (user's dev server)

- The agent asks: "Please run your dev server and give me the URL. Open it with `?3d-preview`." It does not start or kill it.
- Next dev note from this repo: after any CSS change plus server restart a stale tab holds old CSS; when comparing a live scene, open a fresh tab or capture through a fresh headless context (always fresh, so headless is immune) [P, project CLAUDE.md].
- Bridge contract (`window.__3d`): `ready`, `shotNames()`, `setShot(name)`, `frame(n)`, `capture()` returning a PNG data URL, `stats()` returning `{tris,calls,texMB}`. For R3F apps the bridge reads `gl.info` and the default camera via a tiny `useThree` component the agent adds, then removes at the end (agent must list the added file in the handoff). For scroll-driven scenes `setShot` maps to scroll progress.
- Notes widget in-app is optional. Simpler: the user views the app and the standalone viewer for the same version side by side and writes notes in the standalone viewer. Recommend this default; the in-app widget is extra code in the user's repo.
- Never leave the bridge in production code; guard with `import.meta.env.DEV`/`process.env.NODE_ENV !== 'production'` and ask before adding it, since it is a change in the user's repo.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Headless WebGL fails or renders black on macOS | probe + renderer-string check, two arg sets, headed fallback, `frame(n)` + `toDataURL` path |
| CDN down / offline | `serve.py --vendor` caches to `vendor/`; unpkg fallback |
| three upgrades break importmap | pin `0.186.1`; preflight prints pinned vs `npm view three version` |
| Viewer renders differently from the user's app (colour space, tone mapping, env) | viewer exposes the same toggles; shots.json records renderer settings; Mode B for ground truth; say so in the handoff |
| WebGPU/TSL scenes not capturable headless | default WebGL; flag unsupported |
| Hidden-tab rAF stall | fixed-dt `frame(n)` hook |
| Feedback file clobbered by two writers | append-only, one line per POST, ids server-generated |
| Cross-origin POST from user's app | CORS in `serve.py`; loopback only; no secrets stored |
| Large GLBs (>50 MB) slow to load | show progress; stats panel warns |
| Licence contamination from copying viewers | write `viewer.html` fresh; borrow ideas only from non-MIT/Apache sources |

## 10. Gaps (unresolved)

1. No measured headless-WebGL run on this Mac (Chrome 155 + Playwright 1.60 python). The recipe is [U] until probed. Cheapest test: a 10-line page that creates a WebGL2 context and prints the renderer.
2. Playwright browsers not installed; whether `channel="chrome"` works in Playwright 1.60 with Chrome 155 is [U] (documented feature, not tested).
3. model-viewer attribute list and `toBlob` details not verified (docs page returned no content via fetch).
4. gltf.report licence and czlonkowski template licence not confirmed.
5. frame.io / SyncSketch / ftrack / Figma behaviours came from one secondary article; the "minimum subset" is design judgement.
6. generate-image / generate-video skill capture conventions not inspected.
7. The r186 HDR loader class name (`HDRLoader` vs `RGBELoader`) not verified; check `examples/jsm/loaders/` listing before writing viewer.html.
8. Image-sequence onion skin and video-loop review (frame-accurate scrubbing, `requestVideoFrameCallback`) not researched.

## Sources
- https://github.com/donmccurdy/three-gltf-viewer (MIT; package.json three ^0.176, Vite ^6.4.2) fetched 2026-10-16 [V]
- https://github.com/KhronosGroup/glTF-Sample-Viewer (Apache-2.0) fetched 2026-10-16 [V]
- https://github.com/google/model-viewer (Apache-2.0); npm `@google/model-viewer` 4.4.0 [B]
- https://raw.githubusercontent.com/mrdoob/three.js/dev/editor/index.html fetched 2026-10-16 [V]
- https://macmyths.com/how-to-capture-webgl-without-a-gpu/ fetched 2026-10-16 [P]
- https://chromium.googlesource.com/chromium/src.git/+/d99a9664c873fc38e226e33bc92da974fb852da3 (2016, search snippet only) [P/stale]
- https://www.remotion.dev/docs/chromium-flags (search snippet only) [U]
- https://morphic.com/resources/alternatives/syncsketch-alternatives (search snippet only) [P]
- Local: `docs/research/community-scan/sources/github/czlonkowski__blender-web-3d-skill__blender-web-3d/` (assets/viewer/README.md, references/threejs-viewer.md); `~/Documents/Personal/Projects/scroll-animation-skill/skills/scroll-animation/references/verification.md`; `~/.claude/skills/site-capture/SKILL.md`; `~/.claude/skills/scroll-driven-video/SKILL.md`; project `CLAUDE.md` (eagle-website).
- HEAD checks and `npm view` run 2026-10-16 [B].
