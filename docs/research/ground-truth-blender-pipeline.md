# Ground truth: Blender, asset pipeline, generative 3D, CAD (lane R2)
Date: 2026-10-16. Grades: [V] official · [B] measured · [P] practitioner · [U] unverified.
Local presence check: blender, gltf-transform, gltfpack, ktx, toktx, openscad all ABSENT on this machine; `uvx` present (/opt/homebrew/bin/uvx).

## 1. Version / tool table
| Tool | Version (date) | Install | Source / licence |
|---|---|---|---|
| Blender | 5.2 LTS, 2026-07-14 (current stable AND LTS). Prior LTS 4.5 (2025-07-15), 4.2 (2024-07-16) | blender.org download / `brew install --cask blender` [P] | blender.org/download/releases [V]; GPL |
| bpy (PyPI) | 5.2.2 (2026-09-15) | `pip install bpy` (standalone module) | pypi.org [V] |
| Blender Lab MCP | repo updated 2026-09-29; addon needs Blender >= 5.1 | add-on zip (Blender Lab repo) + MCP server (.mcpb or from source) | projects.blender.org/lab/blender_mcp, blender.org/lab/mcp-server [V]; GPL-3.0 (LICENSE file) |
| mcp-for-blender (ex blender-mcp, ahujasid) | PyPI 2.1.9 (2026-10-06); old `blender-mcp` 2.0.0 on PyPI (2026-09-16) | `uvx mcp-for-blender` | github.com/ahujasid/blender-mcp [V]; MIT; 31.1k stars; pushed 2026-10-06 |
| bpy-dev/blender-mcp | pushed 2026-09-12 | see repo | GPL-3.0; 98 stars; "independent enhanced distribution of Blender Lab MCP: standalone bpy, runtime API docs, benchmarks" [V repo desc] |
| @gltf-transform/cli | 4.5.1 (2026-09-28) | `npm i -g @gltf-transform/cli` | npm [V]; MIT |
| gltfpack (npm) | 1.3.0 (2026-09-25); meshoptimizer v1.3 | `npm i -g gltfpack` or native binary from releases (preferred) | npm, GitHub [V]; MIT |
| KTX-Software (`ktx`) | v4.4.2 (2025-10-04); gltf-transform needs >= 4.4.0 | GitHub release installer / brew [P] | github.com/KhronosGroup/KTX-Software; licence NOASSERTION (Apache-2.0 mix) |
| glTF-Validator | npm `gltf-validator` 2.0.0-dev.3.10 (2024-10-22); repo active 2026-10-06; no GitHub releases | `npm i gltf-validator` (Node API) or build Dart CLI | Apache-2.0 [V] |
| gltfjsx | 6.5.3 (2024-11-04) — stale 2 years | `npx gltfjsx model.glb --transform` | MIT; see trap list |
| build123d | 0.13.0 (2026-09-21) | `pip install build123d` | Apache-2.0 [V] |
| CadQuery | 2.8.0 (2026-06-21) | `pip install cadquery` | repo licence NOASSERTION (Apache-2.0 per project, [U]) |
| manifold-3d | 3.5.4 (2026-09-25) | `npm i manifold-3d` / PyPI `manifold3d` | Apache-2.0 |
| trimesh | 5.1.1 (2026-10-02) | `pip install trimesh` | PyPI |
| OpenSCAD | latest GitHub *release* is 2021.01; project active (pushed 2026-10-16); nightlies are what people use | brew / nightly [P] | licence NOASSERTION (GPL-2 w/ exceptions) [U] |
| OrcaSlicer | v2.4.2 (2026-07-07) | release DMG | AGPL-3.0 |
| Bambu Studio | v02.08.02.61 (2026-08-21) | release DMG | AGPL-3.0 |
| text-to-cad (earthtojake) | v0.7.21 (2026-10-11); 20.9k stars; MIT; `cadgen==0.7.21` on PyPI | `claude plugin marketplace add earthtojake/text-to-cad#latest` then `claude plugin install text-to-cad@earthtojake`; or `npx skills add earthtojake/text-to-cad#latest` | README [V] |
| img2threejs | github.com/img2threejs/img2threejs, 18.2k stars, Apache-2.0, pushed 2026-10-08 | clone into `~/.claude/skills/img2threejs` | [P] (search snippets + gh api); many mirrors/forks disagree on owner — use this canonical one |

