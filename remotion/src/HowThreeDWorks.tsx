import React, { useId } from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  interpolateColors,
  Interactive,
  Track,
  useCurrentFrame,
} from "remotion";
import { MONO, SANS, Theme, ThemeName, themes } from "./theme";

// "How 3d works": the explainer on the site's #idea section. Storyboard and every on-screen
// fact's source: .orchestrate/video/storyboard.md. Two acts, reader-first pacing (README): each
// scene animates IN, HOLDS fully still, then fades OUT over 18 f; scenes overlap by 8 f.
// Each scene is a connected composition (Interactive.create, layout absolute-fill) placed on one
// of two alternating Tracks (clips on one Track may not overlap); SCENES below is the one timeline.

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const io = (f: number, range: number[], out: number[]): number =>
  interpolate(f, range, out, { ...clamp, easing: ease });
// typing is linear: an eased caret reads as stutter
const typed = (f: number, a: number, b: number, s: string): string =>
  s.slice(0, Math.round(interpolate(f, [a, b], [0, s.length], clamp)));

// The reference clip and the dark look are footage/renders, not page chrome: they stay dark in
// both themes. These are the only literal colours in the file.
const REF = {
  bg0: "#0b0e14",
  bg1: "#1a1f2b",
  top: "#232a3a",
  side: "#161b27",
  rim: "#9ec5ff",
  text: "#e6eaf3",
};
const LOOKS = {
  studio: { bg0: "#f7f8fb", bg1: "#dfe3ea", top: "#ffffff", side: "#d6dbe4", rim: "", shadow: 0.14 },
  golden: { bg0: "#3a2614", bg1: "#c08243", top: "#ecd2ad", side: "#a77548", rim: "#ffe0ae", shadow: 0.3 },
};

// ---------- the product: an SVG speaker puck, framed per shots.json shot ----------

type Look = "ref" | "greybox" | "v1" | "v2" | "v3" | "studio" | "night" | "golden";
type Framing = "S01" | "S02" | "S03";

const FRAMES: Record<Framing, { cx: number; cy: number; rx: number; h: number }> = {
  S01: { cx: 160, cy: 86, rx: 48, h: 22 },
  S02: { cx: 150, cy: 118, rx: 150, h: 70 },
  S03: { cx: 178, cy: 84, rx: 70, h: 30 },
};

// v1 is the critic's round-1 defect: in S01 the subject sits on the right edge
export const puckGeometry = (framing: Framing, look: Look) => {
  const g = FRAMES[framing];
  return look === "v1" && framing === "S01" ? { ...g, cx: 268 } : g;
};

const Puck: React.FC<{
  t: Theme;
  look: Look;
  framing: Framing;
  w: number;
  h: number;
  bg?: boolean;
  style?: React.CSSProperties;
}> = ({ t, look, framing, w, h, bg = true, style }) => {
  const uid = useId().replace(/:/g, "");
  const { cx, cy, rx, h: sh } = puckGeometry(framing, look);
  const ry = rx * 0.34;
  const grey = look === "greybox";
  const pal =
    look === "studio"
      ? LOOKS.studio
      : look === "golden"
        ? LOOKS.golden
        : grey
          ? { bg0: t.codeBg, bg1: t.wire, top: t.panel, side: t.line, rim: "", shadow: 0.18 }
          : { bg0: REF.bg0, bg1: REF.bg1, top: REF.top, side: REF.side, rim: REF.rim, shadow: 0.45 };
  const rimW = look === "v1" || look === "v2" ? 1.2 : 2.6;
  const glow = look === "ref" || look === "v3" || look === "night" || look === "golden";
  const arc = `M ${cx - rx} ${cy} A ${rx} ${ry} 0 0 1 ${cx + rx} ${cy}`;
  return (
    <svg width={w} height={h} viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice" style={{ display: "block", ...style }}>
      <defs>
        <radialGradient id={`bg${uid}`} cx="0.6" cy="0.3" r="0.9">
          <stop offset="0" stopColor={pal.bg1} />
          <stop offset="1" stopColor={pal.bg0} />
        </radialGradient>
        <filter id={`gl${uid}`} x="-20%" y="-50%" width="140%" height="200%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
        <filter id={`sh${uid}`} x="-20%" y="-100%" width="140%" height="300%">
          <feGaussianBlur stdDeviation="5" />
        </filter>
      </defs>
      {bg ? <rect width="320" height="180" fill={`url(#bg${uid})`} /> : null}
      <ellipse cx={cx} cy={cy + sh + ry * 0.3} rx={rx * 1.08} ry={ry * 0.6} fill="#000" opacity={pal.shadow} filter={`url(#sh${uid})`} />
      <path
        d={`M ${cx - rx} ${cy} L ${cx - rx} ${cy + sh} A ${rx} ${ry} 0 0 0 ${cx + rx} ${cy + sh} L ${cx + rx} ${cy} Z`}
        fill={pal.side}
        stroke={grey ? t.glyph : "none"}
        strokeWidth={1.4}
      />
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill={pal.top} stroke={grey ? t.glyph : "none"} strokeWidth={1.4} />
      {!grey && look !== "studio" ? (
        <line x1={cx - rx * 0.45} y1={cy + ry * 0.9} x2={cx - rx * 0.45} y2={cy + sh + ry * 0.85} stroke="#fff" strokeOpacity={0.12} strokeWidth={rx * 0.06} />
      ) : null}
      {pal.rim && glow ? <path d={arc} fill="none" stroke={pal.rim} strokeWidth={rimW * 3} opacity={0.45} filter={`url(#gl${uid})`} /> : null}
      {pal.rim ? <path d={arc} fill="none" stroke={pal.rim} strokeWidth={rimW} strokeLinecap="round" /> : null}
    </svg>
  );
};

// ---------- shared primitives ----------

const mono = (size: number, color: string, extra?: React.CSSProperties): React.CSSProperties => ({
  fontFamily: MONO,
  fontSize: size,
  color,
  whiteSpace: "pre",
  ...extra,
});
const sans = (size: number, color: string, extra?: React.CSSProperties): React.CSSProperties => ({
  fontFamily: SANS,
  fontSize: size,
  color,
  ...extra,
});
const kicker = (t: Theme, color?: string): React.CSSProperties => ({
  fontFamily: SANS,
  fontSize: 15,
  fontWeight: 600,
  letterSpacing: "0.12em",
  textTransform: "uppercase",
  color: color ?? t.muted,
});

const Box: React.FC<{
  t: Theme;
  x: number;
  y: number;
  w: number;
  h?: number;
  code?: boolean;
  dashed?: boolean;
  border?: string;
  opacity?: number;
  pad?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ t, x, y, w, h, code, dashed, border, opacity = 1, pad = "12px 16px", style, children }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      height: h,
      boxSizing: "border-box",
      opacity,
      background: code ? t.codeBg : t.panel,
      border: `1.5px ${dashed ? "dashed" : "solid"} ${border ?? t.line}`,
      borderRadius: 12,
      padding: pad,
      overflow: "hidden",
      ...style,
    }}
  >
    {children}
  </div>
);

