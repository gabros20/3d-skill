# Preview and iterate

Purpose: The loop that shows each version to the user, captures evidence for every shot, collects their notes and stops when they approve.

Read when:
- A build step produced something the user must look at, or notes came back.
- Setting up how the user will review (standalone viewer or their live app).

Skip when:
- Checking one claim against evidence only (→ [shared-verification](shared-verification.md).
- The shot list does not exist yet (→ [brief-spec](brief-spec.md)).

Inputs:
- `.3d/shots.json`, a built asset or a running app URL, `3D.md` budgets.

Produces:
- `.3d/versions/vNNN/`, `.3d/evidence/vNNN/<shot>.png`, read-back notes, a version-log line in `3D.md`.

All commands run from the skill root and write under the project's `.3d/`.

## Modes

**A. Standalone.** Assets under `.3d/` viewed in the skill's own viewer.
```
scripts/preview serve [--root .3d] [--port 4173]
```
Routes: `/` viewer, `/api/state` (versions, shots, refs, feedback), everything else from `--root`. `POST /feedback` (server adds id `f0001…` and `ts`; kind `note|status|resolved`; `x`,`y` normalised 0..1; `version` required; status `approved|changes`). `POST /shots` merges the viewer's current camera into `.3d/shots.json`. Own port, loopback only. Viewer keys: 1–9 shots, `[` `]` versions. You start it; stop it when the session ends. Open the printed URL for the user.

**B. Live in the user's app.** The scene runs in their project, opened with `?3d-preview`. The `window.__3d` bridge (`assets/web/bridge.ts`) exposes `window.__3d = { ready, shots(), loadShots(shots), setShot(id), frame(n), capture(), info() }` (`capture()` returns a PNG data URL; a shot with `scroll` calls the app's `setProgress`). `scripts/preview capture` drives it, so capture is deterministic. Adding the bridge is a change in their repo: ask first, guard it to development builds, list the added files in the handoff, and remove it at the end if asked.

**The developer owns their dev server.** Never start, kill or restart it. Ask: "Run your dev server and give me the URL." Read-only use of a server they already run is fine. After a CSS change plus a server restart a tab that stayed open can show stale styles; ask them to open a fresh tab before judging ([shared-debug](shared-debug.md)). Headless capture opens a fresh context, so it is immune.

Default to A for assets and look-dev; use B for anything whose truth is the page (scroll, layout, post stack). Mode B captures prove layout and progress, not Safari rendering.

## The loop

1. `scripts/preview new-version [--note "<what changes>"]` creates `.3d/versions/vNNN/` (prints `{"version","dir"}`, writes `manifest.json`); drop the asset in that dir (the viewer opens the first `.glb/.gltf`, else image, else video). One version per change-set, never edit a shown version.
2. Build the change into that version.
3. `scripts/preview capture [--version vNNN] [--url URL] [--shots .3d/shots.json]` writes `.3d/evidence/vNNN/<shot>.png` for EVERY shot, not only the one you changed. It appends `?3d-preview` to `--url`, loads the project's `shots.json`, then per shot does `setShot` → `frame(--settle, default 120)` → `capture()` (default `--size 1600x900`; flags `--headed --timeout --root`). Read the report: renderer string and probe path (default, gpu, software flags). Software-only GL is a warning; no WebGL, a blank or constant frame, or `ready` never true exits 1: a failed capture, not evidence.
4. Compare: against the reference image (side by side, by eye, plus palette and luma numbers from `scripts/ref-extract`) and against the previous version:
   `scripts/preview diff A B` (two images or two version ids) writes `.3d/diffs/A__B/{side_by_side,blend,difference}` and prints JSON `ssim`, `psnr_db` (`null` with `identical:true` when equal); meaning in [shared-verification](shared-verification.md).
5. Tell the user: URL, version id, what changed, and which note ids this version addresses.
6. `scripts/preview feedback [--version vNNN]` prints their notes by version and shot (`--json` available; append-only `.3d/feedback.jsonl`; kinds `note`, `status`, `resolved`).
7. Map notes to changes, then go to step 1.

## Iteration rules

- ONE change-set per version; a note that implies two independent changes becomes two versions only if they could be wrong separately.
- Group notes by shot; restate each in your words with the intended change before building. A note you cannot map to a parameter gets a question, not a guess.
- Conflicting notes: apply the later one, say so, keep the earlier id referenced.
- Do not "also improve" unrequested things between versions; list them as proposals.
- Corrections are new lines referencing earlier ids; never rewrite `feedback.jsonl`.
- Stop when the user marks a version `approved` (status note) or says so. Then write the final version-log line in `3D.md` with budget numbers from [shared-performance](shared-performance.md).
- Three rounds on the same shot without convergence: pause, show a before/after strip, and ask whether the reference or the brief should change.

## Traps

- Capturing only the changed shot and missing a regression in another.
- A hidden or occluded page makes `requestAnimationFrame` stall and screenshots go stale: capture through `scripts/preview capture` (it steps `frame(n)`) or check `document.visibilityState`.
- Trusting a headless fps number from this loop ([shared-verification](shared-verification.md).
- Leaving the preview server running or the bridge in the user's code after approval.