## 2. Blender (topic 1)
**Versions** [V blender.org/download/releases]: 5.2 LTS is current; there is no non-LTS "newer" release listed. Skill must not assume 4.x.

**Headless CLI** [V docs.blender.org manual, command_line/arguments.rst, fetched 2026-10-16]
- `-b/--background` UI-less; audio disabled by default in bg mode.
- `--python <file>`; `--python-expr "<code>"` (may be a multi-line script; limited by OS argv length); `--python-exit-code <0..255>` exit code when a Python exception is raised in CLI scripts (0 disables) — **set it, otherwise a failed script exits 0**.
- `-X/--factory-startup` skips user startup.blend (add-ons are still the factory set; use for reproducible export/render).
- `--python-use-system-env` lets PYTHONPATH through; `--python-use-user-env` for user site-packages.
- `--offline-mode`; `--log-level <fatal|error|warning|...>`; `-y/--enable-autoexec`, `-Y` disable (default disabled).
- **Args are executed in order.** Manual's own example: `blender -b test.blend --render-output /tmp --render-frame 1` works; putting `--render-output` before the .blend is overwritten by the load, and `--render-frame` before the output path renders first. Load .blend first, then settings, then actions.
- `--` ends Blender's args; everything after is left for the script in `sys.argv` (parse `sys.argv[sys.argv.index("--")+1:]`). [P: standard idiom; manual lists `--` as end-of-args — confirm with `blender --help`.]
- macOS binary: `/Applications/Blender.app/Contents/MacOS/Blender` [P; not installed here so unverified locally].
- Canonical template: `Blender -b --factory-startup file.blend --python-exit-code 1 --python script.py -- --out x.glb`.
- Log format changed in 5.0 (background progress output) — don't regex-parse old log lines [V 5.0 notes].

**glTF exporter `bpy.ops.export_scene.gltf`** [V, read from io_scene_gltf2 source: `blender-v5.2-release` bl_info 5.2.41; `blender-v5.1-release` 5.1.20; main = 5.4.5 for Blender 5.3 dev]
Key properties (names as in source):
| Param | Values / default |
|---|---|
| `filepath` | required |
| `export_format` | `GLB` (binary, default idx 0) · `GLTF_SEPARATE` · `GLTF_EMBEDDED` |
| `export_image_format` | `AUTO` (default) · `JPEG` · `WEBP` (no fallback) · `NONE` |
| `export_image_add_webp` (bool, False) / `export_image_webp_fallback` (bool, False) | adds WebP textures / PNG fallback for WebP. Present in 5.1 and 5.2 |
| `export_jpeg_quality`, `export_texture_dir`, `export_keep_originals` | as named |
| `export_draco_mesh_compression_enable` (False) + `_level`, `export_draco_position_quantization` / `normal` / `texcoord` / `color` / `generic` | Draco |
| `export_meshopt_compression_enable` (False), `export_meshopt_extension` = `EXT_meshopt_compression` (default) or `KHR_meshopt_compression` | **new in 5.2, absent in 5.1** (grep of both release branches) |
| `export_gltfpack_*` (`_tc`, `_tq`, `_si`, `_sa`, `_slb`, `_vp/vt/vn/vc`, `_vpi`, `_noq`, `_kn`) | gltfpack integration options present in 5.2 branch; requires gltfpack binary [U on exact behaviour] |
| `export_materials` | `EXPORT` (default) · `PLACEHOLDER` · `VIEWPORT` · `NONE` |
| `export_apply` (False) | apply modifiers (excl. armatures). **WARNING in source: prevents exporting shape keys** |
| `export_yup` (True) | +Y up (glTF convention) — leave True for web |
| `use_selection`, `export_cameras`, `export_lights`, `export_extras`, `export_tangents`, `export_normals`, `export_texcoords`, `export_skins`, `export_morph*`, `export_gpu_instances`, `export_unused_images` | bool options |
| `export_vertex_color` (enum) + `export_vertex_color_name`, `export_active_vertex_color_when_no_material` | replaces old `export_colors` bool [P] |
| `export_animations` (bool) + `export_animation_mode` (e.g. ACTIONS/NLA_TRACKS/ACTIVE_ACTIONS/BROADCAST), `export_force_sampling`, `export_optimize_animation_size`, `export_nla_strips`, `export_current_frame` | animation |
| `export_import_convert_lighting_mode` | SPEC / COMPAT / RAW light units |
Importer: `bpy.ops.import_scene.gltf(filepath=...)`; options not enumerated in this lane [gap].
Gotchas: Blender writes PNG/JPEG/WebP only — **no KTX2 from Blender**; do KTX2 afterwards with gltf-transform/gltfpack. Draco *and* meshopt in-exporter are convenient but a separate `gltf-transform optimize` pass is the controllable route. Blender 5.2 docs' manual URL for the glTF page (`addons/import_export/scene_gltf2.html`) is a dead end for fetchers (page is huge); read operator source or `help(bpy.ops.export_scene.gltf)` in the target Blender instead — the skill should tell the agent to introspect `bpy.ops.export_scene.gltf.get_rna_type().properties.keys()` at runtime since params drift per version.