const At: React.FC<{ x: number; y: number; o?: number; dx?: number; dy?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({
  x,
  y,
  o = 1,
  dx = 0,
  dy = 0,
  style,
  children,
}) => (
  <div style={{ position: "absolute", left: x, top: y, opacity: o, translate: `${dx}px ${dy}px`, ...style }}>{children}</div>
);

type TagKind = "measured" | "read" | "inferred" | "assumed" | "unknown";
const tagColour = (t: Theme, k: TagKind) =>
  k === "measured" ? t.good : k === "read" ? t.accent : k === "inferred" ? t.amber : k === "assumed" ? t.dim : t.muted;
const Tag: React.FC<{ t: Theme; k: TagKind; label?: string }> = ({ t, k, label }) => (
  <span
    style={{
      fontFamily: MONO,
      fontSize: 15,
      color: tagColour(t, k),
      border: `1.2px solid ${tagColour(t, k)}`,
      borderRadius: 999,
      padding: "1px 8px",
      whiteSpace: "nowrap",
    }}
  >
    {label ?? k}
  </span>
);

const Chip: React.FC<{ t: Theme; children: React.ReactNode; color?: string; fill?: boolean; dashed?: boolean; size?: number; style?: React.CSSProperties }> = ({
  t,
  children,
  color,
  fill,
  dashed,
  size = 14,
  style,
}) => (
  <span
    style={{
      display: "inline-block",
      fontFamily: MONO,
      fontSize: size,
      color: color ?? t.ink,
      background: fill ? t.codeBg : t.panel,
      border: `1.5px ${dashed ? "dashed" : "solid"} ${color ?? t.line}`,
      borderRadius: 8,
      padding: "4px 10px",
      whiteSpace: "nowrap",
      ...style,
    }}
  >
    {children}
  </span>
);

const Stamp: React.FC<{ f: number; at: number; color: string; children: React.ReactNode; size?: number }> = ({ f, at, color, children, size = 15 }) => {
  const o = io(f, [at, at + 8], [0, 1]);
  return (
    <span
      style={{
        display: "inline-block",
        opacity: o,
        scale: String(io(f, [at, at + 12], [1.5, 1])),
        fontFamily: MONO,
        fontSize: size,
        fontWeight: 600,
        color,
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  );
};

// terminal line: `$ cmd` typed, output appears whole
const Cmd: React.FC<{ t: Theme; f: number; a: number; b: number; cmd: string; size?: number }> = ({ t, f, a, b, cmd, size = 15 }) => {
  const s = typed(f, a, b, cmd);
  if (f < a) return <div style={{ height: size * 1.5 }} />;
  return (
    <div style={mono(size, t.ink, { lineHeight: 1.5 })}>
      <span style={{ color: t.muted }}>$ </span>
      {s}
    </div>
  );
};
const Out: React.FC<{ t: Theme; f: number; at: number; color?: string; size?: number; children: React.ReactNode }> = ({ t, f, at, color, size = 15, children }) => (
  <div style={mono(size, color ?? t.muted, { lineHeight: 1.5, opacity: io(f, [at, at + 6], [0, 1]) })}>{children}</div>
);


const PALETTE: [string, number][] = [
  ["#0d1117", 0.41],
  ["#1a2030", 0.22],
  ["#2b3448", 0.14],
  ["#9ec5ff", 0.09],
  ["#5d6b85", 0.08],
  ["#e6eefc", 0.06],
];
const HIST = [0.16, 0.24, 0.19, 0.12, 0.08, 0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.012, 0.01, 0.012, 0.018, 0.01];
const SPEED = Array.from({ length: 48 }, (_, i) => 3.8 + Math.sin(i * 0.55) * 0.9 + Math.sin(i * 1.7) * 0.35 - (i > 15 && i < 19 ? 2.6 : 0) - (i > 34 && i < 37 ? 2.4 : 0));

// the docked measurement graphic: the card's picture without its numbers
const MiniViz: React.FC<{ t: Theme; i: number }> = ({ t, i }) => {
  if (i === 0)
    return (
      <div style={{ display: "flex", gap: 3 }}>
        {PALETTE.map(([hex]) => (
          <div key={hex} style={{ width: 16, height: 22, borderRadius: 3, background: hex, border: `1px solid ${t.line}` }} />
        ))}
      </div>
    );
  if (i === 1)
    return (
      <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 28, width: 110 }}>
        {HIST.map((v, k) => (
          <div key={k} style={{ flex: 1, height: `${(v / 0.24) * 100}%`, background: t.glyph }} />
        ))}
      </div>
    );
  if (i === 2)
    return (
      <svg width={110} height={28}>
        <line x1={0} y1={14} x2={110} y2={14} stroke={t.line} strokeWidth={2} />
        {[2.1, 4.4].map((sec) => (
          <line key={sec} x1={(sec / 6) * 110} y1={4} x2={(sec / 6) * 110} y2={24} stroke={t.ink} strokeWidth={2.5} />
        ))}
      </svg>
    );
  const pts = SPEED.map((v, k) => `${(k / 47) * 110},${26 - (v / 6) * 24}`).join(" ");
  return (
    <svg width={110} height={28}>
      <polyline points={pts} fill="none" stroke={t.accent} strokeWidth={1.6} />
    </svg>
  );
};

// caption text marks emphasis with **…**
const Caption: React.FC<{ t: Theme; a: number; b: number; text: string }> = ({ t, a, b, text }) => {
  const f = useCurrentFrame();
  const o = io(f, [a, a + 12], [0, 1]) * io(f, [b - 10, b], [1, 0]);
  if (o <= 0.01) return null;
  return (
    <div style={{ position: "absolute", left: 40, right: 40, bottom: 18, textAlign: "center", ...sans(21, t.muted), opacity: o }}>
      {text.split("**").map((part, i) =>
        i % 2 ? (
          <b key={i} style={{ color: t.ink }}>
            {part}
          </b>
        ) : (
          <React.Fragment key={i}>{part}</React.Fragment>
        ),
      )}
    </div>
  );
};

// fade in 16 f, hold, fade out; the caption stays up until the scene leaves
const Shell: React.FC<{ t: Theme; dur: number; title: string; caption: string; out: number; children: React.ReactNode }> = ({
  t,
  dur,
  title,
  caption,
  out,
  children,
}) => {
  const f = useCurrentFrame();
  const o = io(f, [0, 16], [0, 1]) * io(f, [dur - out, dur], [1, 0]);
  if (o <= 0.005) return null;
  return (
    <AbsoluteFill style={{ opacity: o, background: t.bg }}>
      {title ? (
        <div style={{ position: "absolute", top: 46, left: 0, right: 0, textAlign: "center", ...mono(24, t.ink, { letterSpacing: "-0.01em" }) }}>{title}</div>
      ) : null}
      {children}
      {caption ? <Caption t={t} a={12} b={dur - 2} text={caption} /> : null}
    </AbsoluteFill>
  );
};

type Inner = React.FC<{ t: Theme }>;


// Each scene shows a headline, one caption and 3–5 key lines. Every string a viewer is meant to
// read is also listed in the scene's `mono`/`sans` arrays (DEFS), which set its hold.

// ---------- S01 request ----------

const PROMPT = "/3d make our homepage hero feel like this — scroll-driven";

const Request: Inner = ({ t }) => {
  const f = useCurrentFrame();
  return (
    <>
      <Box t={t} x={64} y={200} w={560} pad="18px 22px" style={{ borderRadius: 14, scale: String(io(f, [0, 14], [0.96, 1])) }}>
        <div style={mono(19, t.ink, { whiteSpace: "pre-wrap", minHeight: 58 })}>{typed(f, 4, 30, PROMPT)}</div>
        <div style={{ marginTop: 12, opacity: io(f, [24, 32], [0, 1]) }}>
          <Chip t={t} fill size={15}>
            <span style={{ color: t.amber }}>▤ </span>ref.mp4
          </Chip>
        </div>
      </Box>
      <At x={656} y={112} o={io(f, [14, 30], [0, 1])} dx={io(f, [14, 36], [24, 0])}>
        <div style={{ width: 480, height: 270, borderRadius: 12, overflow: "hidden", position: "relative", border: `1.5px solid ${t.line}` }}>
          <Puck t={t} look="ref" framing="S03" w={480} h={270} />
          <div style={{ position: "absolute", left: 12, right: 12, bottom: 10, height: 3, borderRadius: 2, background: "rgba(255,255,255,.18)" }}>
            <div style={{ width: "40%", height: "100%", borderRadius: 2, background: REF.text }} />
          </div>
        </div>
      </At>
    </>
  );
};

// ---------- S02 measure ----------

const MEASURE_FILES = ["palette.json", "luma.json", "cuts.json", "motion.json"];
const SPEC_ROWS: [string, string, TagKind, string][] = [
  ["palette[0]", "#0d1117", "measured", "measured"],
  ["focal_mm_ff", "[70, 135]", "inferred", "low · inferred"],
];

const Measure: Inner = ({ t }) => {
  const f = useCurrentFrame();
  return (
    <>
      <At x={64} y={100}>
        <Cmd t={t} f={f} a={6} b={14} cmd="ref-extract ref.mp4" size={17} />
      </At>
      {MEASURE_FILES.map((name, i) => (
        <Box key={name} t={t} x={64} y={146 + i * 64} w={300} h={54} pad="0 12px" opacity={io(f, [16 + i * 5, 26 + i * 5], [0, 1])}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: "100%" }}>
            <span style={mono(15, t.ink)}>{name}</span>
            <MiniViz t={t} i={i} />
          </div>
        </Box>
      ))}
      <Box t={t} x={404} y={146} w={732} h={180} code pad="18px 24px" opacity={io(f, [38, 48], [0, 1])}>
        <div style={{ ...mono(16, t.ink), marginBottom: 14 }}>
          <span style={{ color: t.amber }}>▤ </span>.3d/reference-spec.json
        </div>
        {SPEC_ROWS.map(([field, value, k, label], r) => (
          <div key={field} style={{ display: "flex", alignItems: "center", height: 44, opacity: io(f, [44 + r * 6, 52 + r * 6], [0, 1]) }}>
            <span style={mono(18, t.ink, { width: 200 })}>{field}</span>
            <span style={mono(18, t.ink, { flex: 1 })}>{value}</span>
            <Tag t={t} k={k} label={label} />
          </div>
        ))}
      </Box>
    </>
  );
};

