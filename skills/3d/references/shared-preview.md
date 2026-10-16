# Preview and iterate

Purpose: The loop that shows each version to the user, captures evidence for every shot, collects their notes and stops when they approve.

Read when:
- A build step produced something the user must look at, or notes came back.
- Setting up how the user will review (standalone viewer or their live app).

Skip when:
- Checking one claim against evidence only (→ [shared-verification](shared-verification.md)).
- The shot list does not exist yet (→ [brief-spec](brief-spec.md)).

Inputs:
- `.3d/shots.json`, a built asset or a running app URL, `3D.md` budgets.

Produces:
- `.3d/versions/vNNN/`, `.3d/evidence/vNNN/<shot>.png`, read-back notes, a version-log line in `3D.md`.

`<skill>` is the installed skill directory. Invoke scripts by that path with the USER'S PROJECT ROOT as the working directory; defaults (`.3d`) resolve against it. Never run them from the skill directory. Everything is written under the project's `.3d/`.

## Modes

**A. Standalone.** Assets under `.3d/` viewed in the skill's own viewer.
```
<skill>/scripts/preview serve [--dir .3d] [--port 4173] [--app DIR]
<skill>/scripts/preview stop        # reads .3d/preview.pid
```
Routes: `/` viewer, `/api/state` (versions, shots, refs, feedback), everything else from `--dir`. `POST /feedback` body: `version` (required), `note` and/or `status` (`approved|changes`; at least one), optional `shot`, `x`, `y` (0..1); the server adds `id` (`f0001…`), `kind` and `ts`. `POST /shots` body: one `shots.v1` shot entry, merged into `.3d/shots.json`. Own port, loopback only. Viewer keys: 1–9 shots, `[` `]` versions. The viewer loads three.js from a pinned CDN, so it needs network. It reads `.3d/look.json` (`look.v1`: `toneMapping`, `exposure`, `environment`, `background`; default neutral) so the preview matches the chosen look. You start it; stop it with `<skill>/scripts/preview stop` when the session ends. `--app DIR` also serves a static page directory at `/app/`; capture it with `--url http://127.0.0.1:<port>/app/` (`?3d-preview` is appended). Open the printed URL for the user.

**B. Live in the user's app.** The scene runs in their project, opened with `?3d-preview`. The `window.__3d` bridge (`assets/web/bridge.ts`) exposes `window.__3d = { ready, shots(), loadShots(shots), setShot(id), frame(n), capture(), info() }` (`capture()` returns a PNG data URL; a shot with `scroll` calls the app's `setProgress`). `<skill>/scripts/preview capture` drives it, so capture is deterministic. Adding the bridge is a change in their repo: ask first, guard it to development builds, list the added files in the handoff, and remove it at the end if asked.

**The developer owns their dev server.** Never start, kill or restart it. Ask: "Run your dev server and give me the URL." Read-only use of a server they already run is fine. After a CSS change plus a server restart a tab that stayed open can show stale styles; ask them to open a fresh tab before judging ([shared-debug](shared-debug.md)). Headless capture opens a fresh context, so it is immune.

Default to A for assets and look-dev; use B for anything whose truth is the page (scroll, layout, post stack). Mode B captures prove layout and progress, not Safari rendering.

## The loop

