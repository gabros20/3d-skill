#!/usr/bin/env python3
"""Texture prep on a single image: seam test, cross-fade tiling, de-light, map derivation.

Runs only inside Blender (bpy + the numpy that ships with it, so EXR and 16-bit PNG read fine).
No scene is touched and no .blend is saved:

    blender -b --factory-startup --python-exit-code 1 \
        --python <skill>/assets/blender/texture_prep.py -- --seam albedo.png

One mode per run (args after `--`):
  --seam IMG                 wrap-around seam ratio (edge step / typical neighbour step); exit 1 above --max-seam
  --tile IMG --out OUT       cross-fade the half-offset copy over the image so it tiles (organic textures only);
                             exit 1 if the result still fails the seam test
  --delight IMG --out OUT    divide out low-frequency luminance (baked light / vignette) with a wrap-safe blur
  --derive IMG --out-dir DIR write <stem>_normal / _roughness / _height beside each other in DIR
  --report IMG               size, depth, seam ratio and low-frequency luminance spread; exit 1 above --max-seam
Options:
  --max-seam R       seam pass threshold (default 1.3)
  --fade F           --tile blend band as a fraction of the half-image (default 0.5; 1 = widest, softest)
  --sigma-frac F     --delight blur sigma as a fraction of the short side (default 0.1)
  --strength S       --delight: gain exponent 0..1 (default 1) | --derive: normal strength (default 2)
  --max-lowfreq C    --delight exit 1 if the low-frequency luminance spread (std/mean) stays above C (default 0.12)
  --linear           treat the input as linear light (default: sRGB-encoded, except .exr)
  --height luma|FILE --derive height source: luminance of IMG (default) or a grey file
  --smooth PX        --derive pre-blur of the height in pixels (default 1.0)
  --rough-range A,B  --derive roughness range (default 0.4,0.9; bright albedo = smoother)
  --depth 8|16       --derive bit depth of the data maps (default 16); --tile/--delight keep 8-bit unless
                     OUT is .exr or --depth 16
  --stem NAME        --derive output stem (default: input name without a trailing _albedo/_basecolor/_diff/_col)
Normals are OpenGL (green up); flip G for DirectX. Output colour spaces: colour = encoded as authored,
data maps = Non-Color. Pixel rows are read bottom-up, as Blender stores them.
Prints one JSON line {"ok","mode",...}. Exit 0 ok / 1 problems / 2 usage.
"""
from __future__ import annotations

import json
import os
import re
import sys

try:
    import bpy
    import numpy as np
except ImportError:  # pragma: no cover - plain python
    sys.stderr.write("texture_prep.py runs only inside Blender (see the docstring)\n")
    sys.exit(2)

MODES = ("seam", "tile", "delight", "derive", "report")
FLAGS = {"linear", "help"}
VALUED = {"seam", "tile", "delight", "derive", "report", "out", "out-dir", "max-seam", "fade", "sigma-frac",
          "strength", "max-lowfreq", "height", "smooth", "rough-range", "depth", "stem"}


def usage(msg: str = "") -> None:
    sys.stderr.write(__doc__ + ("\n" + msg + "\n" if msg else ""))
    sys.exit(2)


def parse_args() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o: dict = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if not a.startswith("--"):
            usage("unexpected argument: %s" % a)
        k = a[2:]
        if k in ("help", "h"):
            print(__doc__)
            sys.exit(0)
        if k in FLAGS:
            o[k] = True
            i += 1
        elif k in VALUED and i + 1 < len(argv):
            o[k] = argv[i + 1]
            i += 2
        else:
            usage("unknown or incomplete arg: %s" % a)
    modes = [m for m in MODES if m in o]
    if len(modes) != 1:
        usage("pick exactly one of --seam/--tile/--delight/--derive/--report")
    o["mode"] = modes[0]
    try:
        o["max_seam"] = float(o.get("max-seam", 1.3))
        o["fade"] = min(1.0, max(0.05, float(o.get("fade", 0.5))))
        o["sigma_frac"] = float(o.get("sigma-frac", 0.1))
        o["max_lowfreq"] = float(o.get("max-lowfreq", 0.12))
        o["smooth"] = float(o.get("smooth", 1.0))
        o["depth"] = int(o["depth"]) if "depth" in o else None
        lo, hi = (float(x) for x in o.get("rough-range", "0.4,0.9").split(","))
        o["rough_range"] = (lo, hi)
        o["strength_set"] = "strength" in o
        o["strength"] = float(o.get("strength", 2.0 if modes[0] == "derive" else 1.0))
    except ValueError:
        usage("numeric option could not be parsed")
    if o["depth"] not in (None, 8, 16):
        usage("--depth must be 8 or 16")
    if o["mode"] in ("tile", "delight") and "out" not in o:
        usage("--%s needs --out" % o["mode"])
    if o["mode"] == "derive" and "out-dir" not in o:
        usage("--derive needs --out-dir")
    return o


# ---- image io (raw values: nothing is colour-converted on the way in or out) --------------------------------