// ---------- S03 grill ----------

const QS: [string, string][] = [
  ["Pinned in the hero, scrubbed by scroll?", "yes · SCROLL"],
  ["The look is open: A, B or C?", "B"],
];
const DIRS: [string, Look][] = [
  ["A", "studio"],
  ["B", "night"],
  ["C", "golden"],
];

const Grill: Inner = ({ t }) => {
  const f = useCurrentFrame();
  return (
    <>
      <Box t={t} x={64} y={96} w={1072} h={128} pad="16px 24px" opacity={io(f, [6, 16], [0, 1])}>
        <div style={{ ...kicker(t), marginBottom: 12 }}>Round 1</div>
        <div style={{ display: "flex", gap: 40 }}>
          {QS.map(([q, a], i) => {
            const at = 12 + i * 14;
            return (
              <div key={q} style={{ flex: 1, opacity: io(f, [at, at + 10], [0, 1]), translate: `0px ${io(f, [at, at + 10], [6, 0])}px` }}>
                <div style={sans(19, t.ink)}>{q}</div>
                <div style={mono(17, t.accent, { marginTop: 6 })}>→ {a}</div>
              </div>
            );
          })}
        </div>
      </Box>
      {DIRS.map(([label, look], i) => {
        const at = 40 + i * 6;
        const chosen = look === "night";
        return (
          <At key={label} x={64 + i * 364} y={244} o={io(f, [at, at + 10], [0, 1])}>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 12 }}>
              <div style={{ borderRadius: 10, overflow: "hidden", border: `2.5px solid ${chosen ? t.accent : t.glyph}` }}>
                <Puck t={t} look={look} framing="S03" w={300} h={169} />
              </div>
              <span style={mono(24, chosen ? t.accent : t.muted, { fontWeight: 700 })}>{label}</span>
            </div>
          </At>
        );
      })}
    </>
  );
};

// ---------- S04 brief ----------

const GATES = ["Brief", "Style frames", "Blockout", "Lookdev", "Final"];

const Brief: Inner = ({ t }) => {
  const f = useCurrentFrame();
  return (
    <>
      <Box t={t} x={64} y={96} w={560} h={220} opacity={io(f, [6, 18], [0, 1])}>
        <div style={{ display: "flex", gap: 16, marginTop: 8 }}>
          {(["S01", "S02", "S03"] as Framing[]).map((id) => (
            <div key={id}>
              <div style={{ border: `1.5px solid ${t.glyph}`, borderRadius: 6, overflow: "hidden" }}>
                <Puck t={t} look="greybox" framing={id} w={160} h={90} />
              </div>
              <div style={mono(15, t.muted, { marginTop: 8 })}>{id}</div>
            </div>
          ))}
        </div>
        <div style={{ ...mono(16, t.ink), marginTop: 20 }}>
          <span style={{ color: t.amber }}>▤ </span>.3d/shots.json <span style={{ color: t.muted }}>shots.v1</span>
        </div>
      </Box>
      <div style={{ position: "absolute", left: 140, right: 140, top: 381, height: 2, background: t.line, opacity: io(f, [20, 44], [0, 1]) }} />
      {GATES.map((g, i) => {
        const at = 20 + i * 5;
        const done = i === 0;
        return (
          <At key={g} x={120 + i * 230} y={368} o={io(f, [at, at + 8], [0, 1])}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, background: t.bg, paddingRight: 8 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 14,
                  display: "grid",
                  placeItems: "center",
                  border: `2px solid ${done ? interpolateColors(io(f, [46, 58], [0, 1]), [0, 1], [t.line, t.good]) : t.line}`,
                  background: t.panel,
                  ...mono(15, t.ink),
                }}
              >
                {done && f >= 46 ? (
                  <Stamp f={f} at={46} color={t.good} size={15}>
                    ✓
                  </Stamp>
                ) : (
                  i + 1
                )}
              </div>
              <span style={sans(16, t.ink)}>{g}</span>
            </div>
          </At>
        );
      })}
    </>
  );
};