1. `<skill>/scripts/preview new-version [--note "<what changes>"] [--technique T1,T8] [--snapshot PATH...]` creates `.3d/versions/vNNN/` (prints `{"version","dir"}`, writes `manifest.json`); `--technique` records the technique ids in `manifest.json` (a version with no named technique or measured fit is not a change-set). `--snapshot` copies the given files into the version (never copy builds by hand); otherwise drop the asset in that dir (the viewer opens the first `.glb/.gltf`, else image, else video). One version per change-set, never edit a shown version.
2. Build the change into that version.
3. Capture consent first: read `capture: ask|auto` in `3D.md`. `auto` is the default for the skill's own preview server; ALWAYS ask before driving the user's app or browser (Mode B) unless it says `auto`. Capture needs python playwright + Chrome ([shared-preflight](shared-preflight.md)). Low resolution first (`--size 854x480`), full size only for approval. Then `<skill>/scripts/preview capture [--version vNNN] [--url URL] [--shots .3d/shots.json]` writes `.3d/evidence/vNNN/<shot>.png` for EVERY shot, not only the one you changed. It appends `?3d-preview` to `--url`, loads the project's `shots.json`, then per shot does `setShot` → `frame(--settle, default 120)` → `capture()` (flags `--size --headed --timeout --dir`; `--end` also captures each shot's `to` pose as `<id>_end.png`; `--pathtrace [--samples N] [--shot ID]` writes a path-traced twin `<shot>_pt.png`, only to confirm a CEILING claim per [realism-gate](realism-gate.md)). Read the report (renderer string, probe path). Software-only GL is a warning; no WebGL, a blank or constant frame, or `ready` never true exits 1: a failed capture, not evidence.
4. Compare: against the reference image (side by side, by eye, plus palette and luma numbers from `<skill>/scripts/ref-extract`) and against the previous version:
   `<skill>/scripts/preview diff A B` (two images or two version ids) writes `.3d/diffs/A__B/{side_by_side,blend,difference}` and prints JSON `ssim`, `psnr_db` (`null` with `identical:true` when equal); meaning in [shared-verification](shared-verification.md).
5. For review, `<skill>/scripts/preview board [--version vNNN]` builds a storyboard contact sheet of the version's shot captures with ids and notes. Run the fresh-critic gate ([shared-verification](shared-verification.md)) before presenting; log the round in the `3D.md` version log, append its `rounds.v1` line, and run `<skill>/scripts/preview rounds`: its verdict (continue, pass, stop) decides the next step ([realism-gate](realism-gate.md)). On pass, tell the user: URL, version id, what changed, and which note ids this version addresses.
6. `<skill>/scripts/preview feedback [--version vNNN]` prints their notes by version and shot (`--json` available; append-only `.3d/feedback.jsonl`; kinds `note`, `status`, `resolved`).
7. Map notes to changes, then go to step 1.

## Iteration rules

- ONE change-set per version; a note that implies two independent changes becomes two versions only if they could be wrong separately.
- Group notes by shot; restate each in your words with the intended change before building. A note you cannot map to a parameter gets a question, not a guess.
- Conflicting notes: ask, never pick; no unrequested improvements between versions (list them as proposals).
- Render after every stage and look at it: validation passing is not visual verification.
- Context hygiene: at every user gate, and whenever context passes about 300k tokens, checkpoint into `3D.md` (decisions, version log, open questions) and hand off or delegate. A build iteration may run as a fresh subagent fed only the brief, `3D.md`, `feasibility.json` and the last `preview match` report. Never idle-wait on a hot context.
- Tune with `<skill>/scripts/preview sweep` (N parameter variants into one labelled contact sheet plus `rank.json`; read the JSON, open the sheet for the top 2), never by regex-editing scene code. Compare motion with `<skill>/scripts/preview compare A B --stack` (synced side-by-side or stacked video).
- Corrections are new lines referencing earlier ids; never rewrite `feedback.jsonl`.
- Stop when the user marks a version `approved` (status note) or says so. Then write the final version-log line in `3D.md` with budget numbers from [shared-performance](shared-performance.md).
- Version hygiene: read the version id `new-version` prints and confirm it before capturing; never re-capture into a version whose critic round is recorded (create a new version); keep scratch work out of `.3d/versions/`.
- When the user rejects an approach, the whole family is rejected: record it in `3D.md` as rejected-with-family and ask before building anything in that family.
- On verdict `stop`, follow the MAX REACHED procedure in [realism-gate](realism-gate.md); do not start another round.
- A shot may carry `t` (seconds); the bridge's time hook applies it before capture.

## Traps

- Capturing only the changed shot and missing a regression in another.
- A hidden or occluded page makes `requestAnimationFrame` stall and screenshots go stale: capture through `<skill>/scripts/preview capture` (it steps `frame(n)`) or check `document.visibilityState`.
- Trusting a headless fps number from this loop ([shared-verification](shared-verification.md)).
- Leaving the preview server running or the bridge in user code after approval.
