# Harvest R5: Blender via MCP and headless CLI

Compiled 2026-10-16. Nothing installed or run. Grades: [V] official (V* = official text relayed by a third party) · [B] measured by the source author · [P] practitioner · [U] unverified or my inference. Blender 5.x facts are secondhand (scenario deltas cite release notes); R2 confirms.

Tags (all MIT unless noted; adapt ideas, write our own text): **SC** scenario-labs/skills · **EL** EL4CTEO/blender-skills · **VG** vladmdgolam blender-mcp · **CZ** czlonkowski blender-web-3d · **KJ** kajisho5 · **RL** RobLe3 · **IB** ifBars · **KI** elithril blender-kiln · **NR** NousResearch hermes wrapper (wraps GPL-3.0+ Blender Lab MCP) · **AH** ahujasid mcp-for-blender · **MM** majidmanzarpour · **JT** jangtrinh · **AR** arjun988 · **RA** ra100 · **QW** QwenLM (Apache-2.0) · **OG** math-inc OpenGauss (stale since 2026-04).

**Verdict.** Best: SC (process, 5.2.1-tested numbers, API traps), EL (budgets, presets), VG + CZ (Blender-to-three.js hand-off), KI (hard MCP rules), MM + JT (reference-fidelity gates). Skip: AR (thin), OG (4.3 era), freshtechbro (stale 2025-11), HKUDS, SFKislev, affaan.

---

## 1. Execution channels

### 1.1 Decision rule
| Need | Channel | Why |
|---|---|---|
| Export, bake, batch, audit, final render, CI, anything reproducible | Headless `blender -b` | Versionable script. CZ, KJ, SC, MM default to it |
| User is watching, live iteration, their open scene, brush strokes, viewport capture | MCP bridge (GUI Blender) | SC [B]: brush strokes fail poll headless; `sculpt.mesh_filter` and `paint.mask_flood_fill` crash headless |
| Both | Iterate live, then save steps as a numbered idempotent script and re-run headless on the master file | MM, CZ |

ALWAYS export GLB headless (VG, KI: MCP exports time out). NEVER open your own GUI Blender on the user's machine (SC: focus theft, pile-up).

### 1.2 Official Blender Lab MCP vs community `ahujasid`
| | Official [V*] | Community [P] |
|---|---|---|
| Needs | Blender 5.1+, extensions-repo add-on, **Allow Online Access** on, loopback 9876, `uv` + git | Blender 4.x ok, add-on + `uvx mcp-for-blender`; add-on starts with Blender |
| Tools | 26 (NR): `execute_blender_code`, `get_objects_summary`, `get_object_detail_summary`, `search_api_docs`, `get_python_api_docs`, `get_screenshot_of_window/area_as_image`, `render_viewport_to_path`, `jump_to_view3d_object_by_name`, `*_for_cli` (RA, KI) | AH README: nine (`execute_blender_code`, `look` multi-view/solid/material/wire/xray, `get_scene_info`, `generate_3d`, `search_assets`/`import_asset`, `get_addon_status`); KI lists 36 incl. `get_object_info` with `world_bounding_box` [conflict] |
| Assets | none | Poly Haven (CC0), Sketchfab, Poly Pizza, Tripo, Rodin, Hunyuan3D |
| Result | Python must set `result = {...}` dict with string keys; other types error after code ran (NR) | Text with prints; treat `Error executing code:` as failure |
| Security | Blender's page: arbitrary Python, no guard against deletion or exfiltration (NR, V*) | Same; AH "ALWAYS save first"; telemetry opt-in, `DISABLE_TELEMETRY=true` |

Choose official when Blender 5.1+ and no marketplace/generation need (KI: same 7 GLBs, 10% cheaper); community for assets/generators or 4.x. RL: select once per task, never switch mid-task, never replay a mutation after a timeout (inspect first). Both default to 9876 [U: simultaneous bridges need different ports].

**Naming trap [V*]:** PyPI `blender-mcp` is ahujasid's server, not the official one. Official runs from git pinned by SHA (`uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@<sha>#subdirectory=mcp" blender-mcp`; NR pins `2cea8d56`, v1.0.3). First uv build took minutes: pre-warm with `--help`.