// ---------- S05 approach ----------

const MATRIX: [string, string][] = [
  ["HERO", "live three.js or R3F"],
  ["SCROLL", "live scene on scroll"],
  ["SCRUB", "pre-rendered · scroll-video.md"],
];
const LADDER = ["live", "reduced", "poster + video", "static"];

const Approach: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const hl = io(f, [26, 36], [0, 1]);
  return (
    <>
      <Box t={t} x={64} y={100} w={652} h={200} pad="20px 24px" opacity={io(f, [4, 14], [0, 1])}>
        {MATRIX.map(([use, strat], i) => {
          const me = i === 1;
          return (
            <div
              key={use}
              style={{
                opacity: io(f, [8 + i * 6, 16 + i * 6], [0, 1]),
                borderLeft: `3px solid ${me ? interpolateColors(hl, [0, 1], [t.panel, t.accent]) : t.panel}`,
                paddingLeft: 12,
                marginLeft: -15,
                height: 52,
                display: "flex",
                alignItems: "center",
              }}
            >
              <span style={mono(18, me ? t.ink : t.muted, { width: 130, fontWeight: me ? 600 : 400 })}>{use}</span>
              <span style={sans(18, me ? t.ink : t.muted)}>{strat}</span>
            </div>
          );
        })}
      </Box>
      <At x={64} y={330} o={io(f, [38, 48], [0, 1])}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ ...kicker(t), marginRight: 6 }}>fallback</span>
          {LADDER.map((r, i) => (
            <React.Fragment key={r}>
              {i ? <span style={mono(16, t.glyph)}>→</span> : null}
              <Chip t={t} fill size={15}>
                {r}
              </Chip>
            </React.Fragment>
          ))}
        </div>
      </At>
    </>
  );
};

// ---------- S06 build ----------

const CHAIN = ["master", "dedup", "weld", "prune", "meshopt"];

const Build: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const row = (y: number, at: number, label: string, children: React.ReactNode) => (
    <At x={64} y={y} o={io(f, [at, at + 10], [0, 1])}>
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <span style={{ ...kicker(t), width: 120 }}>{label}</span>
        {children}
      </div>
    </At>
  );
  return (
    <>
      {row(
        112,
        6,
        "Blender",
        <Chip t={t} color={t.accent} size={16}>
          headless CLI
        </Chip>,
      )}
      {row(
        196,
        18,
        "GLB",
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {CHAIN.map((c, i) => (
            <React.Fragment key={c}>
              {i ? <span style={mono(16, t.glyph)}>→</span> : null}
              <Chip t={t} fill size={15}>
                {c}
              </Chip>
            </React.Fragment>
          ))}
          <span style={{ marginLeft: 16, display: "inline-flex", alignItems: "center", gap: 8 }}>
            <Chip t={t} color={t.bad} size={15} style={{ textDecoration: "line-through" }}>
              optimize
            </Chip>
          </span>
        </div>,
      )}
      {row(
        280,
        34,
        "budget",
        <span style={mono(17, t.ink)}>
          glb-report <span style={{ color: t.good, fontWeight: 600 }}>PASS</span>
        </span>,
      )}
      {row(
        364,
        46,
        "live scene",
        <Chip t={t} fill size={15}>
          <span style={{ color: t.amber }}>▤ </span>SceneCanvas.tsx
        </Chip>,
      )}
    </>
  );
};

// ---------- viewer mock (S07, S09) ----------

const CANVAS_DARK = `radial-gradient(ellipse at 60% 30%, ${REF.bg1} 0%, ${REF.bg0} 75%)`;

const ShotTabs: React.FC<{ t: Theme; active: number }> = ({ t, active }) => (
  <div style={{ display: "flex", gap: 6 }}>
    {["S01", "S02", "S03"].map((s, i) => (
      <Chip key={s} t={t} size={15} color={i === active ? t.accent : undefined} style={{ padding: "1px 9px", background: i === active ? t.codeBg : t.panel }}>
        {s}
      </Chip>
    ))}
  </div>
);

// ---------- S07 preview ----------

const Preview: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const shotO = (i: number) => (i === 0 ? io(f, [30, 40], [1, 0]) : i === 1 ? io(f, [30, 40], [0, 1]) * io(f, [42, 52], [1, 0]) : io(f, [42, 52], [0, 1]));
  const active = f < 35 ? 0 : f < 47 ? 1 : 2;
  const overlay = io(f, [58, 72], [0, 0.5]);
  const cw = 760;
  const ch = 300;
  const pw = Math.round((ch * 16) / 9);
  return (
    <>
      <Box t={t} x={64} y={96} w={1072} h={346} pad="0" opacity={io(f, [4, 18], [0, 1])}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, height: 44, padding: "0 14px", borderBottom: `1.5px solid ${t.line}` }}>
          <span style={mono(15, t.ink, { fontWeight: 600 })}>v001</span>
          <ShotTabs t={t} active={active} />
        </div>
        <div style={{ position: "absolute", left: 0, top: 44, width: cw, height: ch, background: CANVAS_DARK, overflow: "hidden" }}>
          {(["S01", "S02", "S03"] as Framing[]).map((s, i) => (
            <div key={s} style={{ position: "absolute", left: (cw - pw) / 2, top: 0, opacity: shotO(i) }}>
              <Puck t={t} look="v1" framing={s} w={pw} h={ch} bg={false} />
            </div>
          ))}
          <div style={{ position: "absolute", left: (cw - pw) / 2, top: 0, opacity: overlay }}>
            <Puck t={t} look="ref" framing="S03" w={pw} h={ch} bg={false} />
          </div>
        </div>
        <div style={{ position: "absolute", left: cw + 22, top: 80, width: 1072 - cw - 44 }}>
          <div style={mono(16, t.ink)}>reference overlay</div>
          <div style={{ marginTop: 14, height: 8, borderRadius: 4, background: t.codeBg, border: `1px solid ${t.line}` }}>
            <div style={{ width: `${overlay * 100}%`, height: "100%", borderRadius: 4, background: t.accent }} />
          </div>
          <div style={mono(15, t.muted, { marginTop: 8 })}>{Math.round(overlay * 100)}%</div>
        </div>
      </Box>
    </>
  );
};

// ---------- S08 critic (round 1 fails, the fix is a new version, round 2 passes) ----------

const SCORES: [string, number, number][] = [
  ["composition", 1, 3],
  ["lighting", 2, 2],
  ["materials", 2, 2],
  ["colour", 3, 3],
  ["motion", 2, 2],
  ["performance", 2, 2],
  ["fidelity", 3, 3],
];

