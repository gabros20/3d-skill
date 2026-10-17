# remotion — "How 3d works" explainer

The explainer for the **3d** skill's site (`site/index.html` → `#idea` player): 1200×520, 30 fps,
8582 frames (286.1 s), loops. Two acts: one 3D task end to end — a reference clip rebuilt as a
model visitors spin on a product page (request → measured refspec → grill → brief and gates →
pipeline → feasibility ceiling → build → previews → fresh critic → the user's note → approved →
`3D.md`), then the pack (router, preflight, stop rules, where outputs land). The scene
timeline is the `SCENES` const in [`src/HowThreeDWorks.tsx`](src/HowThreeDWorks.tsx); the
storyboard with every on-screen fact's source is `.orchestrate/video/storyboard.md`.

Structure follows the prepacked Remotion skills (4.0.536): each scene is an
`Interactive.create()` connected composition placed on one of two alternating `<Track>`s (clips on
one Track may not overlap) and registered standalone under the Studio's **Scenes** folder
(`scene-<id>`, `chapter-rail`). `remotion.config.ts` renders with Chrome for Testing because the
4.0.536 headless shell aborts on macOS 26; drop that line once a later shell launches.

The palette in [`src/theme.ts`](src/theme.ts) mirrors `site/index.html`'s `:root` tokens
exactly, so the video reads as part of the page in both light and dark.

## Commands

```bash
npm i                     # install (node_modules is gitignored)
npm run dev               # Remotion Studio preview
```

Render the two theme variants + poster stills into the site (paths are relative to this dir):

```bash
npx remotion render how-3d-works-light ../site/assets/how-3d-works-light.mp4 --codec=h264 --crf=23
npx remotion render how-3d-works-dark  ../site/assets/how-3d-works-dark.mp4  --codec=h264 --crf=23
npx remotion still  how-3d-works-light ../site/assets/how-3d-works-light-poster.png --frame=3823
npx remotion still  how-3d-works-dark  ../site/assets/how-3d-works-dark-poster.png  --frame=3823
```

The page swaps `how-3d-works-{light,dark}.mp4` on theme change and falls back to the poster PNG
(and to the static diagram) when video or motion is unavailable. The poster is frame 3823, the
preview viewer with the reference overlay — a hold, not frame 0. When `SCENES` changes, update the
page's PLAYER-META (`data-duration`, `data-chapters` = scene start / 30) to match.

If a render dies with `Visited "http://localhost:…" but got no response` (a tab crashed under memory
pressure), re-run it with `--concurrency=2`.

Rendered videos are multi-megabyte binaries. If `git push` fails with HTTP 400, raise the buffer
for that push: `git -c http.postBuffer=524288000 push`.

## Pace every scene for a reader, not the author

The single most common defect in these videos is switching too fast: a scene's text finishes
animating in and the fade-out starts immediately, so a first-time viewer never gets to read it.
Build each scene as three explicit phases:

```text
animate IN  →  HOLD fully still (a reading beat)  →  fade OUT
```

- **Compute the hold; never set it by feel.** This is the canonical rule:

  ```text
  HOLD ≥ 2.0 s settle + W / 3 s + 1.0 s × G
  ```

  - HOLD is the time everything is still, after the last element lands.
  - W counts the new words a viewer should read: headline, key lines and caption. Monospace and code words count × 1.3.
  - G is the number of visual groups to parse (diagram, card, table, chart, viewer).
  - A caption is fully opaque for ≥ 1.0 + words / 3.3 s, and is never cut before its scene's hold ends.
  - `readingLoad()` in `src/HowThreeDWorks.tsx` applies it. Each scene's `DEFS` entry lists exactly the strings it shows, so the code derives `dur = IN + hold + OUT`.
- Too long? Cut words, not seconds: a headline, one caption and 3–5 key lines per scene.
- The fade-out must begin at `dur − fade`, **after** every element has finished appearing. Never let text animate during a hold.
- Verify before a full render: `npx remotion still <id> <out> --frame=N` at the middle of each hold, and confirm the scene is complete and legible.

A dense explainer runs well over a minute once every scene holds long enough to read; a cut that
feels "tight" to its author is almost always too fast for a first-time viewer.

## AI authoring skills (prepacked)

The official Remotion authoring skills ([remotion-dev/skills](https://github.com/remotion-dev/skills))
are prepacked in this repository — tracked under `.agents/skills/` and symlinked from
`.claude/skills/` — so any agent storyboarding or re-authoring the explainer finds them without
installing anything. Refresh them to the latest upstream versions with:

```bash
npx skills add remotion-dev/skills
```

The installer also drops symlinks into the runtime `skills/` directory; those are gitignored and
`scripts/init` removes them — the installable pack must never ship them. When a repository is
initialized without `--video`, `scripts/init` strips the authoring skills along with this project.