def load(path: str):
    """Return (float32 array h x w x 4, info). Rows bottom-up; values exactly as stored in the file."""
    if not os.path.isfile(path):
        raise FileNotFoundError("no such image: %s" % path)
    im = bpy.data.images.load(path, check_existing=False)
    try:
        im.colorspace_settings.name = "Non-Color"
        w, h = im.size
        buf = np.empty(w * h * 4, np.float32)
        im.pixels.foreach_get(buf)
        info = {"width": w, "height": h, "channels": im.channels, "float": bool(im.is_float)}
        return buf.reshape(h, w, 4), info
    finally:
        bpy.data.images.remove(im)


def save(path: str, arr, depth: int | None = None) -> str:
    """Write raw values. .exr = float; .png/.jpg 8-bit unless depth == 16 (PNG only)."""
    ext = os.path.splitext(path)[1].lower()
    fmt = {".png": "PNG", ".exr": "OPEN_EXR", ".jpg": "JPEG", ".jpeg": "JPEG", ".tif": "TIFF",
           ".tiff": "TIFF"}.get(ext)
    if fmt is None:
        raise ValueError("unsupported output extension %r (use .png .exr .jpg .tif)" % ext)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    h, w = arr.shape[:2]
    depth = 16 if (depth == 16 and fmt in ("PNG", "TIFF")) else 8
    wide = fmt == "OPEN_EXR" or depth == 16
    im = bpy.data.images.new("tp_out", w, h, alpha=False, float_buffer=wide)
    try:
        im.colorspace_settings.name = "Non-Color"
        out = np.ascontiguousarray(np.clip(arr, 0.0, 1.0) if fmt != "OPEN_EXR" else arr, np.float32)
        out[..., 3] = 1.0
        im.pixels.foreach_set(out.ravel())
        im.update()
        if wide:
            s = bpy.context.scene
            ims = s.render.image_settings
            ims.file_format = fmt
            ims.color_depth = "32" if fmt == "OPEN_EXR" else "16"
            ims.color_mode = "RGB"
            ims.color_management = "OVERRIDE"
            ims.view_settings.view_transform = "Raw"
            ims.linear_colorspace_settings.name = "Non-Color"
            im.save_render(path, scene=s)
        else:
            im.filepath_raw = path
            im.file_format = fmt
            im.save()
    finally:
        bpy.data.images.remove(im)
    return path


# ---- numerics -----------------------------------------------------------------------------------------------


def srgb_to_linear(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def blur_wrap(a, sigma: float):
    """Gaussian blur by FFT: periodic by construction, so it never invents an edge."""
    if sigma <= 0:
        return a
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    k = np.exp(-2.0 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * k)).astype(np.float32)


def seam_stats(arr) -> dict:
    """Edge step across the wrap seam vs the mean step between interior neighbours, per axis."""
    a = arr[..., :3]

    def ratio(seam, inner):
        s, i = float(np.mean(np.abs(seam))), float(np.mean(np.abs(inner)))
        if i < 1e-6:
            return 1.0 if s < 1e-6 else 99.0
        return s / i

    rx = ratio(a[:, 0] - a[:, -1], a[:, 1:] - a[:, :-1])
    ry = ratio(a[0] - a[-1], a[1:] - a[:-1])
    return {"x": round(rx, 3), "y": round(ry, 3), "ratio": round(max(rx, ry), 3)}


def lowfreq_spread(arr, linear: bool, sigma_frac: float) -> float:
    lum = luma(arr if linear else srgb_to_linear(arr))
    low = blur_wrap(lum, sigma_frac * min(lum.shape))
    m = float(np.mean(low))
    return float(np.std(low) / m) if m > 1e-6 else 0.0


def is_linear(path: str, opts: dict) -> bool:
    return bool(opts.get("linear")) or path.lower().endswith(".exr")