const Critic: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const fixed = io(f, [112, 126], [0, 1]);
  const r2 = io(f, [126, 136], [0, 1]);
  return (
    <>
      <At x={64} y={110} o={io(f, [6, 18], [0, 1])}>
        <div style={{ display: "flex", gap: 10 }}>
          {(["S01", "S02", "S03"] as Framing[]).map((s) => {
            const bad = s === "S01";
            return (
              <div
                key={s}
                style={{
                  borderRadius: 6,
                  overflow: "hidden",
                  border: `2px solid ${bad ? interpolateColors(io(f, [70, 78], [0, 1]) * (1 - fixed), [0, 1], [t.line, t.bad]) : t.line}`,
                  position: "relative",
                  width: 120,
                  height: 68,
                }}
              >
                <Puck t={t} look="v1" framing={s} w={116} h={65} style={{ position: "absolute", opacity: 1 - fixed }} />
                <Puck t={t} look="v2" framing={s} w={116} h={65} style={{ position: "absolute", opacity: fixed }} />
              </div>
            );
          })}
        </div>
      </At>
      <Box t={t} x={64} y={210} w={386} h={110} border={t.accent} opacity={io(f, [16, 30], [0, 1])}>
        <div style={mono(21, t.accent, { fontWeight: 600 })}>fresh critic</div>
        <div style={{ ...sans(17, t.ink), marginTop: 10 }}>never told what was fixed</div>
      </Box>
      <Box t={t} x={500} y={96} w={636} h={300} pad="12px 22px" opacity={io(f, [24, 32], [0, 1])}>
        <div style={{ ...mono(15, t.muted), marginBottom: 6 }}>{f < 120 ? "v001" : "v002"}</div>
        {SCORES.map(([label, s1, s2], i) => {
          const at = 30 + i * 4;
          const score = s1 + (s2 - s1) * r2;
          const flagged = s1 < 2 && r2 < 0.5;
          return (
            <div key={label} style={{ display: "flex", alignItems: "center", height: 33, opacity: io(f, [at, at + 8], [0, 1]) }}>
              <span style={sans(16, flagged && f >= 70 ? t.bad : t.ink, { width: 150 })}>{label}</span>
              {[0, 1, 2].map((d) => (
                <div
                  key={d}
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: 7,
                    marginRight: 6,
                    border: `1.5px solid ${flagged ? t.bad : t.glyph}`,
                    background: interpolateColors(Math.max(0, Math.min(1, score - d)), [0, 1], [t.panel, flagged ? t.bad : t.accent]),
                  }}
                />
              ))}
            </div>
          );
        })}
        <div style={{ position: "absolute", left: 330, top: 120, ...mono(18, t.bad, { fontWeight: 600 }), opacity: io(f, [70, 80], [0, 1]) * (1 - io(f, [120, 126], [0, 1])) }}>v001 · fail</div>
        <div style={{ position: "absolute", left: 330, top: 120, ...mono(18, t.good, { fontWeight: 600 }), opacity: io(f, [140, 150], [0, 1]) }}>v002 · pass</div>
      </Box>
    </>
  );
};

// ---------- S09 approve (the user's note becomes v003) ----------

const NOTE = "rim too thin — match the clip";

const Approve: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const cw = 760;
  const ch = 260;
  const pw = Math.round((ch * 16) / 9);
  const left = (cw - pw) / 2;
  const g = puckGeometry("S01", "v2");
  const px = left + ((g.cx + g.rx * 0.6) / 320) * pw;
  const py = ((g.cy - g.rx * 0.34 * 0.8) / 180) * ch;
  const split = f >= 70;
  const wipe = io(f, [70, 96], [0.2, 0.5]);
  return (
    <>
      <Box t={t} x={64} y={96} w={cw} h={ch} pad="0" style={{ background: CANVAS_DARK }}>
        <div style={{ position: "absolute", left, top: 0 }}>
          <Puck t={t} look="v2" framing="S01" w={pw} h={ch} bg={false} />
        </div>
        {split ? (
          <div style={{ position: "absolute", inset: 0, clipPath: `inset(0 0 0 ${wipe * 100}%)`, opacity: io(f, [70, 76], [0, 1]) }}>
            <div style={{ position: "absolute", left, top: 0 }}>
              <Puck t={t} look="v3" framing="S01" w={pw} h={ch} bg={false} />
            </div>
          </div>
        ) : null}
        {split ? <div style={{ position: "absolute", top: 0, bottom: 0, left: wipe * cw - 1, width: 2, background: t.accent, opacity: io(f, [70, 76], [0, 1]) }} /> : null}
        {split ? (
          <>
            <span style={{ position: "absolute", left: 14, bottom: 10, ...mono(15, REF.text) }}>v002</span>
            <span style={{ position: "absolute", right: 14, bottom: 10, ...mono(15, REF.text) }}>v003</span>
          </>
        ) : null}
        <div
          style={{
            position: "absolute",
            left: px - 12,
            top: py - 12,
            width: 24,
            height: 24,
            borderRadius: 12,
            display: "grid",
            placeItems: "center",
            background: t.accent,
            ...mono(15, t.accentInk, { fontWeight: 700 }),
            opacity: io(f, [6, 12], [0, 1]) * (1 - io(f, [66, 72], [0, 1])),
            scale: String(io(f, [6, 16], [1.4, 1])),
            border: "2px solid rgba(0,0,0,.4)",
          }}
        >
          1
        </div>
        {f >= 104 ? (
          <div style={{ position: "absolute", right: 18, top: 16 }}>
            <Stamp f={f} at={104} color={t.good} size={20}>
              approved
            </Stamp>
          </div>
        ) : null}
      </Box>
      <At x={64} y={376} o={io(f, [14, 20], [0, 1])}>
        <span style={mono(17, t.ink)}>
          <span style={{ color: t.accent }}>note 1 </span>
          {typed(f, 14, 34, NOTE)}
        </span>
      </At>
      <Box t={t} x={850} y={96} w={286} h={260} code pad="16px 20px" opacity={io(f, [70, 84], [0, 1])}>
        <div style={mono(17, t.ink)}>v003 vs v002</div>
        <div style={mono(17, t.ink, { marginTop: 14 })}>ssim 0.95</div>
        <div style={sans(16, t.muted, { marginTop: 6 })}>a visible, local change</div>
      </Box>
    </>
  );
};

// ---------- S10 record ----------

const LOG: [string, string, string][] = [
  ["v001", "critic fail", "changes"],
  ["v002", "critic pass · note 1", "changes"],
  ["v003", "critic pass", "approved"],
];

const Record: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const row = (i: number) => io(f, [16 + i * 7, 24 + i * 7], [0, 1]);
  return (
    <Box t={t} x={200} y={96} w={800} h={300} pad="20px 30px" opacity={io(f, [6, 18], [0, 1])}>
      <div style={mono(22, t.ink, { marginBottom: 14 })}>
        <span style={{ color: t.amber, fontSize: 18 }}>▤ </span>3D.md
      </div>
      <div style={{ ...mono(17, t.ink), opacity: row(0), height: 34 }}>pipeline: SCROLL world</div>
      <div style={{ ...mono(17, t.ink), opacity: row(1), height: 34 }}>
        budget: <span style={{ color: t.good }}>PASS</span> <span style={{ color: t.muted }}>84,210 tris · 1.90 MB</span>
      </div>
      <div style={{ height: 10 }} />
      {LOG.map(([v, what, st], i) => (
        <div key={v} style={{ display: "flex", opacity: row(2 + i), height: 32, alignItems: "center" }}>
          <span style={mono(17, t.ink, { width: 80 })}>{v}</span>
          <span style={mono(17, what.includes("fail") ? t.bad : t.ink, { flex: 1 })}>{what}</span>
          <span style={mono(17, st === "approved" ? t.good : t.amber)}>{st}</span>
        </div>
      ))}
    </Box>
  );
};

