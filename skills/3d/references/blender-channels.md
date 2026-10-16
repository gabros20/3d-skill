# Blender Channels

Purpose: Pick how the agent drives Blender (headless CLI or an MCP bridge), set it up, and fail safely.

Read when:
- Any task touches Blender, `.blend`, `bpy`, or "blender-mcp".
- An MCP call timed out, returned nothing, or the bridge will not connect.

Skip when:
- The GLB already exists and Blender is no longer the editor (→ [asset-pipeline](asset-pipeline.md)).

Inputs:
- `.3d/capabilities.md` (Blender path and version, MCP hints), the task: build, inspect, export or render.

Produces:
- A chosen channel, a working connection (or a reported blocker), and consent recorded for arbitrary Python.

## Decision rule

| Need | Channel | Evidence it gives |
|---|---|---|
| Inspect, export, bake, render, batch, QA, anything that must reproduce | Headless CLI | headless render (`render_shots.py`; Workbench for silhouettes) is the only evidence for materials, visibility and "done" |
| User is watching, live modelling, their open scene | MCP bridge to a GUI Blender | an MCP screenshot shows composition and state, not final look |
| Both | Iterate over MCP, then save the steps as an idempotent script ([blender-scripting](blender-scripting.md)) and re-run headless on the master | |

ALWAYS export and final-render headless: MCP calls have a wall-clock limit and exports hit it. NEVER launch a second GUI Blender on the user's machine.

## Headless CLI

```
/Applications/Blender.app/Contents/MacOS/Blender -b scene.blend --factory-startup \
  --python-exit-code 1 --python <skill>/assets/blender/<script>.py -- --flag value
```

1. Binary: `$BLENDER`, then `blender` on PATH, then the macOS path above. Missing → report `missing_tool`, propose the install (cost: free), never install.
2. Arguments run left to right: load the `.blend` before `--python`; set output options before the render action.
3. `--python-exit-code 1` is mandatory; without it a failed script exits 0.
4. `--factory-startup` keeps user add-ons from loading (reproducible; one add-on made network calls in a measured run).
5. Script args go after `--` (`sys.argv[sys.argv.index("--")+1:]`). Use absolute paths, quote them.
6. Return data as one JSON line or a JSON file; never regex Blender's log (the format changed in 5.0). Script patterns and gates: [blender-scripting](blender-scripting.md).
7. Run from the user's project root and call scripts as `<skill>/assets/blender/<x>.py` (as in the block above); `.3d/` paths resolve against cwd. One Blender process at a time per agent. The shipped script list lives in SKILL.md (Tools).
8. Never save the `.blend` after `export_web.py`; modifiers were applied in that session only.

## MCP bridges

Both execute arbitrary Python inside Blender with no guard (delete files, read the network). Say so, get explicit consent, ask the user to save first, prefer an isolated profile or VM when the machine holds secrets. Treat either as a transport and observation layer: authoring is still Python you write. One MCP at a time per task, never switch mid-task; both default to port 9876.

| | Community `mcp-for-blender` | Official Blender Lab MCP |
|---|---|---|
| Licence, Blender | MIT, 3.0+ | GPL-3.0, 5.1+ |
| Install | `uvx mcp-for-blender`; add-on via `uvx mcp-for-blender install-addon`, enable it, N-panel → start server | extension add-on (Blender Lab repo, drag the zip twice: first adds the repo) + server from git |
| Extras | Poly Haven, Sketchfab, generators, `look` multi-view | bundled version-matched API and manual search, `*_for_cli` twins, no assets |
| Choose when | default; 4.x; asset search wanted | first-party wanted; Blender ≥ 5.1; bundled docs wanted |

- PyPI `blender-mcp` is the community server, not the official one. Tool names drift: read the live tool schemas, never call a remembered name. Community socket has no auth: localhost only. Its telemetry is opt-in and off by default; keep it off (`disable_telemetry` tool) unless the user allows it.