### 1.3 Setup and health check
1. Never install Blender or the add-on or change preferences for the user (NR); preflight proposes, user approves. AH's `curl | sh` installer must not be auto-run.
2. A tool listing proves the server started, not that Blender is connected.
3. Official check: `get_objects_summary`. `Cannot connect to Blender at localhost:9876` = bridge not ready: walk setup (blender.org/lab/mcp-server, two drag-drops, Allow Online Access in Preferences > System > Network, Add-ons > MCP, "Server is running").
4. Community: `get_addon_status`. Raw probe `nc -z -w2 localhost 9876` (OG). VG trio: scene info, `print("ok")`, a screenshot; stop if any fails.
5. Disabled integrations vanish: a PolyHaven call while off returns `Unknown command type`, which looks like a version bug; call `get_*_status` first (KI [B]).
6. `*_for_cli` tools need `blender` on the **server's** PATH; `BLENDER_PATH` in a shell does not reach it. macOS: wrapper script calling `/Applications/Blender.app/Contents/MacOS/Blender "$@"` (NR).

### 1.4 Timeouts and chunking
- Each MCP call is a fresh Python namespace; `bpy.data` persists; re-import each call (EL, RL). Short idempotent calls, get-or-create by name, never touch objects you did not create (SC).
- Stated timeouts disagree: 15-30 s (VG), legacy socket 180 s (RL), 15 s helper default (OG). Measure on target. Poly Haven downloads freeze the UI; ask 1k-2k (AH).
- On timeout: inspect state, do not resubmit (RL). Save `save_as_mainfile(copy=True)` per stage (SC).