## 3. MCP servers (topic 2)
**Official Blender Lab MCP** [V blender.org/lab/mcp-server, repo readme, readme_tools.rst, fetched 2026-10-16]
- Architecture: `MCP client <-stdio-> blender-mcp (Python pkg, entry point blender-mcp) <-TCP socket-> Blender add-on` (host/port/auto-start in add-on prefs).
- Requirements: Blender **5.1+**, add-on (drag zip into Blender; two passes: first adds Blender Lab repository, second installs), MCP server as `.mcpb` bundle (newer clients) or from source. Page's documented client is llama.cpp; no Claude/Codex recipe — for Claude Code, register the stdio command yourself (see below) [gap: exact command not documented in fetched pages].
- Tools (readme_tools.rst, auto-generated): `execute_blender_code`, `execute_blender_code_for_cli` (separate background Blender process), `get_blendfile_summary_*` (datablocks, missing_files, linked_libraries, path_info, usage_guess — each with a `_for_cli` twin taking a `blend_file`), `get_object_detail_summary`, `get_objects_summary`, `get_python_api_docs` (bundled RST API docs by identifier/`*` pattern), `get_screenshot_of_area_as_image`, `_of_window_as_image`, `_of_window_as_json`, `jump_to_tab_by_name`, `jump_to_tab_by_space_type`, `jump_to_view3d_object_by_name`, `jump_to_view3d_object_data_by_name`, `render_thumbnail_to_path` (list truncated at 90 lines; more may exist).
- Security [V]: "will execute LLM generated code in Blender without any guards" — use a VM / machine without sensitive data. Deferred responses only in interactive add-on server; background mode requires synchronous completion.
- Licence: GPL-3.0.

**Community mcp-for-blender (ahujasid)** [V github readme, 2026-10-16]
- Renamed from `blender-mcp`; old `uvx blender-mcp` still works. Not affiliated with Blender Foundation. MIT, 31.1k stars.
- Install: `uvx mcp-for-blender setup` (auto) or manual. Requires uv (official installer, not `pip install uv`), Blender 3.0+, Python 3.10+. Add-on: `uvx mcp-for-blender install-addon`, enable "Interface: MCP for Blender", N-panel tab -> Start MCP Server / Connect to Claude. **Do not run the uvx command manually in a terminal.**
- Tools (9): `execute_blender_code`, `look` (viewport/camera/multi-angle/animation renders), `get_scene_info`, `generate_3d`, `search_assets`, `import_asset`, `get_addon_status`, `disable_telemetry`, `record_trajectory_feedback`. (Old tool names like `get_polyhaven_*`, `search_sketchfab_models` seen in LLM memory are replaced — stale trap.)
- Integrations: Poly Haven (CC0, no key), Sketchfab (API key), Hyper3D Rodin / Hunyuan3D / Tripo (generation; Hunyuan Tencent Cloud needs region setting; paid "Premium" avoids own keys), Poly Pizza (free key; some CC-BY).
- Known issues: timeouts -> split requests into smaller steps; Poly Haven downloads run on Blender's main thread and freeze UI (ask 1k/2k); `spawn uvx ENOENT` -> absolute path to uvx in config; socket server has **no auth/encryption** (localhost only); telemetry exists (`disable_telemetry`); optional `BLENDER_MCP_SAFE_MODE=1` pre-checks scripts.
- The "export timeout" concern: not specifically documented; generic timeout advice applies. Raise client timeouts (below) for long exports.