## Official Blender Lab MCP (v1.0.3)

- Needs Blender ≥ 5.1 and **Allow Online Access** on (Preferences → System → Network, or `--online-mode`): without it the add-on shows "on" and never binds. Add-on id `mcp`; the server speaks stdio by default (`--transport http` only for clients that need it: CORS `*`, no DNS-rebinding guard, localhost only).
- Env: `BLENDER_MCP_HOST`, `BLENDER_MCP_PORT`, `BLENDER_PATH` (binary for the `_for_cli` tools).
- Install from git pinned to a tag or reviewed SHA: `uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp` (constructed from the entry point, untested here). The macOS `.mcpb` bundle install fails with "Operation not permitted" (issue #57): use uvx.
- Tool map, by job:
  - Inspect: `get_objects_summary` (bloats on big scenes: prefer `get_object_detail_summary`), `get_blendfile_summary_*` (datablocks, missing files, linked libraries, path info).
  - Act: `execute_blender_code`; return data by assigning a **dict** to `result` (a list or scalar errors). Server instructions call it a last resort.
  - See: `get_screenshot_of_area_as_image(area_ui_type)`, `get_screenshot_of_window_as_image`, `render_thumbnail_to_path`, `render_viewport_to_path` (writes a file despite a read-only hint; read the returned path).
  - Docs: `search_api_docs`, `get_python_api_docs`, `search_manual_docs`. Query before writing any unfamiliar 5.x API from memory.
  - Headless twins: `*_for_cli` run on a numbered copy of the file, 120 s cap, hang on Windows (#42).
- Execution model: runs on Blender's main thread, one request at a time, UI frozen meanwhile; 300 s socket cap, 10 MiB request cap. **No undo and no real sandbox** (it only patches `sys.exit` and blocks four operators): save a numbered copy per stage.
- Headless serving (untested here, the add-on is not installed): `blender -b file.blend --online-mode --command blender_mcp --host H --port P`.
- Windows: a second Blender can silently share a port (#63).

### Register

- Claude Code (community): `claude mcp add --transport stdio blender -- uvx mcp-for-blender`; official: the same command with the `uvx --from "git+…" blender-mcp` line above (`--` required; `--scope project` writes `.mcp.json`). Add `"timeout": 600000` per server for long calls; `MAX_MCP_OUTPUT_TOKENS` (default 25,000) caps screenshots and scene dumps.
- Codex (community): `codex mcp add blender -- uvx mcp-for-blender` (official: same, with its command), then in `~/.codex/config.toml` raise `tool_timeout_sec` (default 60) to 300+.
- `spawn uvx ENOENT` → use the absolute path to `uvx`.

### Health check (a tool list proves the server started, not that Blender is connected)

1. Community: `get_addon_status`, then `get_scene_info`, then run `print("ok")`, then one screenshot. Official: `get_objects_summary` (a tool list alone proves nothing).
2. `Cannot connect … 9876` → the add-on server is not running; walk the user through starting it. Raw probe: `nc -z -w2 localhost 9876`.
3. A disabled integration answers `Unknown command type`; check its status tool before suspecting a version bug.
4. `*_for_cli` tools need `blender` on the server's PATH; on macOS point them at a wrapper script.

### Timeouts

1. Keep each call short and idempotent: get-or-create by name, touch only what you created. Each call starts a fresh namespace; `bpy.data` persists.
2. On a timeout, inspect the scene first, never resubmit the mutation blindly.
3. Move export, bake and render to the headless CLI instead of raising limits further.
4. Save a copy per stage (`bpy.ops.wm.save_as_mainfile(copy=True, filepath=…)`).

## Traps

- A task only listed an MCP tool: that does not mean Blender is open.
- Viewport screenshots are not evidence for materials or render visibility (`hide_render` objects still show); render headless instead ([blender-lookdev-render](blender-lookdev-render.md)).
- Do not call `read_factory_settings` or delete data you did not create in the user's session.
