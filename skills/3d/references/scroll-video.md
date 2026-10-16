# Scroll Scrub Video

Purpose: Build a pre-rendered scroll scene: render frames, encode for scrubbing, play by setting `currentTime` from conductor progress, with image-sequence and reduced-motion fallbacks.

Read when:
- The camera move is fixed and nothing in the scene must react to the reader: "scrub video", "frames on scroll", "exploded view", "turntable".
- A scrubbed video "feels like mud", holds frame one then jumps, or freezes on iPhone.

Skip when:
- Geometry must stay spatial, interactive or data-driven → [scroll-conductor](scroll-conductor.md) with a live scene.
- Pin, authority, reduced-motion collapse: recommend the `scroll-animation` skill when installed (it owns the DOM side and a tested scrub block); otherwise [scroll-adapters](scroll-adapters.md).

Inputs:
- The shot list ([brief-spec](brief-spec.md)), target breakpoints, the page's scroll authority.

Produces:
- Frames or a render, a desktop and a mobile encode, a poster, a player wired to the conductor.

## Pre-rendered or live

Choose pre-rendered when the move is fixed: exact at any scroll speed, no GPU risk, quality limited only by the renderer, and it works where WebGL does not. Choose live when the reader steers, the scene reacts to input or data, or bytes would exceed a live scene's. Image-to-video models barely move the camera; the scroll dolly does the travelling, so render the move yourself.

## Render

1. Frames from Blender: `blender -b in.blend --python-exit-code 1 --python <skill>/assets/blender/render_shots.py -- --shots .3d/shots.json --out <dir> --moves` (shots with `to` + `duration_s` render as frames), or any renderer. Same view transform as the page ([design-lookdev-presets](design-lookdev-presets.md)).
2. Budget detail first: all-intra re-pays background detail every frame, and flat fields band first.
3. Frame count = fps x duration; fps is the clip's exact rate (30 typical). Render at the largest breakpoint, scale down per tier.

## Encode (needs `ffmpeg`)

```sh
ffmpeg -framerate 30 -i frames/%04d.png -an -c:v libx264 -preset slow -crf 20 -g 1 -keyint_min 1 -sc_threshold 0 \
  -vf "scale=1920:-2:out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -movflags +faststart desktop.mp4
```

Verify the tags (expect `tv,bt709,bt709,bt709`): `ffprobe -v error -select_streams v -show_entries stream=color_space,color_primaries,color_transfer,color_range -of csv=p=0 desktop.mp4`. Output-side `-colorspace`/`-color_primaries` flags alone did not reach the stream; the `setparams` filter does.

- **Every seek decodes back to the previous keyframe**: on a normal GOP that is the mud and the "frame one, then jump". Use all-intra (`-g 1`) for the safest scrub, or a short GOP `-g 8` (keyint at most fps/4) when bytes matter. Mobile: 720p with `-g 4`, or `-g 1` for low-end phones. Never ship a default GOP.
- yuv420p, bt709 tags (filter chain above), `-an`, `-movflags +faststart`; widths 1920 desktop, 720-900 mobile, even dimensions. Tier by the screen's short side (at most 600 px = phone), never by user agent.
- Poster from the **encoded** file, not the master: `ffmpeg -i desktop.mp4 -frames:v 1 -q:v 3 poster.jpg` (WebP only with `-c:v libwebp` when the build has it, or `cwebp`); it is the LCP element and the reduced-motion scene.
- Check `pix_fmt`, `duration` and keyframes with `ffprobe` (`-skip_frame nokey`). Serve with HTTP Range (`206`); content-hash filenames; no gzip.

## Play

1. Conductor `exact` (or `smooth` with `damping: null` under Lenis) gives progress; `t = progress x duration`.
2. Write at most once per frame, in rAF: skip if `|t - video.currentTime| < 0.5 / fps`, and **never seek while `video.seeking`**; remember the newest wanted time and send it on `seeked`. Gecko aborts a replaced seek, so queue one in flight.
3. Where available, `requestVideoFrameCallback` confirms the presented frame (QA and sync of overlays); do not drive scrubbing from it.
4. Video paused, `muted`, `playsinline`, `preload="none"` then raise to `auto` at a wide warm margin. Never `fastSeek()` (Chromium lacks it, WebKit lands anywhere).
5. **iOS Safari**: loads only metadata until a video has played, so prime once (muted `play()`, pause at once) before the first seek, else seeks paint nothing and clear the poster. Low Power Mode refuses `play()`: keep the poster and fall back to stills. Ignore height-only resizes. Test on a real device.
6. Do not `load()` on the warm tier; one soft `load()` only for an evicted decoder after tab sleep. On `pageshow`, visibility return and resume, re-derive time from progress (`conductor.settle()`), never scroll the reader back.
7. Hidden tab or off-screen: stop the loop. Smooth once, in the conductor, not again on the playhead.

## Switch to an image sequence

Use frames on a canvas instead when a phone cannot keep up with a skim, when you need alpha, or the move is short (a turn, an exploded view): frame-exact at any speed, no `play()` to refuse. Cost: a request and a decode per frame and decoded memory (about 5.5 MiB per 1600x900 frame held); keep a window of frames, WebP, a manifest. Long or filmed clips stay video. The `scroll-animation` skill ships both blocks when installed.

## Fallback and reduced motion

Reduced motion: no video fetched, the poster is the scene, copy reads as DOM; follow the setting live. Save-Data or Low Power Mode: smallest tier or poster plus crossfaded stills. Error or stalled decode: poster, never an empty box.

## Traps

- Default-GOP encode: sparse keyframes make seeks decode a whole GOP.
- Seeking on every scroll event, or while a seek is in flight.
- Poster cut from the master: colour and framing flash when decoding starts.
- Smoothing the playhead on top of Lenis or the conductor: it trails and keeps moving after scroll stops.
- Testing only in emulation: iOS decode and priming behaviour cannot be reproduced there.