**Register in clients**
- Claude Code [V code.claude.com/docs/en/mcp]: `claude mcp add --transport stdio blender -- uvx mcp-for-blender` (the `--` is required; `--scope local|project|user`; `--env K=V`). Project file `.mcp.json`: `{"mcpServers":{"blender":{"type":"stdio","command":"uvx","args":["mcp-for-blender"],"timeout":600000}}}`. Timeouts: per-server `timeout` (ms, hard wall-clock per tool call), `MCP_TOOL_TIMEOUT`, `MCP_TIMEOUT` (startup), `MAX_MCP_OUTPUT_TOKENS` default 25,000 (screenshots/scene dumps can hit this).
- Codex [V learn.chatgpt.com/docs/extend/mcp, formerly developers.openai.com/codex/mcp]: `codex mcp add blender -- uvx mcp-for-blender`; or `~/.codex/config.toml`: `[mcp_servers.blender] command="uvx" args=["mcp-for-blender"] startup_timeout_sec=20 tool_timeout_sec=300`. **Default tool timeout is 60 s** — too short for exports/renders; raise it.
- Official Lab MCP: command is `blender-mcp` (pip package from repo `mcp/` dir) — register the same way once installed [U on exact install command].

**Decision for skill**: prefer headless CLI scripts for deterministic export/convert (no GUI, exit codes); use MCP only for interactive scene building/inspection. Use the official Lab MCP when Blender >= 5.1 and licence/security posture matters; ahujasid when asset-search/generation integrations are wanted.