### 1.5 Headless contract
`blender -b [file.blend] --factory-startup --python-exit-code 1 -P script.py -- args` (SC, EL).
- `--factory-startup`: without it user add-ons load (one made network calls on SC's machine [B]). `--python-exit-code 1`: else a failed export exits 0 (KI [B]). IB adds `--disable-autoexec`.
- Args run left to right: `-o -F -E` before `-f`/`-a`.
- Return data via JSON file or a final `RESULT {...}` line; never parse logs (5.0 changed format).
- One Blender process at a time per agent. Quote paths; absolute paths headless.
- Binary: `$BLENDER` > PATH > `/Applications/Blender.app/Contents/MacOS/Blender`; never assume it exists, report `missing_tool` (KJ, MM).
- Batch: N processes, shard `i/N` (EL).

## 2. The agent loop

1. Brief in numbers: purpose, budgets (tris, texture px, MB), style, references (SC).
2. Read state first. Official summary has no vertex counts: use Python on `bpy.data`; community `get_scene_info` has no dimensions (KI).
3. Plan big to small; one change per call.
4. Capture: frame the viewport on the subject first (KI rule 22: unframed view shows a prop as a few pixels; official `jump_to_view3d_object_by_name`), then screenshot. Two opposite angles after texturing; KI wants 4+ captures per asset (its bench saw one).
5. Gate numbers AND image: audit script plus review sheet (SC: silhouette, matcap, wire from front/side/three-quarter/low). Judge with a rubric: first read, value structure, form, colour, composition, artifacts.
6. Fix before advancing (a blockout defect costs one script, after texturing costs the stage). NEVER report done without looking at a render.

Visual validation:
- Headless has no screenshot: render. Workbench needs no GPU; EEVEE needs a GL context even headless; Linux CI needs Mesa EGL (KJ [B]).
- Prefer a render to a screenshot for materials/light (RL). Official `render_viewport_to_path` writes to Blender's scratch dir: read returned `result.filepath`, never a stale file (RL).
- The viewport is not evidence (MM): `hide_render`-only objects still show there.
- Reference matching: blockout silhouette IoU >= 0.85, band widths within 0.05; forms 0.90 / 0.03; proportions within 5% then 2% (MM [P]). AR: max 3 compare loops. JT: two repeats of the same failure means change approach.
- Never lose user work: no `read_factory_settings`, no deleting data you did not create, backup before batch edits (EL, KI).

## 3. Modelling

Order (RL 11-step, SC, JT): reference, **block-out at real size** (1 unit = 1 m), camera lock, light v1, refine forms, flat-value materials, light v2, detail, final render, composite, export. RL time split: lighting 10-20%, modelling 30-40% [P]; "90% modelling, 10% lighting" is the anti-pattern.

ALWAYS: look up real dimensions (RL); label unseen surfaces "inferred" (MM, JT); apply rotation and scale before bevel/solidify/array/bake/export; keep objects returned by `new()` (never re-fetch by requested name); tag owned data; data API/bmesh over operators (600 `primitive_monkey_add` 4.16 s vs `objects.new` 0.015 s [B, SC]).

Hard-surface (SC): cut first, bevel after, normals last. Booleans above a 30-degree micro bevel (Harden Normals, Miter Outer Arc; ~3 mm body, 1 mm small parts, 3 segments render, 1-2 game), Weighted Normal at the bottom, Mirror late; design bevel weight-limited, 8-12 segments. Solver EXACT; open cutters break Exact and silently skip in Manifold [B]. Walls/steps/grooves wider than 2x micro width or Clamp Overlap shrinks the bevel object-wide [B]. If Harden/Weighted Normal change nothing, the face is not flat. Judge in shiny matcap, close up on every cut. School A (n-gons + booleans) for planar machined parts; School B (quad cage + subdivision, support loops) for continuous curvature or sculpt bakes.

Procedural / Geometry Nodes (SC): fields are deferred questions; prefer trait selections (position, normal, proximity) over index; simulate only if history matters (else drive from Scene Time); loops last; everything is object-local; tools not trees (expose dependencies as group inputs). Use Essentials assets first; keep instances. **Web trap: GN output exists only as a modifier result, so `export_apply=False` writes the base mesh and the procedural asset is lost silently** (KI [B]: 2,688 tris became 2). Apply GN on an export copy.

Image-to-3D (JT, MM): fidelity contract first (target use, critical features per view, unseen surfaces inferred or more views requested); missing evidence stays UNKNOWN; never weaken the rubric after a failed candidate. Silhouette before form, form before detail, topology before texture.

Gotchas [B, SC]: `obj.data` ignores modifiers (use `evaluated_get` + `to_mesh()` + `to_mesh_clear()`); `matrix_world` stale until `view_layer.update()`; Edit Mode keeps its own mesh copy; iterate `collection[:]` when renaming; 0-user datablocks are not saved.

## 4. Materials and PBR

Rules (EL, SC):
1. Metallic binary 0/1 except transition pixels. Dielectric base sRGB ~30-240; metals 180-255.
2. Roughness carries realism: vary +-0.1-0.2; uniform looks CG.
3. Base Color and Emission sRGB; roughness, metallic, normal, AO, height, opacity `Non-Color`, set before writing pixels or baking (top bug).
4. Normal map OR displacement, never both; bump Distance is real height of 0..1.
5. Keep IOR 1.5 and Specular IOR Level 0.5 for dielectrics. Build effects as grey masks into Mix/HSV.
6. Bevel, AO, Pointiness nodes are Cycles-only and stochastic: bake before thresholding (SC [B]).

Principled v2 (4.0+): `Subsurface Weight`, `Specular IOR Level`, `Transmission Weight`, `Coat Weight`, `Sheen Weight`, `Emission Color` + `Emission Strength` (default 0). 5.2 adds `Thin Wall`. Find nodes by `type`, not localised name (EL, KI, MM). `use_nodes` is a deprecated no-op.

Glass/alpha: `surface_render_method` `DITHERED` or `BLENDED`; exports as KHR_materials_transmission/ior/volume. CZ [P]: web glass alpha ~0.45 with slight tint; window emission ~3 (above ~7 AgX whites out). Judge under 2-3 HDRIs (EL). Imports: check licence and scale; convert Diffuse BSDF to Principled (VG).

glTF packing: R=AO, G=roughness, B=metallic; AO needs a custom "glTF Material Output" group (EL). OpenGL normals; DirectX flips G; never JPEG normals. Only image-texture to Principled chains export.

## 5. UV and baking

UV (SC): seams follow method (few and hidden for 2D paint; more when baking); hard edges are seams when baking. **Always pass `method=` to `uv.unwrap`** (5.2.1 default CONFORMAL [B]). Padding res/128 (16 px at 2K). Density: 10.24 px/cm FPS, 5.12 third person, 2.56 top-down; coverage >70%. Stacked/mirrored islands move a tile out before baking. Bake with no UV layer errors obscurely (KJ).

Bake (SC, EL):
1. Pre-flight: scale applied, audit clean, low triangulated like the target, hard edges = seams, parts exploded or per pair, high covers low.
2. Cycles only. Target image node **active and selected** in every low material (5.0 bakes only to selected).
3. Test 512, final 2048. Samples: normal 16, AO 64-256, margin res/128. Extrusion > farthest high protrusion (default ~2% of low diagonal); cage when uniform fails; AO distance ~0.2 x bbox diagonal.
4. Gate in pixels: normal blue < 0.5 = rays hit far side; exactly flat = missed; all-white AO = distance too small; inverted texels < 2% (adaptive 1.2-2.2% vs single pass 7-8% [B]). Numbers over thumbnails (KJ).
5. EXR float: `Non-Color` before `save()` or values come out sRGB-encoded [B].
6. Procedural to texture: bake via Emission, 30+ samples, rebuild from the maps.

Baked lighting for web (CZ [P]): per-room light rigs; second UV layer (`smart_project` angle 1.2, margin 0.0006); Cycles DIFFUSE direct+indirect, colour off, ~64 samples, margin 3, 2048 float atlas; median then Gaussian 3x3; RGBE `.hdr`. NEVER carry RGB lighting in the glTF occlusion slot. Skip for single-sun exteriors.

## 6. Lighting, look-dev, cameras

- Compose and lock camera first (lighting is view-dependent), then lights, then materials (RL, SC).
- Value separation first, checked desaturated; darken the set before brightening the subject (SC).
- Size and distance are the controls: face key head-sized or larger; no fixed key:fill ratio; every light motivated; rim on key side (SC).
- Product 3-point (EL): key ~45 degrees side, 30-40 up; fill opposite at 1/3; rim behind; area lights sized ~ object; neutral grey backdrop. Reflective product: shape the softbox reflections.
- Brightness through `view_settings.exposure`, never by scaling lamps. AgX hides clipping: read the EXR (linear 4.0 displays 0.91 [B]).
- Colour: AgX default; **Khronos PBR Neutral for brand colour** (error of 255: Khronos 3.8, AgX 27-42, Standard 33 [B]); match three.js `AgXToneMapping` / `NeutralToneMapping` (CZ, EL). One view transform per project; looks are view-prefixed (`AgX - Punchy`).
- Cycles film: 3 bounces, no caustics, 100 test / 500-1500 final spp (SC). EEVEE: ray tracing off by default; bake volume probes for interiors.
- Cameras (EL): 24-35 mm interiors (level camera, shift not tilt), **85-135 mm product** (3/4 view, 10-25 degrees up), DOF f/2.8-5.6 at real scale, tight clip.
- `light_linking`/`lightgroup` live on the Object. 5.x sky types: `SINGLE_SCATTERING`, `MULTIPLE_SCATTERING`, `PREETHAM`, `HOSEK_WILKIE`.

## 7. Rendering stills, turntables, loops for marketing

1. Render contract (IB): audience, still/turntable/sequence, resolution, fps, engine, device, time budget, passes, alpha, colour management; named constants in the scene script; set everything explicitly.
2. Low-sample diagnostic per camera; open the images.
3. EEVEE to iterate, Cycles as truth for glass/close-ups; within ~30% on the subject (SC).
4. Cycles levers (EL): adaptive sampling (0.01 final / 0.05 preview) + OIDN with albedo+normal; product paths total 12, glossy 4, transmission 8-12; clamp indirect 5-10 and `blur_glossy` 0.5-1 for fireflies; fewer bigger lights. Presets: preview 64 spp 50% res, final 512, product 1024 transparent.
5. Denoise once (IB): preview OIDN Fast at 16-32 spp; final OIDN High, Accurate prefilter, colour+albedo+normal.
6. Apple Silicon: METAL only (adding CPU ~2x slower); 12-20 s/frame at 1080p 48-64 spp (MM [B]); `use_persistent_data` for animation.
7. Turntable (EL, SC): **orbit camera and lights, never the asset**; 120-240 frames, 24-30 fps, 85 mm; linear interpolation with frame N+1 == frame 1 for a seamless loop; 18% grey cyclorama; contact shadow.
8. Frames first (numbered PNG/EXR, skip existing so a crash resumes), then ffmpeg. 5.0: set `image_settings.media_type='VIDEO'` before `file_format='FFMPEG'`; try the assignment, enum lists under-report (KJ).
9. Transparent: `film_transparent=True` + PNG/EXR. Compositor bloom = Glare node; tree lives on `scene.compositing_node_group`.
10. Done when the source reproduces the render in a clean process; report paths, versions, samples, denoise, colour management, duration (IB).

## 8. Export to web (glTF) and hand-off to gltf-transform

1. Pre-export: apply rotation/scale, fix normals/doubles, unique ASCII names, no negative scale, <=4 influences, props' origin at base.
2. Material audit (VG idea): flag Noise/Voronoi/Wave, Color Ramp, complex Mix factor, no Principled, textures >2048, Normal Map via Bump node, image materials without UVs.
3. Bake or simplify failures, or name materials and patch at runtime (CZ: zero bytes).
4. Scope: select one root hierarchy (`use_selection=True`), never the whole scene; `export_cameras=False`, `export_lights=False` (runtime lights).
5. Export **raw, uncompressed** headless: `export_format='GLB'`, `export_image_format='AUTO'`, `export_extras=True`, `export_gpu_instances=True` for linked duplicates, Draco off (VG, CZ). Keep the raw GLB.
6. Parse the result: size, meshes, materials, images, animations, tris, extensions (EL).
7. gltf-transform as **individual measured steps** with `inspect` before/after. VG/KI: `resize` 1024, `webp` q85-90, mesh compression last. CZ: dedup, instance, join(keepNamed), weld, resample, prune(keepLeaves), sparse, webp, meshopt.
8. Verify independently: gltf-viewer.donmccurdy.com, Babylon Sandbox, Khronos validator, GLTFLoader console, then the real app by pixels (CZ).

ALWAYS keep names stable (names are the contract with runtime code); use named pivot Empties for JS-driven motion. NEVER Draco twice; NEVER trust Blender names in code.

| What breaks | Result |
|---|---|
| Procedural textures, Color Ramp, Mix factors | Lost; roughness falls to socket default |
| Normal Map via Bump node | WebP export writes a texture with no source; GLTFLoader rejects the whole file (CZ) |
| Displacement, bump-from-noise | Not exported; bake a normal map |
| Drivers | Not exported; keyframed actions are |
| Collection instances | Expand to node trees: draw calls multiply |
| Array modifier baked | Size balloons (VG: 1 MB to 56 MB, one rig) |
| GN modifier output | Lost unless applied (KI) |
| Names | Spaces to `_`, dots removed (`Sphere.003` to `Sphere003`), dupes suffixed |
| Meshopt GLB | Blender cannot re-import it (KJ [B]); Draco can; Draco changes vertex counts, compare triangles |
| meshopt quantisation | Int16 positions with scale in node matrix: dequantise before transforming (CZ) |
| `flatten()` / `palette()` / `instance()` | flatten kills JS pivots; palette merges material names; instance skipped when any animation exists (CZ) |
| Animation | Action with no armature user skipped; `export_animation_mode` ACTIONS/ACTIVE_ACTIONS/NLA_TRACKS/SCENE (EL) |

`export_apply` conflict: VG/KI False, CZ/RL True. My synthesis [U]: decide per modifier on an export copy: apply shape-defining ones (bevel, boolean, GN, mirror); keep repeats as linked duplicates + `export_gpu_instances`.

Compression (VG, CZ): WebP cuts download not VRAM; only resize or KTX2 (ETC1S colour, UASTC normals, needs `ktx` CLI) cuts VRAM. RGBA with mips: 4096 ~85-89 MB, 2048 ~21, 1024 ~5.5, 512 ~1.4. CZ [P, unmeasured by us]: meshopt decodes 5-10x faster than Draco. Preload the model; `compileAsync` before reveal.

## 9. Blender 5.x version traps

[V via SC release-note links; most [B] re-tested in 5.2.1.] 5.2 LTS dated 2026-07-14; 5.1 = Python 3.13.
| Remembered code | 5.x reality |
|---|---|
| `engine='BLENDER_EEVEE_NEXT'` | `'BLENDER_EEVEE'` (5.0); assign in try/except |
| `op({ctx dict})` | `with context.temp_override(...)`; check `op.poll()` |
| `scene.use_nodes` / `scene.node_tree` | `scene.compositing_node_group`; no Composite node (Group Output); node options are input sockets |
| `file_format='FFMPEG'` alone | set `media_type='VIDEO'` first |
| `action.fcurves` | removed 5.0; channelbags via `bpy_extras.anim_utils`; set `action_slot`. **VG's own animation-extraction script uses it and breaks** |
| `mat.use_nodes = True` | deprecated no-op |
| Principled `Specular`/`Subsurface`/`Transmission`/`Clearcoat`/`Emission` | v2 names; Emission Strength defaults 0 |
| `mesh.use_auto_smooth` | removed 4.1: `shade_smooth_by_angle` (writes `sharp_edge`), Smooth by Angle GN modifier, or `mesh.set_sharp_from_angle` (CZ) |
| `mod["Socket_2"]=v` (GN) | `mod.properties.inputs.<identifier>.value` (5.2) |
| `ng.inputs.new` | `ng.interface.new_socket(...)` |
| Boolean `FAST` | `FLOAT`; `EXACT` default, `MANIFOLD` 4.5+ |
| Musgrave, Separate/Combine RGB, Velvet, Point Density | removed; Noise fractal types, Separate/Combine Color, Sheen |
| Sky `NISHITA` | not in enum |
| `paint.brush_set`, `sculpt_tool` | brush assets (`brush.asset_activate`), `sculpt_brush_type` |
| EEVEE bloom/SSR/GTAO toggles | Glare node, `use_raytracing`, `use_fast_gi`; probes `SPHERE/PLANE/VOLUME` |
| Passes `Z`, `DiffCol`; spaces `Linear`, `Raw` | `Depth`, `Diffuse Color`; `Linear Rec.709`, `Non-Color` |
| `ob["x"]` for `bpy.props` | attribute access only |
| `bgl` | removed; `gpu`; `gpu.init()` in background (5.2) |
| glTF kwargs from old scripts (`export_nla_strips`) | [U] may be renamed; filter kwargs by `op.get_rna_type().properties` |

Meta-rule (SC, EL): ask Blender: `dir(obj)`, `T.bl_rna.properties.keys()`, `op.get_rna_type().properties`, official `search_api_docs`, KI `bpy_api_lookup`. `hasattr(bpy.types.Mesh, "prop")` is False for RNA properties. Sources are stale about themselves: RL pro-workflow Recipe 2 sets `BLENDER_EEVEE_NEXT`; QW uses `NISHITA`; VG tool `screenshot` predates AH `look`. Probe before trusting any remembered snippet.

## 10. Asset QA (PASS / WARN / FAIL)

Order (EL, KJ): QA, optimise, QA again, export, verify file. Report tris per object, fixes, accepted warnings with reasons.

| Check | FAIL | WARN | Src |
|---|---|---|---|
| Unapplied/negative scale | any | | EL, SC |
| Non-manifold / flipped normals / inside-out | any | boundary edges (non-print) | EL (KJ welds a scratch copy first, else hard edges read as open) |
| Missing texture files; textured mesh with no UV | any | | KJ, EL |
| Z-fighting, back-to-back faces, floating parts | | any, explain intent | EL |
| Duplicate verts, degenerate faces, n-gons | | any (n-gon ok on flat hard-surface) | EL |
| Texture px | | >2048 hero web (KJ lax 4096) | EL, VG |
| Tris | | hero >30k, prop >10k (EL; KJ 300k) | [conflict] |
| Materials per asset | | >2 | EL |
| GLB size | | hero >5 MB, scene >20 MB (EL 2-5 / 10-20; RL 8 soft / 15 hard; VG raw <30, optimised <5) | [conflict] |
| GPU estimate (`gltf-transform inspect`) | >100 MB | >50 MB | VG |
| Skin | >4 influences | >100 bones | EL |
| Engine verts | | 1.5-3x Blender's (seams, hard edges) | EL |
| Round-trip vs manifest | counts differ | height off >1% | MM |
| Bake inverted texels | >2% | miss >2% | SC |

Visual: contact sheet (clay, random colour per object exposes detached pieces, wire), matcap close-ups, PSNR/SSIM before/after decimation (KJ). Draw calls (CZ, EL): one object per (material, animation root); merge by nearest animated ancestor (2,091 to 330 meshes [B, one scene]); never merge objects with animated ancestor, shape keys, drivers, custom split normals; LOD 50/25/12.5% at screen size 0.5/0.25/0.125.

## 11. Reusable script patterns (describe; write our own)

1. **Headless runner**: locate Blender, `--factory-startup --python-exit-code 1`, args after `--`, JSON result file, timeout, `--dry-run` (KJ, EL).
2. **Idempotent managed script** (SC P1, CZ): get-or-create collection; delete only tagged objects; rebuild; `view_layer.update()`; validate; save absolute; one JSON report; rerun creates no `.001` twins.
3. **Scene probe**: world bbox via `matrix_world @ corner`, poly counts, materials, parents, array counts; iterative traversal (VG, CZ).
4. **Material export audit** and **mesh QA** (section 8 step 2, section 10), profiles game/render/print.
5. **Review sheet**: temporary scene, fixed views, silhouette/matcap/wire/clay/checker modes, user settings untouched (SC, KJ).
6. **Turntable rig** with replaceable `LD_Lookdev` collection (EL); **export wrapper** with scoped root, GLB parse, size gate (EL, CZ); **round-trip check** (MM).
7. **Bake high to low** with adaptive extrusion and pixel metrics (SC); **BVH orphan sweep** and **draw-call consolidation** (CZ).
8. **Numpy bulk access** (`foreach_get/set`: 491k verts, 105 ms loop vs 0.1 ms [B, SC]); **batch shard runner**; **compare sheet + IoU**.

## 12. Conflicts between sources
| Topic | A | B | Lean |
|---|---|---|---|
| `export_apply` | False (VG, KI) | True (CZ, RL) | Per modifier; GN must be applied |
| Mesh compression | Draco last (VG, KI) | meshopt (CZ, EL) | Glb lane decides; keep uncompressed source |
| `gltf-transform optimize` | NEVER, simplify destroys geometry (VG, KI) | use with `--texture-compress ktx2` (EL) | [U] VG looks overstated; glTF lane to test |
| Web texture cap | 1024 (VG, KI, RL) | 1-2k (EL), 4096 (KJ) | 1024 default, 2048 hero close-ups |
| Tri budget | EL hero 10-30k | KJ 300k | EL |
| MCP timeout | 15-30 s (VG) | 180 s (RL) | Measure |
| Community tool count | nine (AH) | 36 (KI) | Read schemas live |
| Hard-surface order | cut, bevel, normals (SC) | AR bevel above boolean | SC (measured) |
| Boolean solver | EXACT (SC) | FLOAT/MANIFOLD for speed (EL) | EXACT |

## 13. Router signals (for the `3d` skill)
Route here on: "blender", ".blend", "bpy", "blender-mcp", "poly haven", "sketchfab", "make/model a 3D model", "turntable", "product/hero render", "bake", "UV unwrap", "retopo", "geometry nodes", "hard-surface", "procedural", "export GLB from Blender", "materials lost on export", "flat in three.js after export".
Sub-route: channel (MCP/headless), then modelling / materials / UV-bake / lighting / render, then export. Hand to the glTF pack once a GLB exists and Blender is no longer the editor; to three.js/R3F for loader, tone mapping, runtime patches; to art-direction for brief and critique.
NOT here: compressing an existing GLB (glTF pack), pure three.js or shaders, Spline, generative 3D (separate optional area, though AH/KI MCPs expose it).
Preflight to detect and propose (never auto-install): `blender` on PATH or `/Applications/Blender.app`, version (5.1+ for official MCP), `uv`, listed MCP servers, port 9876, `node`/`gltf-transform`, `ktx`.

## 14. Sources and gaps
All under `docs/research/community-scan/sources/` (scenario commit 49dd26e) plus live `gh api` reads of the remaining scenario, EL, KJ and MM files. EL has 20 skills; rigging, shapekeys, sculpting, simulation, animation, scene-setup, addon-development and retopology-uv were not read.
Gaps: no source tests 5.2 glTF exporter kwargs end to end; none measures MCP timeouts or official `render_*` timings; Draco/meshopt option names need R2 confirmation.