// ---------- S11 router ----------

const LANES = ["debug", "one change", "new piece", "Blender", "review"];
const GROUPS: [string, number][] = [
  ["front door", 7],
  ["shared", 5],
  ["three.js", 8],
  ["scroll + assets", 7],
  ["Blender", 5],
  ["optional", 4],
];
// where the debug lane's three files sit in the grid: [group, index]
const ROUTED: [number, number][] = [
  [1, 1],
  [2, 0],
  [1, 4],
];

const Router: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const lane = io(f, [50, 60], [0, 1]);
  return (
    <>
      {LANES.map((l, i) => {
        const me = i === 0;
        return (
          <Box
            key={l}
            t={t}
            x={64}
            y={100 + i * 52}
            w={220}
            h={42}
            pad="8px 14px"
            border={me ? interpolateColors(lane, [0, 1], [t.line, t.accent]) : t.line}
            opacity={io(f, [4 + i * 3, 12 + i * 3], [0, 1])}
          >
            <span style={mono(16, me ? interpolateColors(lane, [0, 1], [t.ink, t.accent]) : t.ink, { fontWeight: me && lane > 0.5 ? 600 : 400 })}>{l}</span>
          </Box>
        );
      })}
      {GROUPS.map(([name, n], g) => (
        <Box key={name} t={t} x={320 + (g % 3) * 276} y={100 + Math.floor(g / 3) * 150} w={262} h={136} pad="12px 14px" opacity={io(f, [20 + g * 4, 30 + g * 4], [0, 1])}>
          <div style={{ ...mono(15, t.muted), marginBottom: 10 }}>{name}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {Array.from({ length: n }, (_, k) => {
              const r = ROUTED.findIndex(([gg, kk]) => gg === g && kk === k);
              const lit = r >= 0 ? io(f, [56 + r * 6, 64 + r * 6], [0, 1]) : 0;
              return (
                <div
                  key={k}
                  style={{
                    width: 46,
                    height: 20,
                    borderRadius: 5,
                    border: `1.5px solid ${interpolateColors(lit, [0, 1], [t.line, t.accent])}`,
                    background: interpolateColors(lit, [0, 1], [t.codeBg, t.accent]),
                  }}
                />
              );
            })}
          </div>
        </Box>
      ))}
      <At x={64} y={378} o={io(f, [74, 82], [0, 1])}>
        <span style={mono(20, t.accent, { fontWeight: 600 })}>3 of 36 loaded</span>
      </At>
    </>
  );
};

// ---------- S12 preflight ----------

const SCRIPTS = "capabilities · ref-extract · spec-check · glb-report · preview";

const Preflight: Inner = ({ t }) => {
  const f = useCurrentFrame();
  return (
    <>
      <At x={64} y={104}>
        <div style={{ display: "flex", gap: 18, alignItems: "baseline" }}>
          <Cmd t={t} f={f} a={6} b={14} cmd="capabilities" size={17} />
          <Out t={t} f={f} at={16} size={17} color={t.amber}>
            ktx missing
          </Out>
        </div>
      </At>
      <Box t={t} x={64} y={160} w={720} h={76} pad="20px 24px" opacity={io(f, [22, 34], [0, 1])}>
        <div style={mono(18, t.ink)}>
          install ktx? <span style={{ color: t.good }}>(free)</span>
        </div>
      </Box>
      <At x={64} y={262} o={io(f, [38, 46], [0, 1])}>
        <span style={{ ...mono(17, t.amber, { fontWeight: 600 }), border: `1.5px solid ${t.amber}`, borderRadius: 999, padding: "6px 18px" }}>nothing installed without your yes</span>
      </At>
      <At x={64} y={340} o={io(f, [50, 58], [0, 1])}>
        <div style={kicker(t)}>the pack&apos;s scripts</div>
        <div style={mono(17, t.ink, { marginTop: 8 })}>{SCRIPTS}</div>
      </At>
    </>
  );
};

// ---------- S13 scroll ----------

const FLOW = ["scroll", "adapter", "conductor", "scene"];

const Scroll: Inner = ({ t }) => {
  const f = useCurrentFrame();
  const barX = 140;
  const barW = 920;
  return (
    <>
      <At x={0} y={112} style={{ width: 1200 }}>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 14 }}>
          {FLOW.map((n, i) => (
            <React.Fragment key={n}>
              {i ? <span style={{ ...mono(20, t.glyph), opacity: io(f, [6 + i * 8, 14 + i * 8], [0, 1]) }}>→</span> : null}
              <span style={{ opacity: io(f, [6 + i * 8, 14 + i * 8], [0, 1]) }}>
                <Chip t={t} size={18} color={n === "conductor" ? t.accent : undefined} style={{ padding: "8px 18px", fontWeight: n === "conductor" ? 600 : 400 }}>
                  {n}
                </Chip>
              </span>
            </React.Fragment>
          ))}
        </div>
      </At>
      <At x={0} y={186} o={io(f, [40, 48], [0, 1])} style={{ width: 1200, textAlign: "center" }}>
        <span style={sans(18, t.muted)}>one scroll source, smoothed once, drives the 3D</span>
      </At>
      <div style={{ position: "absolute", left: barX, top: 300, width: barW, height: 8, borderRadius: 4, background: t.codeBg, border: `1px solid ${t.line}`, opacity: io(f, [50, 58], [0, 1]) }} />
      {(
        [
          ["exact → logic", 0.62, t.ink, -1],
          ["smooth → visuals", 0.58, t.accent, 1],
        ] as [string, number, string, number][]
      ).map(([label, v, c, side]) => (
        <div key={label} style={{ position: "absolute", left: barX + v * barW - 1, top: 284, opacity: io(f, [54, 64], [0, 1]) }}>
          <div style={{ width: 3, height: 40, background: c, borderRadius: 2 }} />
          <div style={{ position: "absolute", top: 46, ...(side < 0 ? { left: 8 } : { right: 8 }), whiteSpace: "nowrap", ...mono(17, c) }}>{label}</div>
        </div>
      ))}
    </>
  );
};

// ---------- S14 outputs + adjacent skills ----------

const TREE = ["3D.md", ".3d/"];
const DOT3D = ["brief.md", "shots.json", "reference-spec.json", "versions/", "evidence/", "feedback.jsonl"];
const ADJ = ["scroll-animation", "fluid-design", "generate-image", "generate-video", "manufacturing-workflow", "frontend"];