## 4. glTF pipeline (topic 3)
**@gltf-transform/cli 4.5.1** [V npm; help text read from source `packages/cli/src/cli.ts` on main, 2026-10-16]
Commands: inspect, validate, copy, optimize, merge, partition, dedup, prune, gzip, xmp, center, instance, flatten, join, draco, meshopt, quantize, dequantize, weld, unweld, tangents, unwrap, reorder, simplify, metalrough, palette, unlit, resize, **etc1s, uastc** (KTX2 — there is no `ktx2` command), ktxdecompress, ktxfix, avif, webp, png, jpeg, resample, sequence, sparse. Global: `-v`, `--vertex-layout`, `--allow-net`.
**`optimize` defaults (main branch source)** — all on unless noted: `--instance true`, `--palette true` (merges materials into palette textures!), `--simplify true` (error tolerance and ratio from SIMPLIFY_DEFAULTS, lossy), `--prune true`, `--prune-solid-textures true`, `--sparse true`, `--compress meshopt` (choices draco|meshopt|quantize|false), `--meshopt-level high`, `--texture-compress auto` (recompress in original format; choices ktx2|webp|avif|auto|false), `--texture-size 2048`, `--flatten true`, `--join true`, `--join-meshes`/`--join-named` true, `--weld true`, `--resample true`. **Defaults are aggressive and lossy: simplify, palette, flatten+join (breaks scene-graph node names/animation targets and per-part picking).** For scroll-driven hero models that animate parts: `--simplify false --join false --flatten false --palette false` or run discrete commands. 4.5.1 default values might differ slightly from main [U]; always run `gltf-transform optimize -h`.
**KTX2**: `etc1s`/`uastc` shell out to **`ktx`** (not `toktx`) and require KTX-Software >= 4.4.0 (`KTX_SOFTWARE_VERSION_MIN='4.4.0'`; check runs `ktx --version`) [V source toktx.ts]. Resize uses Sharp (npm dep). Rule of thumb [P]: ETC1S for albedo/emissive (small), UASTC for normal maps; set color-space slots correctly (`--slots`).
**gltfpack 1.3.0** [V meshoptimizer gltf/README]: `-i in -o out.glb`; `-c` EXT_meshopt_compression, `-cc` extra (serve gzip), `-cz`/`-ce khr` KHR_meshopt_compression, `-cf` fallback buffer; textures `-tc` (KTX2/Basis; needs KHR_texture_basisu and a full build with basis_universal fork; npm build is limited — native binary recommended), `-tw` WebP, `-tu`; `-si R` simplify ratio (default 1 = off); `-noq` disable quantization, `-vp/-vt/-vn/-vc` bits, `-vpf` float positions, `-mi` instancing (EXT_mesh_gpu_instancing), keep flags `-kn` names, `-km` materials, `-ke` extras; `-gsd` gaussian splat SH degree. Output uses KHR_mesh_quantization unless `-noq` -> three.js needs MeshoptDecoder set (`loader.setMeshoptDecoder`).
**glTF-Validator** [V]: `gltf_validator [opts] <file|dir>`; `-o` stdout, `-a` all messages, `-c` yaml config; writes `<asset>.report.json`; non-zero exit on errors. npm API `gltf-validator` exists (last publish 2024, still the usual route). Dart build needed for CLI binary [no prebuilt release found: gap].
**gltfjsx 6.5.3** [V repo]: `--transform/-T` = gltf-transform pipeline producing `<name>-transformed.glb` (Draco, pruning, dedup, instancing, resize textures default 1024, WebP; flags `--resolution`, `--format`, `--simplify`, `--keepmeshes`, `--keepmaterials`); `--types/-t` TS; `--instance/-i`, `--instanceall/-I`; `--keepnames/-k`; `--meta/-m`. Draco output needs Draco decoder at runtime (`useGLTF` drei default CDN ok). Not updated since 2024-11; R3F v9 compat not stated [U].
**Budgets** [P — no official three.js numbers exist]: sources (skillselion, neural4d, tripo blog, playbooks.com, discourse.threejs.org 2026 thread) cluster: mobile whole-scene <=100k tris (some say 50k), <50 draw calls (ceiling ~500), textures 1024 (2048 desktop hero, max), 800 KB hero asset / 2-5 MB total GLB, KTX2 512-1024 for mobile, transparency overdraw is the real mobile killer, 8x 4K textures stall via VRAM. One field report: ~3M triangles/50 GLBs on iPhone 11 with custom pipeline [P, outlier]. Raw 8-15 MB product export -> 1-2 MB optimized [P]. Recommend skill sets *starting* budgets and requires measuring (`gltf-transform inspect`, renderer.info).

