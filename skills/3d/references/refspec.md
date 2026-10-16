# Reference Spec Schema

Purpose: Define `refspec.v1`, the structured result of reference analysis, so brief, build and verification read one shape.

Read when:
- Writing or validating `.3d/reference-spec.json`.
- Turning a refspec into an image or video generation prompt.

Skip when:
- Choosing what numbers to put in three.js or Blender (→ [refspec-mapping](refspec-mapping.md)).
- Deciding how to analyse a reference (→ [intake-references](intake-references.md)).

Inputs:
- `scripts/ref-extract` output and your vision passes.

Produces:
- A valid `.3d/reference-spec.json`; an example is `assets/templates/refspec.example.json`.

## Contents

- Leaf rule · Top-level keys · Dimension fields · Video block · Rendering to prompts · Validation

## Leaf rule

Every estimated numeric or judgement field is a leaf object, never a bare value. Descriptive enums and labels (`sensor`, `dir_clock`, `key.type`, `hardness`, `surface`, `content`) may stay bare strings:

```json
{ "value": "soft", "confidence": "med", "evidence": "read" }
{ "range": [28, 50], "confidence": "low", "evidence": "inferred" }
```

- Exactly one of `value` (enum, string, number, hex) or `range` ([lo, hi], same unit).
- `confidence`: `high` | `med` | `low`. `evidence`: `measured` | `read` | `inferred` | `assumed` | `unknown`.
- `inferred` and `assumed` leaves must use `range` for numbers. `unknown` leaves carry no value.
- Arrays of items (palette, materials, layers, shots) hold leaf objects inside each item; the array itself is not a leaf.
- Units: angles in degrees, lens in mm full-frame equivalent, fractions 0-1, colour `#rrggbb`.

## Top-level keys (order is fixed: global, structural, detail)

Compatible with the `generate-image` attribute tree: `type` first; `camera{lens,angle,framing,focus,depth}` and `lighting{type,quality,mood}` names are reused when rendering to a prompt.

| Key | Content |
|---|---|
| `schema` | `"refspec.v1"` |
| `refs[]` | `id`, `path`, `kind` image\|video, `role`, `intent`, `weight`, `meta{w,h,fps,duration_s,exif,color}` |
| `type` | one phrase: "photoreal product still", "stylised 3D scene" |
| `medium` | photoreal · cgi-real · stylised-3d · toon · clay · low-poly · isometric · flat-vector · painterly · mixed |
| `style_tokens` | 1-3 observable technique tokens, no artist names |
| `anchors[]` | 3-5 strings, most similarity-critical first |
| `aspect` | ratio, orientation |
| `composition` · `camera` · `lighting` · `colour` · `materials[]` · `form` · `fx` | below |
| `hidden_or_unknown[]` | what the reference cannot show |
| `conflicts[]` | `{field, owners, chosen, reason}` |
| `negative_prompt[]` | wrong medium, things not to copy |
| `video` | video references only |

## Dimension fields

- **composition**: `framing` (centred, thirds, golden, diagonal, symmetrical, radial) · `subject_frac` (subject bbox area / frame) · `subject_pos{x,y}` (0-1, origin top-left) · `horizon_y` · `leading_lines[]` · `negative_space{where,frac}` · `layers[]{depth fg|mid|bg, content, blur}`.
- `focal_class` (full-frame equivalent): ultra-wide <20 mm · wide 20-35 · normal 35-60 · tele 60-135 · long >135. Only the class is reliable from a picture.
- **camera**: `shot_size` (ECU CU MCU MS MWS WS EWS) · `angle` (eye, low, high, top-down, dutch) · `tilt_deg` · `roll_deg` · `height` (floor, knee, waist, eye, above-head, aerial) · `focal_class` · `focal_mm_ff` · `sensor` (default "FF 36x24, assumed") · `fov_v_deg` · `perspective{vp_count, convergence, distortion}` · `dof{look, focus_plane, bokeh}` · `lens_artefacts[]`.
- **lighting**: `key{dir_clock, elev_deg, type sun|softbox|window|overcast|practical|neon|area, hardness, k, color}` · `fill{ratio_stops, dir, color}` · `rim{present, dir, strength, color}` · `practicals[]` · `env{kind studio|outdoor-sun|overcast|sunset|night-city|interior|void|gradient, contrast}` · `time_of_day` · `shadows{hardness, density, contact}` · `volumetrics` · `mood` (free text with concrete causes).
- **colour**: `palette[]{hex, role dominant|support|accent|shadow|highlight, share}` · `value_key` · `contrast` · `luma_p1_p50_p99` · `saturation` · `temp_overall` · `grade{shadows_tint, highlights_tint, lut_family}`.
- **materials[]**: `surface`, `coverage`, `base_color`, `roughness` (range), `metalness` (0 or 1), `anisotropy`, `clearcoat`, `transmission`, `ior`, `sss`, `emissive`, `normal_relief`, `pattern_scale`, `wear`.
- **form**: `primitives[]`, `macro_meso_micro`, `symmetry`, `shape_language`, `bevel`, `topology_note`.
- **fx**: `bloom`, `halation`, `chromatic_aberration`, `grain`, `vignette`, `motion_blur`, `particles`, `outline`.

## Video block

`video{shots[], cuts_per_10s, loop{seamless, loop_t}, audio_sync}`. Each shot: `n`, `t_in`, `t_out`, `shot_size`, `angle`, `camera_move{type, dir, amount, curve, parallax}`, `subject_motion` (verbs), `beats[]{t, what}`, `speed`, `spec_ref` (the keyframe's own refspec id), `transition_in/out`. `camera_move.type`: static, pan, tilt, dolly, truck, pedestal, push-in, pull-out, orbit, arc, crane, handheld, whip, zoom, roll. `curve`: linear, ease-in, ease-out, ease-in-out, overshoot, or `sampled` with a list of 8-16 normalised points. These shots feed `shots.json` ([brief-spec](brief-spec.md)).

## Rendering to prompts

- Still prompt (`generate-image` shape): join in this order: medium, subject, setting, composition and camera, light, colour, style tokens, quality, ratio. Photoreal subject needing consistency: use the attribute tree. Recommend that skill when installed; never invoke it.
- Video prompt (`generate-video` shape): shot plus subject, subject motion, camera move (one primary), pacing, light and medium, constraints. Ratio, resolution and duration are API parameters, not prompt text.
- Lead any prompt with `anchors[]`; put `negative_prompt[]` last.

## Validation

1. `python3 -m json.tool .3d/reference-spec.json` parses.
2. `schema` is `refspec.v1`; every `refs[].id` is unique.
3. No `inferred` or `assumed` leaf holds a bare number.
4. Every `measured` leaf equals the script output.
5. `anchors` has 3-5 entries; `hidden_or_unknown` is not empty.
