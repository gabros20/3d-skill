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

| Need | Channel |
|---|---|
| Inspect, export, bake, render, batch, QA, anything that must reproduce | Headless CLI |
| User is watching, live modelling, their open scene, viewport screenshots | MCP bridge to a GUI Blender |
| Both | Iterate over MCP, then save the steps as an idempotent script and re-run headless on the master file |

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
6. Return data as one JSON line or a JSON file; never regex Blender's log (the format changed in 5.0).
7. Run from the user's project root and call scripts as `<skill>/assets/blender/<x>.py` (as in the block above); `.3d/` paths resolve against cwd. One Blender process at a time per agent. Shipped scripts: `<skill>/assets/blender/inspect_scene.py`, `export_web.py`, `render_shots.py` (flags in each docstring).
8. Never save the `.blend` after `export_web.py`; modifiers were applied in that session only.

## MCP bridges

Both execute arbitrary Python inside Blender with no guard (delete files, read the network). Say so, get explicit consent, ask the user to save first, prefer an isolated profile or VM when the machine holds secrets (the official server says this itself).

| | Community `mcp-for-blender` | Official Blender Lab MCP |
|---|---|---|
| Licence | MIT | GPL-3.0 |
| Blender | 3.0+ | 5.1+ |
| Install | `uvx mcp-for-blender`; add-on via `uvx mcp-for-blender install-addon`, enable it, N-panel → start server | add-on from the Blender Lab repo (two drag-drops, Allow Online Access on) + server from git pinned by SHA |
| Extras | Poly Haven, Sketchfab, generators | `*_for_cli` tools (background Blender), bundled API docs, no assets |
| Choose when | default; 4.x; asset search wanted | first-party wanted; Blender ≥ 5.1 |

- PyPI `blender-mcp` is the community server, not the official one. The official one is installed from git: `uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@<sha>#subdirectory=mcp" blender-mcp`. Pin a reviewed SHA; pre-warm once (first build is slow). Untested here; the documented route is a clone plus `uv --directory <clone>/mcp run blender-mcp`.
- Tool names drift (the 2025 community set was replaced by a consolidated set). Read the live tool schemas; never call a remembered name.
- One MCP at a time per task. Never switch mid-task. Both bridges default to port 9876.
- The community socket has no auth: localhost only. Telemetry is opt-in and off by default; keep it off (`disable_telemetry` tool) unless the user allows it.

### Register

- Claude Code: `claude mcp add --transport stdio blender -- uvx mcp-for-blender` (`--` required; `--scope project` writes `.mcp.json`). Add `"timeout": 600000` per server for long calls; `MAX_MCP_OUTPUT_TOKENS` (default 25,000) caps screenshots and scene dumps.
- Codex: `codex mcp add blender -- uvx mcp-for-blender`, then in `~/.codex/config.toml` raise `tool_timeout_sec` (default 60) to 300+.
- `spawn uvx ENOENT` → use the absolute path to `uvx`.

### Health check (a tool list proves the server started, not that Blender is connected)

1. Community: `get_addon_status`, then `get_scene_info`, then run `print("ok")`, then one screenshot. Official: `get_objects_summary`.
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
- Viewport screenshots are not evidence for materials or render visibility (`hide_render` objects still show); render instead ([blender-lookdev-render](blender-lookdev-render.md)).
- Do not call `read_factory_settings` or delete data you did not create in the user's session.
