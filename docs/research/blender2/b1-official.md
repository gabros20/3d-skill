# B1 - Official ground truth for agentic Blender (MCP, Python API, CLI)

Date: 2026-10-16. Blender 5.2.2 LTS (build 2026-09-15), macOS arm64 (Apple M3 Pro), headless.
Grades: [V] official/source/introspected, [B] measured by me, [P] practitioner, [U] unverified.
Sources: blender.org/lab/mcp-server (fetched 2026-10-16); projects.blender.org/lab/blender_mcp tag v1.0.3 (cloned, source read; API at projects.blender.org/api/v1/repos/lab/blender_mcp); PyPI mcp-for-blender 2.1.9 (wheel unpacked); `blender --help`; headless runs of scripts in the session scratchpad.

---

## 1. Blender Lab MCP server

### 1.1 What it is, version, install

| Item | Fact | Grade |
|---|---|---|
| Version | add-on + server **v1.0.3**, tagged 2026-09-11. Releases: 0.1.0 (2026-03-24), 0.2.0 (04-10), 0.3.0 (04-14), 1.0.0 (04-27), 1.0.2 (09-08), 1.0.3 (09-11). Assets: `blender-1.0.3.mcpb`, `mcp-1.0.3.zip` | [V] Gitea API |
| Needs | Blender **>= 5.1** (`blender_version_min = "5.1.0"`), license GPL-3.0+, add-on id `mcp` | [V] manifest |
| Three parts | (1) Blender add-on (TCP socket bridge **inside** Blender), (2) `blender-mcp` Python MCP server (FastMCP), (3) an LLM client. Page: "Blender does not have any built-in functionality for connecting to LLMs" | [V] page |
| Add-on install | Add Blender Lab extensions repo `https://lab.blender.org/` (drag-drop zip does it; "you will need to do it twice": once to add the repo, once to install), then install + enable "MCP" | [V] page + README |
| Server install | `.mcpb` bundle (Claude Desktop-style) from the release page, or `pip install git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp`. Entry point `blender-mcp = blmcp:main`; bundle runs `uv run blender-mcp`. Python >= 3.10, deps `mcp[cli]>=1.2,<2`, docutils, pyyaml | [V] pyproject, manifest |
| Offline gate | Add-on refuses to start unless **Allow Online Access** is on (`bpy.app.online_access`; CLI `--online-mode`). Failure is silent-ish (issue #45: server shows "on" but never binds) | [V] source + issue |
| Page's claims about clients | Names only llama.cpp (and says llama.cpp does not support the `.mcpb`). **No** Claude Code / Codex instructions on the page. The word "agent" does not appear; no roadmap section; no "agent control plane" framing found anywhere in the page or repo. Treat that framing as the lead's, not Blender's | [V] page |

### 1.2 Client config for Claude Code / Codex / generic (constructed, not run)

The server speaks **stdio by default** (`--transport stdio`) and optional streamable HTTP (`--transport http --host 127.0.0.1 --port 8000`, stateless, CORS `*`, DNS-rebinding protection OFF; source comment says HTTP exists for llama.cpp's web UI and "most agents wont use STDIO" [sic]). So any MCP client that launches a stdio command works. [U] - these exact lines are my construction from the entry point; not executed (no installs allowed):

```bash
# Claude Code
claude mcp add blender -- uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp
# Codex
codex mcp add blender -- uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp
# generic mcp.json
{"mcpServers":{"blender":{"command":"uvx","args":["--from","git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp","blender-mcp"],"env":{"BLENDER_MCP_PORT":"9876"}}}}
```

Env vars read by the server [V]: `BLENDER_MCP_HOST` (default `localhost`), `BLENDER_MCP_PORT` (default `9876`), `BLENDER_PATH` (binary for `*_for_cli` tools, default `blender` on PATH).

### 1.3 Tool list (read from `mcp/blmcp/tools/*.py`, v1.0.3) [V]

Every non-CLI tool = "format a snippet of Python from `*_toolcode.py`, send it over the socket, run it in Blender's main thread." Hint annotations are MCP `readOnlyHint`/`destructiveHint`.

| Tool | Params | Purpose / notes |
|---|---|---|
| `execute_blender_code` | `code: str` | exec in running Blender, full `bpy`. **Return data by assigning a dict to `result`** (non-dict -> error; non-JSON values fall back to `repr`). stdout/stderr captured. destructive. Server instructions call it "a last resort" |
| `execute_blender_code_for_cli` | `blend_file, code` | Spawns `blender --background <copy> --python-expr`, 120 s timeout. Works on a synced numbered copy of the file (not the live one) |
| `get_objects_summary` | - | collection tree + objects (name, type, parent, data, selection, visibility). Issue #54: can bloat context on big scenes |
| `get_object_detail_summary` | `name` | type, transforms, parent/children, modifiers, constraints, materials, visibility, collections |
| `get_blendfile_summary_datablocks` | - | datablock counts, active workspace, render engine |
| `get_blendfile_summary_missing_files` | - | missing external refs (images, libs, fonts, sounds, clips, caches) |
| `get_blendfile_summary_of_linked_libraries` | - | tree of direct/indirect linked libraries |
| `get_blendfile_summary_path_info` | - | path, saved/dirty status, age, backups |
| `get_blendfile_summary_usage_guess` | - | guesses use-cases (scored 0-100) |
| (each `get_blendfile_summary_*` has a `_for_cli(blend_file)` twin) | | headless variant on a file on disk |
| `get_screenshot_of_window_as_image` | `size_limit_in_bytes=0` | PNG of the whole Blender window (needs a GUI session) |
| `get_screenshot_of_area_as_image` | `area_ui_type, size_limit_in_bytes=0` | PNG of one editor area by `ui_type` |
| `get_screenshot_of_window_as_json` | - | JSON of window layout, areas, active object, selection |
| `render_viewport_to_path` | `output_path` | full render with **current** render settings to a file (readOnly hint, but writes a file) |
| `render_thumbnail_to_path` | `output_path` | small low-quality render, temporarily overrides settings. Issue #61: GUI sessions may render at original resolution |
| `jump_to_tab_by_name` / `jump_to_tab_by_space_type(allow_edits)` | | switch workspace; `allow_edits` may duplicate a workspace |
| `jump_to_view3d_object_by_name` / `..._object_data_by_name` | `name, allow_edits` | frame an object in the 3D view; `allow_edits` may unhide it / enable its collections |
| `get_python_api_docs` | `identifier` | bundled API RST for a dotted name; `*` and `bpy.*` list modules/children; includes literalinclude examples |
| `search_api_docs` / `search_manual_docs` | `query, max_results, context, index` | full-text search over bundled API reference / user manual (RST ships in the package, matching the installed Blender version) |

Not present [V]: no scene-mutation tools beyond code execution, no asset-library tools, no undo tool, no multi-frame render, no GUI input (click/key) tools, no add-on management. Repo issue #4 ("fewer general-purpose tools > many specialized ones") and #39 ("Additional tools and features") are open: the design is intentionally thin.

### 1.4 Execution model, security, limits

| Topic | Fact | Grade |
|---|---|---|
| Transport to Blender | non-blocking TCP server in the add-on, null-byte-delimited JSON, polled from `bpy.app.timers` (0.05 s active, 1 s idle after 5 s). Default `localhost:9876`; host/port are add-on preferences; autostart on by default (1 s delay, not in background mode) | [V] source |
| Threading | code runs on Blender's **main thread** inside the timer: Blender UI blocks while it runs; one request at a time | [V] source |
| Timeouts | client socket timeout **300 s** per call; `_for_cli` 120 s; request size cap **10 MiB**; deferred jobs (modal render via `check_is_finished`) up to 1 h | [V] source |
| Deferred completion | snippet may define `check_is_finished()`; the server keeps the connection open and polls it (interactive add-on only; rejected in `--background` serving) | [V] |
| "Sandbox" | `WeakSandboxForLLM`: patches `sys.exit` and blocks 4 operators (`wm.quit_blender`, `wm.read_factory_settings`, `wm.read_factory_userpref`, `wm.read_userpref`). Source says it "isn't really a sandbox... slap on the wrist". Page: executes LLM code "without any guards"; use a VM/throwaway machine | [V] |
| No automatic undo | I found no undo wrapping around exec; assume each call is a real, permanent edit unless the snippet calls `bpy.ops.ed.undo_push`. Save/backup first | [V] (absent in source) / [U] |
| Multi-instance | one add-on per Blender, one port each. Run several Blenders on different ports and start one `blender-mcp` per port with `BLENDER_MCP_PORT`. Windows: SO_REUSEADDR lets a 2nd Blender silently share a port (issue #63) | [V] |
| Background serving | `blender -b file.blend --command blender_mcp --host H --port P` serves the same protocol with no GUI (needs `--online-mode`); screenshots/jump tools are meaningless there | [V] cli.py |
| Server instructions (sent to the model) | inspect before assuming, don't destructively modify without confirmation, prefer ops for standard actions and data API for precision, set mode + active + selection explicitly, update depsgraph before reading computed values, use bmesh in edit mode, return structured data | [V] prompts.yml |
| Known issues (open) | macOS `.mcpb` install fails with "Operation not permitted" (#57); `_for_cli` hangs on Windows (inherited stdin, #42/#58/#60); `result` must be a dict though instructions say lists (#64); `get_python_api_docs` fails on `bpy.types.Object.location` (#62) | [V] issues |
| Official examples | rename datablocks, relation queries ("which objects use material X"), render-aware poly-count outliers (must use depsgraph, RENDER vs VIEWPORT modifier visibility differ) | [V] README |

### 1.5 Versus community `mcp-for-blender` 2.1.9 (ahujasid/blender-mcp, "not affiliated with Blender Foundation")

| | Blender Lab `blender-mcp` 1.0.3 | community `mcp-for-blender` 2.1.9 |
|---|---|---|
| Philosophy | thin: introspection + code exec + screenshots + bundled docs | fat: assets, generation, telemetry, trajectory logging |
| Tools (server.py) | ~25, listed above | `get_addon_status`, `disable_telemetry`, `get_scene_info`, `execute_blender_code`, `look`, `search_assets`, `import_asset`, `generate_3d`, `viewport_latest/capture/pick`, `record_trajectory_feedback` (+ internal Poly Haven / Sketchfab / Poly Pizza / Hyper3D helpers) |
| Port | 9876 | 9876 (same default - they collide if both run) |
| Timeout | 300 s | 180 s |
| Safety | weak sandbox, always on | opt-in `BLENDER_MCP_SAFE_MODE=1` AST allow-list (prompt-injection guard; admits socket accepts raw code from any local process) |
| Docs in-tool | full API + manual RST bundled | none |
| Telemetry | none seen | has consent-gated telemetry + `disable_telemetry` tool |

Take-away for the skill: the official server is a *transport + observation layer*; all authoring still happens as Python the agent writes. Anything an agent can do through it, it can do headless with `blender -b` for free, except live viewport screenshots and the user's open session.

---

## 2. Python API patterns for agents (Blender 5.2.2, all [B] unless marked)

Every snippet below was run with `blender -b --factory-startup --python-exit-code 3 --python file.py`.

### 2.1 Data API first, ops only when unavoidable
Data API (`bpy.data.*.new`, `collection.objects.link`, `bmesh`) needs no context, selection or mode and returns the object, so no `.001` name guessing:
```python
me = bpy.data.meshes.new("M"); ob = bpy.data.objects.new("O", me)
bpy.context.scene.collection.objects.link(ob)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2); bm.to_mesh(me); bm.free()
```
Ops are unavoidable for: shade smooth/auto-smooth-style helpers, mesh `remove_doubles` outside bmesh, UV unwrap/pack (`uv.smart_project`), bake, render, export (`export_scene.gltf`), rigid-body/cloth bakes, `object.convert`, `object.modifier_apply`, add-on operators.

### 2.2 `context.temp_override` (works in background) 
```python
with bpy.context.temp_override(active_object=ob, object=ob,
        selected_objects=[ob], selected_editable_objects=[ob]):
    bpy.ops.object.shade_smooth()          # ran OK
```
Override only the keys the operator's poll reads. For UI-area ops you need `window/area/region` from a real screen: **untestable headless** (no GUI areas; `bpy.ops.ed.undo()` fails poll in bg with "context is incorrect").

### 2.3 Depsgraph / evaluated data
```python
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg); m = ev.to_mesh()   # 96 polys for cube + Subsurf lvl 2 (orig mesh: 6)
...; ev.to_mesh_clear()
```
Always read counts/bounds from the evaluated mesh (this is exactly the official "outlier" example). Call `bpy.context.view_layer.update()` after edits and before reading `matrix_world`.

### 2.4 Geometry Nodes via Python - **5.2 changed modifier input access**
- Build: `ng = bpy.data.node_groups.new("GN","GeometryNodeTree")`; sockets via `ng.interface.new_socket(name, in_out='INPUT'|'OUTPUT', socket_type='NodeSocketGeometry'|'NodeSocketFloat'...)`; nodes via `ng.nodes.new("GeometryNodeTransform")`; `ng.links.new(a.outputs[...], b.inputs[...])`; attach with `m = ob.modifiers.new("GN","NODES"); m.node_group = ng`.
- **`m.keys()` / `m["Socket_2"]` raises `TypeError: bpy_struct.keys(): this type doesn't support IDProperties` in 5.2.2.** [B] The old ID-property route is gone.
- Verified replacement: `m.properties.inputs` (type `GeometryNodesInterfaceInputs`); each input is an attribute named by the socket **identifier**:
```python
s = ng.interface.new_socket("Scale", in_out='INPUT', socket_type='NodeSocketFloat')
inp = m.properties.inputs
print(s.identifier)                       # 'Socket_2'  (Socket_0 is the Geometry input)
getattr(inp, s.identifier).value = 2.5    # worked; read back 2.5
# inp["Scale"] / inp[identifier] returns an IDPropertyGroup with NO .value -> don't use item access
```
This is the doc-promised "verify" point: use `.properties.inputs.<identifier>.value`; resolve the identifier from `ng.interface.items_tree` by name, never hard-code `Socket_N`. (`use_attribute` / attribute-name toggles for fields live on the same group; [U] not exercised.)

### 2.5 Compositor
`scene.use_nodes` still exists but emits `DeprecationWarning: expected to be removed in Blender 6.0`. Use the new datablock:
```python
sc.compositing_node_group = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ng = sc.compositing_node_group
blur = ng.nodes.new("CompositorNodeBlur")      # inputs: Image, Size, Type, Extend Bounds, Separable (sockets, not props)
```
`CompositorNodeRLayers`, `CompositorNodeGlare` exist. In 5.x blur size/type are **input sockets** (set `blur.inputs["Size"].default_value`). Output order: put a `NodeGroupOutput`-style output node per 5.2 interface [U - not wired end-to-end].

### 2.6 Animation: slotted / layered Actions (4.4+ model, verified on 5.2.2)
Old `action.fcurves` is **gone** (`hasattr(act,'fcurves') -> False`).
```python
ob.keyframe_insert("location", frame=1)          # still works, auto-creates action+slot+layer+strip
ad = ob.animation_data; act = ad.action
slot = ad.action_slot                             # ActionSlot: use .identifier (e.g. 'OBCube.001'); NO .name
strip = act.layers[0].strips[0]                   # type 'KEYFRAME'
cb = strip.channelbag(slot)                       # ActionChannelbag: .fcurves, .groups
for fc in cb.fcurves: print(fc.data_path, fc.array_index, len(fc.keyframe_points))
fc.evaluate(12)                                   # 2.337 (bezier ease)
```
Build from scratch (no keyframe_insert):
```python
act = bpy.data.actions.new("A"); slot = act.slots.new("OBJECT", "Cube2")   # positional (id_type, name)
st = act.layers.new("L").strips.new(type='KEYFRAME')
cb = st.channelbag(slot, ensure=True)
f = cb.fcurves.new("rotation_euler", index=2); f.keyframe_points.insert(1, 0); f.keyframe_points.insert(30, 3.14)
ob.animation_data_create(); ob.animation_data.action = act; ob.animation_data.action_slot = slot
sc.frame_set(30)      # rotation_euler.z == 3.14  [B]
```
Helpers: `bpy_extras.anim_utils` has `action_ensure_channelbag_for_slot`, `action_get_channelbag_for_slot`, `animdata_get_channelbag_for_assigned_slot`, `bake_action[_objects]`. **Assigning an action without also setting `action_slot` leaves the object un-animated** (slot is the binding).

### 2.7 Drivers
```python
d = ob2.driver_add("location", 0).driver; d.type = 'SCRIPTED'
v = d.variables.new(); v.name = "v"; v.targets[0].id = ob; v.targets[0].data_path = "location[0]"
d.expression = "v*2"          # after frame_set + view_layer.update: 24-frame source x=5 -> driven x=10.0
```
Simple expressions run without "auto-run Python scripts"; arbitrary Python needs `-y`/autoexec ([V] CLI doc).

### 2.8 Handlers, timers, background limits
- Handlers work in bg: `bpy.app.handlers.frame_change_post.append(fn); sc.frame_set(3)` fired (hit=[3]). Remove them in `finally`; handlers persist across file loads only if decorated `@persistent`.
- **`bpy.app.timers` do NOT fire in `--background`** inside a script, even with a sleeping loop (0 hits in 0.5 s) [B]. They fire in the GUI (that is how the MCP add-on works). In bg do work synchronously.
- Render in bg: both EEVEE and Cycles render headless on macOS (see 3). `bpy.app.background` is True. GPU *drawing* (viewport screenshots, `gpu` module offscreen, `render.opengl`) is unavailable/unreliable bg [U-untested].
- Engine ids in 5.2: `'BLENDER_EEVEE'` (the `_NEXT` suffix is gone), `'CYCLES'`, `'BLENDER_WORKBENCH'`. [V] introspection (enum lists `BLENDER_EEVEE`).

### 2.9 Undo, saving, backups, idempotency
- `bpy.ops.ed.undo_push(message=)` works in bg (`{'FINISHED'}`); `bpy.ops.ed.undo()` does not (poll fails) [B]. For agents: snapshot by saving to a numbered copy, not by undo.
- `bpy.ops.wm.save_as_mainfile(filepath=..., compress=True, copy=True)`: a **second save to an existing path creates `a.blend1`** (`save_version` default); clean these up in tests [B].
- Idempotent scripts: look up by name before create (`bpy.data.objects.get(n) or bpy.data.objects.new(n, me)`), set not add (`modifiers.get`), clear and rebuild generated node trees/collections, key everything off explicit names/ids, end with a deterministic `result`/JSON print, run with `--python-exit-code N` so a raised exception becomes a nonzero exit.

### 2.10 Assets, linking, add-ons, preferences
```python
with bpy.data.libraries.load(path, link=True, relative=False) as (src, dst):
    dst.objects = [n for n in src.objects if n == "Cube"]
bpy.context.scene.collection.objects.link(dst.objects[0])   # LINKED: obj.library.name == 'lib.blend' [B]
```
Loading from the *currently open file* raises `ValueError: Cannot load from the current blend file`. Linked objects are read-only until `make_local`/library override. Essentials asset library ships with the install (`<DATAFILES>/assets` exists); user library default `~/Documents/Blender/Assets` [B]; `bpy.ops.asset.*` needs UI context [U].
- Add-ons: `addon_utils.enable("io_scene_gltf2", default_set=False, persistent=False)` returned a module [B]; in 5.2 glTF/FBX/BVH/SVG/UV-layout/`pose_library`/`cycles` are enabled under factory startup. Extensions (`bl_pkg`, repos) need `--online-mode` for network [V].
- Preferences: `bpy.context.preferences.use_preferences_save` was True; config dir `~/Library/Application Support/Blender/5.2/config`. For reproducible runs always pass `--factory-startup`; set Cycles devices per-run in the script (they are saved in userpref otherwise).

---

## 3. CLI for agents

| Flag | Use | Notes (verified where marked) |
|---|---|---|
| `-b` / `--background` | no UI | required for all agent runs |
| `--factory-startup` | ignore user prefs/startup file | reproducibility; also drops saved Metal device selection |
| `-P file.py` / `--python-expr "..."` | run script/inline code | order matters: scripts run after the preceding args are applied |
| `--python-exit-code N` | exit code on uncaught Python exception | **without it a raising script still exits 0** [B]; with `7` -> exit 7 [B]; `sys.exit(5)` -> 5 [B] |
| `-- args...` | pass-through to script | `sys.argv[sys.argv.index('--')+1:]` -> `['--foo','bar']` [B]; Cycles also reads `-- --cycles-device METAL|CPU` [B, rendered 11.3 s] |
| `-E ENGINE` | `CYCLES`, `BLENDER_EEVEE`, `BLENDER_WORKBENCH` | set before `-a`/`-f` |
| `-o PATH` | output; `#` run = zero-padded frame (`f_####` -> `f_0001.png`) | [B] |
| `-F FORMAT` / `-x 1` | image format / force extension | PNG, OPEN_EXR, OPEN_EXR_MULTILAYER, JPEG, WEBP, AVIF, HDR, TIFF, FFMPEG... [V] |
| `-s N -e M -j J` | frame start/end/step | `-s 1 -e 3 -a` wrote f_0001..0003 [B] |
| `-f N` / `-a` | one frame / animation | **put `-f`/`-a` last**: they execute at the point they appear; args after are ignored for that render [V] |
| `-S name` | scene | |
| `-t N` | threads (0 = auto) | |
| `--log "render,cycles"` / `--log "*,^operator"` | category log filter | [V] help |
| `-y` / `--enable-autoexec` | allow Python in files/drivers | security-sensitive |
| `--online-mode` | allow network (extensions, MCP add-on) | |
| `--command blender_mcp` | add-on CLI command (serve MCP headless) | official add-on only |
| `-noaudio` | skip audio init | faster start, avoids device warnings |

Exit codes [B]: 0 normal and for uncaught Python exceptions unless `--python-exit-code`; `bpy.ops.wm.quit_blender()` -> 0.

### Cycles on Apple GPU (Metal), headless [B]
```python
cp = bpy.context.preferences.addons['cycles'].preferences
cp.compute_device_type = 'METAL'
cp.refresh_devices()                       # or get_devices(); devices appear here
# DEV CPU Apple M3 Pro ; DEV METAL Apple M3 Pro (GPU - 14 cores)
for d in cp.devices: d.use = (d.type != 'CPU')
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'
```
Timings, default cube, 960x540, 64 spp + denoise: **cold first Metal render 143.6 s** (kernel compile; wall-clock-kills naive 120 s timeouts), **warm 2.46 s**, CPU 2.08 s, EEVEE 1.08-1.37 s. A trivial scene is no faster on GPU; the point is that Metal works headless and the first call must be budgeted (or pre-warmed). `compute_device_type` enum introspected *before* `refresh_devices` is empty (`[]`) - do not read the list first.

---

## 4. Traps (agent-facing)

1. **`modifier["Socket_N"]` is dead in 5.2**; use `modifier.properties.inputs.<identifier>.value`; item-access returns an `IDPropertyGroup` with no `.value`.
2. **`action.fcurves` is gone**; go layer -> strip -> `channelbag(slot)` -> `fcurves`. `ActionSlot` has `.identifier`, not `.name`. Assigning `action` without `action_slot` animates nothing.
3. `Scene.use_nodes` is deprecated (removal 6.0); use `scene.compositing_node_group`.
4. Engine id is `BLENDER_EEVEE` in 5.2, not `BLENDER_EEVEE_NEXT`.
5. Without `--python-exit-code`, a crashed script returns exit 0: CI/agents will think it succeeded.
6. `bpy.app.timers` never fire headless; `bpy.ops.ed.undo()` fails poll headless; viewport/area screenshots need a GUI session.
7. First Metal render of a session/version compiles kernels (~2.5 min here); later runs are seconds.
8. `-f`/`-a` consume the args already parsed; put `-E -o -F -s -e` before them and the action last.
9. Second `save_as_mainfile` leaves `.blend1`; `libraries.load` cannot read the open file; names get `.001` suffixes: hold the returned object, never look up by assumed name.
10. MCP server specifics: port 9876 shared with the community server; main-thread blocking (long ops freeze the UI, 300 s socket cap); `result` must be a **dict**; no undo, no real sandbox; add-on needs **online access** enabled or silently doesn't bind; `.mcpb` install fails on macOS (#57); `_for_cli` hangs on Windows (#42).
11. "Agent control plane" is not in Blender's text; do not cite it as official positioning.
12. The official server requires 5.1+; for older Blenders only community servers or plain `blender -b` apply.

## 5. Recommended agent stack (opinionated)
- Authoring/batch/CI: `blender -b --factory-startup --python-exit-code 3 -P script.py`; script prints one JSON line, saves to a copy, renders via `-o/-F/-a` last.
- Interactive pairing with a human's open session: Lab MCP (`execute_blender_code`, `get_object_detail_summary`, `get_screenshot_of_window_as_image`), always after saving a backup copy.
- Doc lookup: use `search_api_docs`/`get_python_api_docs` (bundled, version-matched) before guessing 5.x API names - four of the traps above are API renames.