const Outputs: Inner = ({ t }) => {
  const f = useCurrentFrame();
  return (
    <>
      <Box t={t} x={64} y={96} w={480} h={270} code pad="22px 28px">
        <div style={{ ...mono(22, t.ink, { fontWeight: 600 }), opacity: io(f, [6, 14], [0, 1]) }}>
          <span style={{ color: t.amber }}>▤ </span>
          {TREE[0]}
        </div>
        <div style={{ ...mono(22, t.ink, { fontWeight: 600 }), marginTop: 14, opacity: io(f, [12, 20], [0, 1]) }}>
          <span style={{ color: t.amber }}>▸ </span>
          {TREE[1]}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 18px", marginTop: 14, marginLeft: 30 }}>
          {DOT3D.map((p, i) => (
            <span key={p} style={{ ...mono(17, t.ink), opacity: io(f, [18 + i * 4, 26 + i * 4], [0, 1]) }}>
              <span style={{ color: t.amber }}>▤ </span>
              {p}
            </span>
          ))}
        </div>
      </Box>
      <Box t={t} x={572} y={96} w={564} h={270} pad="24px 26px" opacity={io(f, [30, 38], [0, 1])}>
        <div style={{ ...kicker(t), marginBottom: 20 }}>adjacent skills</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          {ADJ.map((s, i) => (
            <span key={s} style={{ opacity: io(f, [34 + i * 4, 42 + i * 4], [0, 1]) }}>
              <Chip t={t} dashed size={18} style={{ background: "transparent", padding: "7px 14px" }}>
                {s}
              </Chip>
            </span>
          ))}
        </div>
      </Box>
    </>
  );
};

// ---------- S15 close ----------

const Close: Inner = ({ t }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", textAlign: "center" }}>
      <div style={{ ...mono(32, t.ink, { letterSpacing: "-0.01em" }), opacity: io(f, [8, 26], [0, 1]) }}>nothing is built before it is measured</div>
      <div style={{ ...mono(32, t.ink, { letterSpacing: "-0.01em" }), marginTop: 12, opacity: io(f, [30, 48], [0, 1]) }}>nothing is called done before it is captured</div>
      <div style={{ ...mono(34, t.accent, { fontWeight: 700 }), marginTop: 40, opacity: io(f, [52, 64], [0, 1]) }}>npx skills add gabros20/3d-skill</div>
    </AbsoluteFill>
  );
};

// ---------- timeline: holds computed, not felt ----------

// HOLD (all still, after the last element lands) ≥ 2.0 s settle + W / 3 s + 1.0 s × G, where W counts
// the NEW words a viewer should read (headline + key lines + caption; monospace words × 1.3) and G
// the visual groups to parse. `mono`/`sans` list exactly the on-screen strings counted.
const FPS = 30;
const OVERLAP = 8;
const words = (s: string) => s.split(/\s+/).filter((w) => /[A-Za-z0-9]/.test(w)).length;

type Def = {
  id: string;
  act: 0 | 1 | 2;
  chapter: string;
  title: string;
  caption: string;
  IN: number; // local frame the last element lands
  G: number;
  mono: string[];
  sans: string[];
  out?: number;
  dy?: number; // centres the content block between headline (bottom ≈ 76) and caption (top ≈ 470)
  C: Inner;
};

const DEFS: Def[] = [
  {
    id: "request", act: 1, chapter: "The request", C: Request, IN: 36, G: 2, dy: 26,
    title: "a vague prompt, one reference",
    caption: "Most 3D work starts **guessing** from here.",
    mono: [PROMPT, "ref.mp4"], sans: [],
  },
  {
    id: "measure", act: 1, chapter: "Measure the reference", C: Measure, IN: 64, G: 2, dy: 26,
    title: "measure first",
    caption: "Scripts measure; **every guess gets a range**.",
    mono: ["ref-extract ref.mp4", ".3d/reference-spec.json", ...SPEC_ROWS.map(([a, b, , l]) => `${a} ${b} ${l}`)],
    sans: [],
  },
  {
    id: "grill", act: 1, chapter: "Grill only the gaps", C: Grill, IN: 62, G: 2, dy: 20,
    title: "ask only the gaps",
    caption: "**At most six questions per round**, each with an answer.",
    mono: [...QS.map(([, a]) => a), "Round 1"],
    sans: QS.map(([q]) => q),
  },
  {
    id: "brief", act: 1, chapter: "Brief, shots, gates", C: Brief, IN: 58, G: 2, dy: 26,
    title: "shots, then five gates",
    caption: "Each gate opens **only on your yes**.",
    mono: [".3d/shots.json shots.v1"],
    sans: GATES,
  },
  {
    id: "approach", act: 1, chapter: "Pick the pipeline", C: Approach, IN: 58, G: 2, dy: 42,
    title: "use picks the pipeline",
    caption: "Every pipeline has a **fallback ladder**.",
    mono: MATRIX.map(([u]) => u),
    sans: [...MATRIX.map(([, s]) => s), "fallback", ...LADDER],
  },
  {
    id: "build", act: 1, chapter: "Build", C: Build, IN: 56, G: 1, dy: 20,
    title: "build",
    caption: "Compressed from a **kept master**, never a bare optimize.",
    mono: ["headless CLI", ...CHAIN, "optimize", "glb-report PASS", "SceneCanvas.tsx"],
    sans: ["Blender", "GLB", "budget", "live scene"],
  },
  {
    id: "preview", act: 1, chapter: "Preview every shot", C: Preview, IN: 72, G: 1,
    title: "preview every shot",
    caption: "Each version is **captured** and laid over the reference.",
    mono: ["v001", "reference overlay 50%"],
    sans: [],
  },
  {
    id: "critic", act: 1, chapter: "A fresh critic", C: Critic, IN: 150, G: 2, dy: 26,
    title: "a fresh critic, before you",
    caption: "v001 fails; **the fix is v002**, re-scored before you see it.",
    mono: ["fresh critic", "v001 · fail", "v002 · pass"],
    sans: ["never told what was fixed", ...SCORES.map(([l]) => l)],
  },
  {
    id: "approve", act: 1, chapter: "Your note, v003, approved", C: Approve, IN: 116, G: 2, dy: 26,
    title: "your note becomes v003",
    caption: "The loop ends **when you approve**.",
    mono: ["note 1 " + NOTE, "v003 vs v002", "ssim 0.95", "approved"],
    sans: ["a visible, local change"],
  },
  {
    id: "record", act: 1, chapter: "The record", C: Record, IN: 54, G: 1, dy: 26,
    title: "the record: 3D.md",
    caption: "Approved means **recorded**.",
    mono: ["pipeline: SCROLL world", "budget: PASS 84,210 tris · 1.90 MB", ...LOG.map((r) => r.join(" "))],
    sans: [],
  },
  {
    id: "router", act: 2, chapter: "A router, not a library", C: Router, IN: 82, G: 2, dy: 22,
    title: "a router, not a library",
    caption: "A lane loads **only its files**: 36 references, none preloaded.",
    mono: [...LANES, "3 of 36 loaded"],
    sans: [],
  },
  {
    id: "preflight", act: 2, chapter: "Preflight", C: Preflight, IN: 58, G: 1, dy: 26,
    title: "preflight",
    caption: "It proposes installs with their cost and **never installs unasked**.",
    mono: ["capabilities", "ktx missing", "install ktx? (free)", "nothing installed without your yes", SCRIPTS],
    sans: ["the pack's scripts"],
  },
  {
    id: "scroll", act: 2, chapter: "Scroll inside the pin", C: Scroll, IN: 64, G: 2, dy: 42,
    title: "scroll inside the pin",
    caption: "Logic reads **exact**; visuals read **smooth**.",
    mono: [...FLOW, "exact → logic", "smooth → visuals"],
    sans: ["one scroll source, smoothed once, drives the 3D"],
  },
  {
    id: "outputs", act: 2, chapter: "Where everything lands", C: Outputs, IN: 62, G: 2, dy: 40,
    title: "where everything lands",
    caption: "Adjacent skills are **recommended, never invoked**.",
    mono: [...TREE, ...DOT3D, ...ADJ],
    sans: ["adjacent skills"],
  },
  {
    id: "close", act: 0, chapter: "Measured, then captured", C: Close, IN: 64, G: 1, out: 12,
    title: "",
    caption: "",
    mono: ["nothing is built before it is measured", "nothing is called done before it is captured", "npx skills add gabros20/3d-skill"],
    sans: [],
  },
];