## 5. Generative 3D (topic 4)
| Service | Facts | Grade |
|---|---|---|
| Meshy API | docs.meshy.ai: bearer key; text-to-3D = preview then refine (`preview_task_id`); poll `GET /openapi/v2/text-to-3d/:id` (PENDING/IN_PROGRESS/SUCCEEDED/FAILED/CANCELED) or SSE. `target_formats`: glb, obj, fbx, stl, usdz, 3mf (3mf opt-in). Models: meshy-6-lite, meshy-6, meshy-7.1, `latest`(=7.1; default). `lowpoly` retires **2026-10-30** -> use `model_type: smart-topology` (meshy-t2 / **t2.5 default**, triangle-only, target_polycount 100-30,000 for t2.5; standard remesh 100-300,000, default 30,000). `enable_pbr` default false (metal/rough/normal). Credits: preview 20 (meshy-6) / 5 (others); refine 10; image-to-3D 20 untextured/30 textured/35 8K-texture (meshy-6); remesh/rigging 5, animation 3. API pay-per-credit, "subject to change". Plan prices from third parties disagree (Pro $20/1,000cr; Max $60) | V (docs) / U (plans) |
| Tripo | Subscription Pro ~$19.90-20/mo (3,000 cr), Max ~$90; aggregator reports price increases May and Aug 2026 (conflicting). Official platform docs page unfetchable (empty). Output formats, face_limit, MCP: unconfirmed; ahujasid MCP integrates Tripo | U |
| Hyper3D Rodin (Deemos) | Official hyper3d.ai pricing: $1.5/credit; API in Business tier $120/mo. Reseller EmpirioLabs Gen2 $0.80/request. Gen-2 ~40 credits claim unverified | V (page via search snippet) / U |
| Hunyuan3D 2 / 2.1 (open weights) | Tencent-Hunyuan repos 15.1k / 4.2k stars, last push 2025-10; licence "Tencent Hunyuan Community": **does not apply in EU, UK, South Korea** (licence header). Hunyuan3D 3.x: no source found; assume same licence [U]. Includes PBR texture pipeline (2.1) | V (licence text via search) |
| TRELLIS / TRELLIS.2 | microsoft, MIT, 14k / 12k stars, pushed 2026-06 / 2026-07. Needs NVIDIA GPU (CUDA) [P]; not usable on a Mac natively | V repo / P |
| Stable Fast 3D | Stability-AI, licence NOASSERTION (Stability community licence), last push 2025-01; UV-unwrapped mesh, fast single image | V / U |
| TripoSR | MIT, 7.1k stars, no texture bake quality; legacy | V |
| img2threejs | Not a mesh generator: an agent skill that rebuilds an object from ONE image as procedural, code-only THREE.Group (primitives, shaders, pivots/sockets/colliders), iterating render-compare passes; Apache-2.0; Python 3.10+ scripts | P |
Quality caveats [P, consistent across vendor docs]: generated meshes are dense triangle soup; need retopo/remesh (Meshy remesh, smart-topology) and UV checks; baked lighting in albedo unless `remove_lighting`; always run through the glTF pipeline + validator; check licensing/ownership terms per tier (not researched: gap). Use generated models as hero props, not for animated rigs without cleanup.

## 6. CAD / printing (topic 5)
- **text-to-cad (earthtojake) v0.7.21** [V README]: plugin; skills: CAD (STEP primary; GLB/STL/3MF/DXF), step.parts, Engineering Drawing, DXF, URDF/SRDF/SDF, SendCutSend, DfAM Check, DFM, G-code (OrcaSlicer), Bambu Labs. Needs uv, Python 3.11+, Node 20+, build123d 0.11 + OCP (OCCT 7.9). Telemetry default ON (`uvx cadgen telemetry off` / `DO_NOT_TRACK=1`; `CADGEN_UPDATE_CHECK=0`). MIT. **README says the older `cad-viewer` and `cad-mcp-setup` skills are retired**, folded into CAD/DXF/URDF skills.
- Engines: build123d (Apache-2.0, 0.13.0) is what text-to-cad uses; CadQuery 2.8.0 (OCCT, STEP/STL); OpenSCAD (CSG, STL/3MF; use nightlies, last tagged 2021.01); manifold-3d 3.5.4 (fast mesh booleans, JS/WASM, good for in-browser/Node).
- Slicers: OrcaSlicer v2.4.2, Bambu Studio — both AGPL-3.0, GUI + CLI (CLI flags not verified: gap).
- **Local `~/.claude/skills/manufacturing-workflow/SKILL.md` already covers** (read 2026-10-16): orchestration of design intent -> CAD -> visual review -> mesh export -> DfAM -> slice -> readiness -> approval -> upload/start -> print outcome -> calibration; durable state under `manufacturing/` (design.yaml, LEDGER.md, SHA-256 stage manifests via `scripts/artifact_gate.py`), prerequisite checker `scripts/check_prerequisites.py --json`, routes to upstream skills `$cad`, `$step-parts`, `$cad-viewer`, `$dfam-check`, `$gcode`, `$bambu-labs`, `$physical-calibration`, `$freecad-fallback`; physical-action gate (upload and start are separate permissions; never install anything unasked). It explicitly does NOT own CAD generation, viewing, DfAM, slicing, printer control.
- **`3d` should compose, not duplicate**: `3d` CAD pack = thin router: (a) CAD -> web viewing: STEP/STL -> GLB then glTF pipeline; (b) mesh/Blender cleanup of printable parts (Blender `bpy.ops.wm.stl_export`/3MF add-on [P]); (c) hand off to `manufacturing-workflow` for anything involving slicing, printers, provenance. Note: that skill references `$cad-viewer`, retired upstream per README — flag as drift risk.