def tile(arr, fade: float):
    """Cross-fade each axis in turn with the half-offset copy. The blend weight is 0 on the borders (where
    the offset copy is continuous across the wrap) and 1 in the middle (where the offset copy's own seam
    sits). One axis at a time: a 2D product mask would leave a visible cross wherever one weight is < 1."""
    def ramp(n):
        t = 1.0 - np.abs(2.0 * (np.arange(n) + 0.5) / n - 1.0)
        t = np.clip(t / fade, 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    h, w = arr.shape[:2]
    wx = ramp(w)[None, :, None]
    out = arr * wx + np.roll(arr, w // 2, axis=1) * (1.0 - wx)
    wy = ramp(h)[:, None, None]
    return out * wy + np.roll(out, h // 2, axis=0) * (1.0 - wy)


def delight(arr, linear: bool, sigma_frac: float, strength: float):
    rgb = arr[..., :3] if linear else srgb_to_linear(arr[..., :3])
    lum = luma(rgb)
    low = blur_wrap(lum, sigma_frac * min(lum.shape))
    gain = np.clip(np.mean(low) / np.maximum(low, 1e-4), 0.5, 2.0) ** max(0.0, min(1.0, strength))
    out = rgb * gain[..., None]
    if not linear:
        out = linear_to_srgb(out)
    res = arr.copy()
    res[..., :3] = out
    return res


def stretch(a, lo_pct=2.0, hi_pct=98.0):
    lo, hi = np.percentile(a, [lo_pct, hi_pct])
    return np.clip((a - lo) / max(hi - lo, 1e-6), 0.0, 1.0)


def derive_normal(height, strength: float):
    """OpenGL tangent-space normal from a height field. np.roll keeps it wrap-safe, so a tileable
    height gives a tileable normal. Rows are bottom-up, so +row is +V (green up)."""
    h, w = height.shape
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    k = strength * min(h, w) / 256.0
    n = np.stack([-dx * k, -dy * k, np.ones_like(height)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def gray4(g):
    return np.stack([g, g, g, np.ones_like(g)], axis=-1).astype(np.float32)


def rgb4(rgb):
    return np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], axis=-1).astype(np.float32)


# ---- modes --------------------------------------------------------------------------------------------------


def run(o: dict) -> tuple[dict, int]:
    mode = o["mode"]
    src = o[mode]
    arr, info = load(src)
    res: dict = {"mode": mode, "image": src, "size": [info["width"], info["height"]],
                 "float": info["float"]}
    code = 0

    if mode in ("seam", "report"):
        res["seam"] = dict(seam_stats(arr), max=o["max_seam"])
        res["seam"]["pass"] = res["seam"]["ratio"] <= o["max_seam"]
        if mode == "report":
            res["lowfreq_std"] = round(lowfreq_spread(arr, is_linear(src, o), o["sigma_frac"]), 4)
            res["mean_luma"] = round(float(np.mean(luma(arr))), 4)
        code = 0 if res["seam"]["pass"] else 1

    elif mode == "tile":
        before = seam_stats(arr)
        out = tile(arr, o["fade"])
        path = save(o["out"], out, o["depth"])
        # re-read so the verdict covers the quantised file, not the float intermediate
        after = seam_stats(load(path)[0])
        res.update(out=path, before=before, seam=dict(after, max=o["max_seam"], **{"pass": after["ratio"] <= o["max_seam"]}))
        res["note"] = "cross-fade softens detail in the blend band; use on organic surfaces, not regular patterns"
        code = 0 if res["seam"]["pass"] else 1

    elif mode == "delight":
        lin = is_linear(src, o)
        before = lowfreq_spread(arr, lin, o["sigma_frac"])
        out = delight(arr, lin, o["sigma_frac"], o["strength"])
        path = save(o["out"], out, o["depth"])
        after = lowfreq_spread(load(path)[0], lin, o["sigma_frac"])
        res.update(out=path, lowfreq_before=round(before, 4), lowfreq_after=round(after, 4),
                   max_lowfreq=o["max_lowfreq"])
        res["pass"] = after <= o["max_lowfreq"]
        code = 0 if res["pass"] else 1

    elif mode == "derive":
        if o.get("height", "luma") != "luma":
            harr, hinfo = load(o["height"])
            if (hinfo["width"], hinfo["height"]) != (info["width"], info["height"]):
                raise ValueError("--height size %dx%d differs from %dx%d" % (
                    hinfo["width"], hinfo["height"], info["width"], info["height"]))
            hsrc = harr[..., 0]
        else:
            hsrc = luma(arr)
        height = blur_wrap(stretch(hsrc, 1.0, 99.0), o["smooth"])
        height = stretch(height, 0.0, 100.0)
        lum = stretch(luma(arr), 2.0, 98.0)
        lo, hi = o["rough_range"]
        rough = hi - lum * (hi - lo)
        stem = o.get("stem") or re.sub(r"[_\-.](albedo|basecolor|base_color|diffuse|diff|col|color)$", "",
                                       os.path.splitext(os.path.basename(src))[0], flags=re.I)
        depth = o["depth"] or 16
        d = o["out-dir"]
        normal = derive_normal(height, o["strength"])
        paths = {
            "normal": save(os.path.join(d, stem + "_normal.png"), rgb4(normal), depth),
            "roughness": save(os.path.join(d, stem + "_roughness.png"), gray4(rough), depth),
            "height": save(os.path.join(d, stem + "_height.png"), gray4(height), depth),
        }
        nback = load(paths["normal"])[0]
        res.update(out_dir=d, maps=paths, normal_convention="opengl", strength=o["strength"],
                   normal_mean=[round(float(v), 3) for v in nback[..., :3].reshape(-1, 3).mean(axis=0)],
                   normal_seam=seam_stats(nback),
                   roughness_range=[round(float(rough.min()), 3), round(float(rough.max()), 3)])
        res["metallic"] = "not derived: use 0, or paint a binary mask; AO comes from bake_maps.py on real geometry"
        code = 0 if res["normal_seam"]["ratio"] <= o["max_seam"] else 1
        if code:
            res["warning"] = "source height does not tile; run --tile first"
    return res, code


def main() -> None:
    o = parse_args()
    try:
        res, code = run(o)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(json.dumps({"ok": False, "mode": o["mode"], "error": str(e)}))
        sys.exit(1)
    res = dict(ok=code == 0, **res)
    print(json.dumps(res))
    sys.exit(code)


if __name__ == "__main__":
    main()