export const readingLoad = (d: { title: string; caption: string; mono: string[]; sans: string[]; G: number }) => {
  const W = 1.3 * [d.title, ...d.mono].reduce((n, s) => n + words(s), 0) + [d.caption, ...d.sans].reduce((n, s) => n + words(s), 0);
  const holdS = 2 + W / 3 + d.G;
  return { W, holdS, hold: Math.ceil(holdS * FPS) };
};

// The same component is placed on a Track below and registered standalone in Root.tsx
// (remotion-markup/connected-compositions.md); its own background lets it open on its own.
export type SceneProps = { readonly theme: ThemeName; readonly dur: number; readonly title: string; readonly caption: string; readonly out: number };
const connect = (id: string, Content: Inner, dy: number) => {
  const SceneInner: React.FC<SceneProps> = ({ theme, dur, title, caption, out }) => {
    const t = themes[theme];
    return (
      <Shell t={t} dur={dur} title={title} caption={caption} out={out}>
        <AbsoluteFill style={{ translate: `0px ${dy}px` }}>
          <Content t={t} />
        </AbsoluteFill>
      </Shell>
    );
  };
  return Interactive.create({
    Component: SceneInner,
    componentName: `${id[0].toUpperCase()}${id.slice(1)}Scene`,
    layout: "absolute-fill",
  });
};

let cursor = 0;
export const SCENES = DEFS.map((d) => {
  const { W, holdS, hold } = readingLoad(d);
  const out = d.out ?? 18;
  const dur = d.IN + hold + out;
  const start = cursor;
  cursor = start + dur - OVERLAP;
  return { ...d, W, holdS, hold, out, dur, start, Scene: connect(d.id, d.C, d.dy ?? 0) };
});
export const DURATION = SCENES[SCENES.length - 1].start + SCENES[SCENES.length - 1].dur;
const CLOSE_START = SCENES.find((s) => s.act === 0)!.start;
// the rail is gone once the close has faded in
export const RAIL_END = CLOSE_START + 8;

// ---------- chapter rail (outside scene opacity; crossfades station state at each scene start) ----------

const ActRail: React.FC<{ t: Theme; act: 1 | 2; cur: number; prev: number; k: number; opacity: number }> = ({ t, act, cur, prev, k, opacity }) => {
  const stations = SCENES.map((s, i) => ({ ...s, i })).filter((s) => s.act === act);
  const state = (i: number, c: number) => (i === c ? 2 : i < c ? 1 : 0);
  const dotFill = (st: number) => (st === 2 ? t.accent : st === 1 ? t.muted : t.bg);
  const dotLine = (st: number) => (st === 2 ? t.accent : t.muted);
  // every label clears 4.5:1 on bg: current accent, done ink, ahead muted
  const label = (st: number) => (st === 2 ? t.accent : st === 1 ? t.ink : t.muted);
  const mix = (fn: (st: number) => string, i: number) => interpolateColors(k, [0, 1], [fn(state(i, prev)), fn(state(i, cur))]);
  return (
    <div style={{ position: "absolute", left: 0, top: 12, width: 1200, height: 24, opacity }}>
      <span style={{ position: "absolute", left: 64, top: 4, ...kicker(t, t.accent) }}>{act === 1 ? "Act 1 · one task" : "Act 2 · the pack"}</span>
      <div style={{ position: "absolute", left: 250, right: 64, top: 2, display: "flex", justifyContent: act === 1 ? "space-between" : "flex-start", gap: act === 1 ? 0 : 40 }}>
        {stations.map((s) => (
          <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: 4, background: mix(dotFill, s.i), border: `1.5px solid ${mix(dotLine, s.i)}` }} />
            <span style={mono(15, mix(label, s.i))}>{s.id}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const RailInner: React.FC<{ theme: ThemeName; style?: React.CSSProperties }> = ({ theme, style }) => {
  const t = themes[theme];
  const frame = useCurrentFrame();
  let cur = 0;
  SCENES.forEach((s, i) => {
    if (frame >= s.start) cur = i;
  });
  const prev = Math.max(0, cur - 1);
  const k = cur === 0 ? 1 : io(frame, [SCENES[cur].start, SCENES[cur].start + 12], [0, 1]);
  const act2Start = SCENES.find((s) => s.act === 2)!.start;
  const a2 = io(frame, [act2Start, act2Start + 16], [0, 1]);
  const all = io(frame, [0, 10], [0, 1]) * io(frame, [CLOSE_START - 8, CLOSE_START + 8], [1, 0]);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1200, height: 40, ...style }}>
      {a2 < 1 ? <ActRail t={t} act={1} cur={Math.min(cur, 9)} prev={Math.min(prev, 9)} k={cur > 9 ? 1 : k} opacity={all * (1 - a2)} /> : null}
      {a2 > 0 ? <ActRail t={t} act={2} cur={Math.max(cur, 10)} prev={Math.max(prev, 10)} k={cur === 10 ? 1 : k} opacity={all * a2} /> : null}
    </div>
  );
};

// a bounded element (layout 'none'): it applies the Studio's style to its own root
export const Rail = Interactive.create({ Component: RailInner, componentName: "ChapterRail" });

// ---------- composition ----------

export const HowThreeDWorks: React.FC<{ theme: ThemeName }> = ({ theme }) => (
  <>
    <AbsoluteFill style={{ background: themes[theme].bg }} />
    {(["Scenes A", "Scenes B"] as const).map((track, k) => (
      <Track key={track} name={track}>
        {SCENES.filter((_, i) => i % 2 === k).map(({ id, start, dur, title, caption, out, Scene }) => (
          <Scene key={id} name={id} from={start} durationInFrames={dur} theme={theme} dur={dur} title={title} caption={caption} out={out} />
        ))}
      </Track>
    ))}
    <Track name="Rail">
      <Rail name="chapter rail" from={0} durationInFrames={RAIL_END} theme={theme} />
    </Track>
  </>
);