## 7. USDZ / AR Quick Look (topic 6)
Sources are forum/search-level only; no current (2026) Apple doc retrieved [U overall].
- Reality Converter (Apple app, GUI): reported inputs obj/fbx/usdz plus glTF; one forum thread: OBJ imported at 1/100 scale while GLB converted correctly -> prefer GLB input [P].
- Apple's Python `usdzconvert` reported retired (AOUSD forum thread) [P]. Alternative: OpenUSD `usdcat foo.gltf -o foo.usdc` then `usdzip foo.usdz -a foo.usdc` — one user lost textures [P/U].
- Blender USD export: `bpy.ops.wm.usd_export` (5.0 renamed/removed params: `export_textures` removed -> `export_textures_mode`; `visible_objects_only` removed; `allow_unicode` default true) [V 5.0 notes]. Blender lacks MaterialX in USDZ; many Blender features unsupported by RealityKit [P]. Animation support in the Blender USD add-on was reported missing in an older thread [stale-ish, U].
- Meshy can emit usdz directly (`target_formats`) [V].
- AR Quick Look limits: no morph targets reportedly [vendor claim U]; keep PBR basic (baseColor, normal, ORM), textures <= 2048 [P]. Verify on a real iOS device; no automated validator located (Apple `usdchecker` ships with USD tools [P]).
- Web usage: `<a rel="ar" href="model.usdz">` (iOS Quick Look); Android uses Scene Viewer with GLB [P, not re-verified this session].

## 8. Stale-API traps an LLM will make
Blender 5.x [V unless marked; sources: developer.blender.org/docs/release_notes/5.0|5.1|5.2/python_api, 2026-10-16]
1. EEVEE id: `scene.render.engine = 'BLENDER_EEVEE_NEXT'` -> **`'BLENDER_EEVEE'`** (5.0). `gtao_distance` -> `view_layer.eevee.ambient_occlusion_distance`; `use_gtao`/`gtao_quality` removed.
2. Render pass names changed (`DiffCol` -> Diffuse Color, `IndexMA` -> Material Index, `Z` -> Depth).
3. `scene.use_nodes` is always True/no effect (removal 6.0); **`scene.node_tree` removed -> `scene.compositing_node_group`**; File Output node: `file_slots`, `layer_slots`, `base_path` removed -> `directory`, `file_name`, `file_output_items`; compositor Color output `RGBA` -> `Color`; many compositor nodes replaced by Shader node twins; Combine/Separate legacy nodes removed.
4. `obj['x']` / `bpy.context.scene['cycles']` dict-style access to bpy.props-defined properties removed; `del obj[k]` -> `obj.property_unset(k)`; prop `get`/`set` -> `get_transform`/`set_transform`.
5. Legacy Action API removed: `action.fcurves`, `.groups`, `.id_root` -> slotted actions/channelbags (`channelbag.fcurves.new(..., group_name=)`); `INSERTKEY_XYZ_TO_RGB` removed. Matters for keyframe scripts and glTF animation work.
6. Boolean solver enum `'FAST'` -> **`'FLOAT'`** (modifier and operator).
7. `ImageFormatSettings.media_type` must be set before `file_format`.
8. `ImageTexture` filter/mipmap props removed (`use_mipmap`, `filter_type`...). BGL removed; `Image.bindcode` removed (use `gpu.texture.from_image`).
9. USD ops: `import_subdiv` -> `import_subdivision`; `attr_import_mode` -> `property_import_mode`; export `export_textures` -> `export_textures_mode`; `visible_objects_only` removed (also removed from `wm.alembic_export`; `Scene.alembic_export` removed).
10. Annotations: `GPencil*` types -> `Annotation*`; legacy `bpy.data.grease_pencils` is now the *new* GP (was `grease_pencils_v3`); scripts creating GP via old API break.
11. Bone/pose: `Bone.hide` only edit-bone visibility (use `PoseBone.hide`); `Bone.select*` removed (use edit bone / `PoseBone.select`).
12. UV: `MeshUVLoopLayer.vertex_selection`/`edge_selection`, `BMLoopUV.select*` removed (shared selection across UV maps); UV `pin` access no longer creates attribute.
13. mathutils buffers now float32; numpy interop changes.
14. 5.1: Python 3.13 bundled; VSE strip props renamed (`frame_final_duration` -> `duration`, etc., old names deprecated until 6.0); brush `use_airbrush` etc. -> `brush.stroke_method`; `sculpt.sample_color` removed.
15. 5.2: **Geometry Nodes modifier inputs**: `modifier["Socket_2"]` / `modifier["Socket_2_attribute_name"]` -> `modifier.properties.inputs.<identifier>.value/.attribute_name`, outputs `.properties.outputs.<id>.attribute_name`; Compare/Random Value socket identifiers changed; sculpt automasking props moved to `mesh_automasking_settings.*`; `active_asset_library` index now offset by "All Libraries"+"Essentials".
16. 5.0 notes were only read to char 100,000 of 106,951 — tail unread (gap).
From memory, not re-fetched [P/U]: 4.x-era traps persist — `mesh.use_auto_smooth` and `calc_normals()` gone (4.1); Principled BSDF inputs renamed ("Specular" -> "Specular IOR Level", "Emission" -> "Emission Color", "Subsurface" -> "Subsurface Weight", "Transmission" -> "Transmission Weight"); `bpy.ops.*` needs correct context (use `bpy.context.temp_override`, never the old dict-arg override); prefer `bpy.data` APIs over ops in headless; ops like `bpy.ops.object.mode_set` fail without active object.
Pipeline traps
- glTF exporter: `export_colors` (old) vs `export_vertex_color` enum; `export_apply=True` silently drops shape keys; `export_import_convert_lighting_mode` affects light intensity; PNG default (`AUTO`) -> big GLBs unless `WEBP`/`JPEG`; export param set differs between 5.1 and 5.2 (meshopt/gltfpack only in 5.2) — introspect at runtime.
- `gltf-transform optimize` default simplify+join+flatten+palette is destructive; `ktx2` is not a command (use `etc1s`/`uastc`); texture tool is `ktx` not `toktx` (>= 4.4.0).
- gltfpack npm build lacks texture compression; meshopt/quantized output needs `MeshoptDecoder` + KHR_mesh_quantization support in the loader; Draco needs DRACOLoader decoder path; KTX2 needs `KTX2Loader.setTranscoderPath` + `detectSupport(renderer)`.
- `gltfjsx` unchanged since 2024; `--transform` default texture res 1024 (can silently downsample hero textures).
- MCP: tool names from 2025 ahujasid docs (`get_polyhaven_*`, `generate_hyper3d_model_via_text`, ...) are replaced by 9 consolidated tools; package renamed; Codex 60 s default tool timeout.
- Meshy: `lowpoly` model type retires 2026-10-30; `meshy-7` deprecated -> `meshy-7.1`.
- Hunyuan3D licence excludes EU/UK/South Korea — do not recommend self-hosting to EU users without flagging.

## 9. Gaps
- Blender importer options, `help(bpy.ops.export_scene.gltf)` full text for exact 5.2 defaults; 5.2 release notes "Pipeline & I/O" page unread; tail of 5.0 API notes unread.
- No Blender installed locally; macOS path and `--` argv idiom unverified on this machine.
- Official Lab MCP: exact Claude Code / Codex registration command and complete tool list (list truncated); no Claude recipe in docs.
- Tripo official API/pricing/formats; Hunyuan3D 3.x existence/licence; Stable Fast 3D current licence terms; commercial-use terms of every generator.
- Apple 2026 AR Quick Look/USD guidance, `usdchecker`, Reality Converter glTF support — only forum-grade evidence.
- OrcaSlicer/Bambu Studio CLI flags; OpenSCAD current stable version.
- Web budgets lack an authoritative source (no Khronos/three.js official numbers); Khronos "3DC Asset Creation Guidelines" (github.com/mlimper/3DC-Asset-Creation, PublishingTargets.md) surfaced in search and is the best candidate to fetch next.
- gltf-transform 4.5.1 `optimize` defaults read from `main`, not the tagged release.
- glTF-Validator: no prebuilt CLI release located; npm package stale since 2024.
