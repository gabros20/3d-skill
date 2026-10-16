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
  fontSize: 13,
  fontWeight: 600,
  letterSpacing: "0.14em",
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
      fontSize: 13,
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

const Caption: React.FC<{ t: Theme; a: number; b: number; children: React.ReactNode }> = ({ t, a, b, children }) => {
  const f = useCurrentFrame();
  const o = io(f, [a, a + 12], [0, 1]) * io(f, [b - 10, b], [1, 0]);
  if (o <= 0.01) return null;
  return (
    <div style={{ position: "absolute", left: 40, right: 40, bottom: 18, textAlign: "center", ...sans(21, t.muted), opacity: o }}>
      {children}
    </div>
  );
};
const B: React.FC<{ t: Theme; children: React.ReactNode }> = ({ t, children }) => <b style={{ color: t.ink }}>{children}</b>;

const Shell: React.FC<{ t: Theme; dur: number; title?: string; out?: number; children: React.ReactNode }> = ({ t, dur, title, out = 18, children }) => {
  const f = useCurrentFrame();
  const o = io(f, [0, 16], [0, 1]) * io(f, [dur - out, dur], [1, 0]);
  if (o <= 0.005) return null;
  return (
    <AbsoluteFill style={{ opacity: o, background: t.bg }}>
      {title ? (
        <div style={{ position: "absolute", top: 46, left: 0, right: 0, textAlign: "center", ...mono(24, t.ink, { letterSpacing: "-0.01em" }) }}>{title}</div>
      ) : null}
      {children}
    </AbsoluteFill>
  );
};

// ---------- S01 request ----------

const PROMPT = "/3d make our homepage hero feel like this — scroll-driven";

const Request: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  return (
    <Shell t={t} dur={dur} title="a vague prompt, one reference">
      <Box t={t} x={72} y={186} w={672} pad="18px 22px" style={{ borderRadius: 14, scale: String(io(f, [0, 14], [0.96, 1])) }}>
        <div style={mono(18, t.ink, { whiteSpace: "pre-wrap", minHeight: 27 })}>{typed(f, 4, 30, PROMPT)}</div>
        <div style={{ marginTop: 12, opacity: io(f, [24, 32], [0, 1]) }}>
          <Chip t={t} fill size={14}>
            <span style={{ color: t.amber }}>▤ </span>ref.mp4
          </Chip>
        </div>
      </Box>
      <At x={96} y={318} o={io(f, [26, 36], [0, 1])}>
        <span style={sans(15, t.muted)}>no 3D.md yet → preflight runs first (act 2)</span>
      </At>
      <At x={780} y={150} o={io(f, [14, 30], [0, 1])} dx={io(f, [14, 36], [24, 0])}>
        <div style={{ width: 320, height: 180, borderRadius: 10, overflow: "hidden", position: "relative", border: `1.5px solid ${t.line}` }}>
          <Puck t={t} look="ref" framing="S01" w={320} h={180} />
          <div style={{ position: "absolute", left: 12, right: 12, bottom: 10, height: 3, borderRadius: 2, background: "rgba(255,255,255,.18)" }}>
            <div style={{ width: "40%", height: "100%", borderRadius: 2, background: REF.text }} />
          </div>
        </div>
        <div style={{ marginTop: 10, ...mono(15, t.muted) }}>ref.mp4 · video</div>
      </At>
      <Caption t={t} a={8} b={124}>
        A vague prompt and one reference clip. Most 3D work starts <B t={t}>guessing</B> from here.
      </Caption>
    </Shell>
  );
};

// ---------- S02 measure ----------

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

const CardHead: React.FC<{ t: Theme; name: string; right?: string }> = ({ t, name, right }) => (
  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
    <span style={mono(15, t.ink)}>
      <span style={{ color: t.amber }}>▤ </span>
      {name}
    </span>
    {right ? <span style={mono(13, t.muted)}>{right}</span> : null}
  </div>
);

const MeasureCard: React.FC<{ t: Theme; i: number }> = ({ t, i }) => {
  if (i === 0)
    return (
      <>
        <CardHead t={t} name="palette.json" right="k = 6" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          {PALETTE.map(([hex, w]) => (
            <div key={hex}>
              <div style={{ height: 40, borderRadius: 6, background: hex, border: `1px solid ${t.line}` }} />
              <div style={{ ...mono(13, t.muted), marginTop: 3 }}>{w.toFixed(2)}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 14 }}>
          <Tag t={t} k="measured" />
        </div>
      </>
    );
  if (i === 1)
    return (
      <>
        <CardHead t={t} name="luma.json" right="16 bins" />
        <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 90, borderBottom: `1.5px solid ${t.line}` }}>
          {HIST.map((v, k) => (
            <div key={k} style={{ flex: 1, height: `${(v / 0.24) * 100}%`, background: t.glyph, borderRadius: "2px 2px 0 0" }} />
          ))}
        </div>
        <div style={{ ...mono(14, t.ink), marginTop: 12 }}>key low · contrast 0.71</div>
        <div style={{ ...mono(14, t.ink), marginTop: 4, marginBottom: 10 }}>p50 0.18</div>
        <Tag t={t} k="measured" />
      </>
    );
  if (i === 2)
    return (
      <>
        <CardHead t={t} name="cuts.json" right="threshold 0.3" />
        <div style={{ position: "relative", height: 90 }}>
          <div style={{ position: "absolute", left: 0, right: 0, top: 44, height: 2, background: t.line }} />
          {[2.1, 4.4].map((s) => (
            <div key={s} style={{ position: "absolute", left: `${(s / 6) * 100}%`, top: 26 }}>
              <div style={{ width: 3, height: 38, background: t.ink, borderRadius: 2, marginLeft: -1.5 }} />
              <div style={{ ...mono(13, t.ink), marginTop: 4, marginLeft: -14 }}>{s} s</div>
            </div>
          ))}
          <div style={{ position: "absolute", left: 0, top: 50, ...mono(13, t.muted) }}>0</div>
          <div style={{ position: "absolute", right: 0, top: 50, ...mono(13, t.muted) }}>6 s</div>
        </div>
        <div style={{ ...mono(14, t.ink), marginTop: 12, marginBottom: 32 }}>2 cuts</div>
        <Tag t={t} k="measured" />
      </>
    );
  const pts = SPEED.map((v, k) => `${(k / 47) * 222},${90 - (v / 6) * 80}`).join(" ");
  return (
    <>
      <CardHead t={t} name="motion.json" right="8 samples/s" />
      <svg width={222} height={90} style={{ display: "block", borderBottom: `1.5px solid ${t.line}` }}>
        <polyline points={pts} fill="none" stroke={t.accent} strokeWidth={2} />
      </svg>
      <div style={{ ...mono(14, t.ink), marginTop: 12 }}>speed_w_pct_s</div>
      <div style={{ ...mono(14, t.ink), marginTop: 4, marginBottom: 10 }}>≈ 3.8 %W/s</div>
      <Tag t={t} k="measured" />
    </>
  );
};

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

const SPEC_ROWS: [string, string, TagKind, string?][] = [
  ["colour.palette[0].hex", "#0d1117", "measured"],
  ["colour.luma.p50", "0.18", "measured"],
  ["lighting.key.dir_clock", '"10"', "read"],
  ["video.shots[0].camera_move", "push-in", "read"],
  ["camera.focal_mm_ff", "[70, 135]", "inferred", "low · inferred"],
  ["hidden_or_unknown", "back faces, absolute scale", "unknown", ""],
];
const PASSES = ["classify", "composition", "camera", "light", "colour", "materials", "form", "fx", "reconcile"];

const Measure: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const dock = io(f, [116, 130], [0, 1]);
  return (
    <Shell t={t} dur={dur} title="measure first, then read">
      <Box t={t} x={64} y={92} w={1072} code pad="8px 16px" opacity={io(f, [116, 128], [1, 0])}>
        <Cmd t={t} f={f} a={8} b={28} cmd="<skill>/scripts/ref-extract ref.mp4" size={16} />
        <Out t={t} f={f} at={30} size={16}>
          ref-extract: video ref.mp4 -&gt; .3d/refs/ref (12 frames, 2 cuts)
        </Out>
      </Box>
      {[0, 1, 2, 3].map((i) => {
        const at = 42 + i * 10;
        const x = 64 + i * 272;
        const y = 168;
        return (
          <Box
            key={i}
            t={t}
            x={x}
            y={y}
            w={256}
            h={252}
            opacity={io(f, [at, at + 10], [0, 1]) * io(f, [116, 124], [1, 0])}
            style={{ translate: `0px ${io(f, [at, at + 10], [8, 0])}px` }}
          >
            <MeasureCard t={t} i={i} />
          </Box>
        );
      })}
      {f >= 120 ? (
        <>
          {/* docked: each file keeps its name and its graphic, no small text */}
          {["palette.json", "luma.json", "cuts.json", "motion.json"].map((name, i) => (
            <Box key={name} t={t} x={64} y={140 + i * 60} w={276} h={52} pad="0 12px" opacity={dock * io(f, [122 + i * 3, 132 + i * 3], [0, 1])}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: "100%" }}>
                <span style={mono(14, t.ink)}>
                  <span style={{ color: t.amber }}>▤ </span>
                  {name}
                </span>
                <MiniViz t={t} i={i} />
              </div>
            </Box>
          ))}
          <At x={360} y={108} o={io(f, [120, 130], [0, 1])}>
            <div style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
              <span style={kicker(t)}>9 vision passes</span>
              {PASSES.map((p, k) => {
                const on = io(f, [130 + k * 2, 136 + k * 2], [0, 1]);
                return (
                  <span key={p} style={mono(13, interpolateColors(on, [0, 1], [t.glyph, t.accent]))}>
                    {p}
                  </span>
                );
              })}
            </div>
          </At>
          <Box t={t} x={360} y={140} w={776} h={236} code pad="12px 18px" opacity={io(f, [122, 136], [0, 1])}>
            <div style={{ ...mono(15, t.ink), marginBottom: 10 }}>
              <span style={{ color: t.amber }}>▤ </span>.3d/reference-spec.json <span style={{ color: t.muted }}>· refspec.v1</span>
            </div>
            {SPEC_ROWS.map(([field, value, k, label], r) => {
              const at = 146 + r * 5;
              return (
                <div key={field} style={{ display: "flex", alignItems: "center", height: 30, opacity: io(f, [at, at + 6], [0, 1]) }}>
                  <span style={mono(15, t.ink, { width: 290 })}>{field}</span>
                  <span style={mono(15, k === "unknown" ? t.muted : t.ink, { flex: 1 })}>{value}</span>
                  {label === "" ? null : <Tag t={t} k={k} label={label} />}
                </div>
              );
            })}
          </Box>
          <At x={360} y={386} o={io(f, [168, 178], [0, 1])}>
            <div style={{ display: "flex", gap: 8 }}>
              {(["measured", "read", "inferred", "assumed", "unknown"] as TagKind[]).map((k) => (
                <Tag key={k} t={t} k={k} />
              ))}
            </div>
          </At>
          <At x={360} y={420}>
            <span style={mono(14, t.muted, { opacity: io(f, [178, 184], [0, 1]) })}>$ spec-check .3d/reference-spec.json   </span>
            <Stamp f={f} at={180} color={t.good} size={14}>
              .3d/reference-spec.json (refspec.v1): OK
            </Stamp>
          </At>
        </>
      ) : null}
      <Caption t={t} a={12} b={128}>
        A script measures first: palette, luma key, cuts, and <B t={t}>camera speed in %W/s</B>.
      </Caption>
      <Caption t={t} a={132} b={dur - 2}>
        Nine vision passes fill the rest. Every estimate carries <B t={t}>a range, a confidence and an evidence tag</B>.
      </Caption>
    </Shell>
  );
};

// ---------- S03 grill ----------

const OPEN = new Set([3, 10, 15]); // style, motion, budgets (bank rows 4, 11, 16)
const INFER = new Set([5, 11, 13]);
const QS: [string, string][] = [
  ["Pinned in the homepage hero, scrubbed by scroll?", "yes · SCROLL, one viewport per beat"],
  ["Match the clip, or borrow its style?", "style · keep the rim light, drop their product"],
  ["Device floor?", "mid-range phone · budgets via 3D.md"],
  ["The look is open: A, B or C, plus one change?", "B"],
];
const DIRS: [string, Look][] = [
  ["A · Studio Product", "studio"],
  ["B · Night Silicon", "night"],
  ["C · Golden Daylight", "golden"],
];

const Grill: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  return (
    <Shell t={t} dur={dur} title="grill only the gaps">
      <At x={64} y={92}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={sans(15, t.muted)}>18 dimensions</span>
          <div style={{ display: "flex", gap: 4 }}>
            {Array.from({ length: 18 }, (_, i) => {
              const c = OPEN.has(i) ? t.amber : INFER.has(i) ? t.glyph : t.good;
              const on = io(f, [4 + i * 1.5, 10 + i * 1.5], [0, 1]);
              return <div key={i} style={{ width: 14, height: 14, borderRadius: 3, border: `1.5px solid ${c}`, background: interpolateColors(on, [0, 1], [t.bg, c]) }} />;
            })}
          </div>
          <span style={{ ...mono(13, t.good), marginLeft: 6 }}>■ given</span>
          <span style={mono(13, t.glyph)}>■ inferable</span>
          <span style={mono(13, t.amber)}>■ open</span>
        </div>
      </At>
      <At x={64} y={118} o={io(f, [10, 22], [0, 1])}>
        <span style={sans(15, t.muted)}>I found: next 16 · three 0.180 · @react-three/fiber 9 · motion 12</span>
      </At>
      <At x={64} y={142} o={io(f, [16, 28], [0, 1])}>
        <span style={mono(15, t.ink)}>
          Scroll-pinned hero reveal · <span style={{ color: t.amber }}>55%</span> · unknown: device floor, scroll length, look
        </span>
      </At>
      <Box t={t} x={64} y={176} w={736} h={222} pad="10px 18px" opacity={io(f, [18, 28], [0, 1])}>
        <div style={{ ...kicker(t), marginBottom: 6 }}>Round 1 · 4 of max 6 · each with a recommended answer</div>
        {QS.map(([q, a], i) => {
          const at = 24 + i * 12;
          return (
            <div key={q} style={{ height: 45, opacity: io(f, [at, at + 10], [0, 1]), translate: `${io(f, [at, at + 10], [-8, 0])}px 0px` }}>
              <div style={sans(16, t.ink)}>
                <span style={mono(14, t.muted)}>Q{i + 1} </span>
                {q}
              </div>
              <div style={mono(14.5, t.accent, { marginTop: 2, marginLeft: 30 })}>→ {a}</div>
            </div>
          );
        })}
      </Box>
      <At x={824} y={176} o={io(f, [76, 84], [0, 1])}>
        <div style={sans(15, t.muted)}>the look is open → 3 directions on a greybox</div>
      </At>
      {DIRS.map(([label, look], i) => {
        const at = 78 + i * 8;
        const chosen = look === "night";
        return (
          <At key={label} x={824} y={202 + i * 66} o={io(f, [at, at + 10], [0, 1])}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ borderRadius: 7, overflow: "hidden", border: `2px solid ${chosen ? t.accent : t.glyph}` }}>
                <Puck t={t} look={look} framing="S01" w={96} h={54} />
              </div>
              <span style={sans(15, chosen ? t.ink : t.muted, { fontWeight: chosen ? 600 : 400 })}>{label}</span>
            </div>
          </At>
        );
      })}
      <At x={64} y={412} o={io(f, [110, 122], [0, 1])}>
        <span style={mono(15, t.ink)}>restated brief · [assumed] tags · Out of scope → yes?</span>
        <span style={mono(14, t.muted)}>{'    "sounds good" = delegation → re-ask'}</span>
      </At>
      <Caption t={t} a={16} b={132}>
        Facts are looked up, never asked. Only the gaps become questions — <B t={t}>six at most</B>, each with an answer.
      </Caption>
      <Caption t={t} a={136} b={dur - 2}>
        An open look gets <B t={t}>three divergent directions</B>. Nothing is built until a restated brief gets a yes.
      </Caption>
    </Shell>
  );
};

// ---------- S04 brief ----------

const BRIEF_LINES = ["1 Logline and thesis", "4 Style — 3 offered, B chosen", "6 Camera — lens per shot", "9 Motion — reduced-motion alternative", "11 Deliverables and budgets", "12 Pipeline"];
const SHOT_JSON = `{ "schema": "shots.v1",
  "id": "S01", "focal_mm": 35,
  "position": [3.2, 1.6, 5.0],
  "target": [0, 0.5, 0],
  "scroll": [0, 0.3], "ease": "inOut",
  "to": { "position": [2.2, 1.2, 3.6] } }`;
const GATES = ["Brief", "Style frames", "Blockout", "Lookdev", "Final"];

const Brief: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const card = (i: number) => ({ opacity: io(f, [8 + i * 16, 22 + i * 16], [0, 1]) });
  return (
    <Shell t={t} dur={dur} title="brief, shots, five gates">
      <Box t={t} x={64} y={96} w={340} h={244} {...card(0)}>
        <div style={{ ...mono(15, t.ink), marginBottom: 10 }}>
          <span style={{ color: t.amber }}>▤ </span>.3d/brief.md
        </div>
        {BRIEF_LINES.map((l) => (
          <div key={l} style={mono(14, t.ink, { lineHeight: 1.75 })}>
            {l}
          </div>
        ))}
        <div style={{ ...sans(15, t.muted), marginTop: 8 }}>14 sections · every guess tagged [assumed]</div>
      </Box>
      <Box t={t} x={420} y={96} w={344} h={244} {...card(1)}>
        <div style={{ ...mono(15, t.ink), marginBottom: 12 }}>storyboard · hook → reveal → payoff</div>
        {(
          [
            ["S01", "establish · 35 mm"],
            ["S02", "detail · 85 mm"],
            ["S03", "payoff · fov 30"],
          ] as [Framing, string][]
        ).map(([id, label]) => (
          <div key={id} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
            <div style={{ border: `1.5px solid ${t.glyph}`, borderRadius: 6, overflow: "hidden" }}>
              <Puck t={t} look="greybox" framing={id} w={96} h={54} />
            </div>
            <span style={mono(14, t.ink)}>
              {id} <span style={{ color: t.muted }}>{label}</span>
            </span>
          </div>
        ))}
      </Box>
      <Box t={t} x={780} y={96} w={356} h={244} code {...card(2)}>
        <div style={{ ...mono(15, t.ink), marginBottom: 8 }}>
          <span style={{ color: t.amber }}>▤ </span>.3d/shots.json
        </div>
        <div style={mono(13.5, t.ink, { lineHeight: 1.55 })}>{SHOT_JSON}</div>
        <div style={{ ...sans(15, t.muted), marginTop: 8 }}>read by preview capture · render_shots.py</div>
      </Box>
      <div style={{ position: "absolute", left: 140, right: 140, top: 381, height: 2, background: t.line, opacity: io(f, [60, 86], [0, 1]) }} />
      {GATES.map((g, i) => {
        const at = 62 + i * 6;
        const x = 120 + i * 230;
        const done = i === 0;
        return (
          <At key={g} x={x} y={368} o={io(f, [at, at + 8], [0, 1])}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, background: t.bg, paddingRight: 8 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 14,
                  display: "grid",
                  placeItems: "center",
                  border: `2px solid ${done ? interpolateColors(io(f, [88, 100], [0, 1]), [0, 1], [t.line, t.good]) : t.line}`,
                  background: t.panel,
                  ...mono(14, t.ink),
                }}
              >
                {done && f >= 88 ? <Stamp f={f} at={88} color={t.good} size={14}>✓</Stamp> : i + 1}
              </div>
              <span style={sans(15, t.ink)}>{g}</span>
            </div>
          </At>
        );
      })}
      <At x={0} y={414} o={io(f, [84, 96], [0, 1])} style={{ width: 1200, textAlign: "center" }}>
        <span style={sans(15, t.muted)}>each on your yes · a change that crosses an approved gate re-opens it</span>
      </At>
      <Caption t={t} a={12} b={dur - 2}>
        The brief, a storyboard and <B t={t}>shots.v1</B> cameras — then five sign-off gates, each passed only on your yes.
      </Caption>
    </Shell>
  );
};

// ---------- S05 approach ----------

const MATRIX: [string, string][] = [
  ["HERO live", "real-time three.js or R3F, compressed GLB, poster first"],
  ["HERO simple · VIDEO", "pre-rendered from Blender, poster image"],
  ["SCROLL world", "real-time scene driven by scroll progress"],
  ["SCROLL scrub", "pre-rendered frames, scrubbed · scroll-video.md"],
  ["PROD stills", "offline Blender render"],
  ["Spline", "Spline scene or react-spline embed"],
  ["SPLAT", "Gaussian-splat viewer"],
  ["AR", "GLB plus USDZ, or WebXR"],
];
const LADDER: [string, string][] = [
  ["Live, full quality", ""],
  ["Live, reduced", "over frame budget on the device floor"],
  ["Poster + video", "no WebGL, low-power, data saver"],
  ["Static composition", "reduced motion, no JS, failed load"],
];

const Approach: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const hl = io(f, [52, 62], [0, 1]);
  return (
    <Shell t={t} dur={dur} title="target use picks the pipeline">
      <Box t={t} x={64} y={92} w={652} h={356} pad="10px 18px" opacity={io(f, [4, 14], [0, 1])}>
        <div style={{ ...kicker(t), marginBottom: 6 }}>target use → strategy</div>
        {MATRIX.map(([use, strat], i) => {
          const at = 8 + i * 6;
          const me = i === 2;
          return (
            <div
              key={use}
              style={{
                opacity: io(f, [at, at + 8], [0, 1]),
                borderLeft: `3px solid ${me ? interpolateColors(hl, [0, 1], [t.panel, t.accent]) : t.panel}`,
                paddingLeft: 10,
                marginLeft: -13,
                height: me ? 52 : 34,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
              }}
            >
              <div style={{ display: "flex", alignItems: "baseline" }}>
                <span style={mono(14.5, me ? t.ink : t.muted, { width: 190, fontWeight: me ? 600 : 400 })}>{use}</span>
                <span style={sans(15, me ? t.ink : t.muted)}>{strat}</span>
              </div>
              {me ? <div style={{ ...sans(15, t.accent), marginLeft: 190, opacity: hl }}>camera freedom, copy synced to state</div> : null}
            </div>
          );
        })}
        <div style={{ ...mono(13.5, t.glyph), marginTop: 6, opacity: io(f, [56, 62], [0, 1]) }}>+ GAME · PRINT · CAD</div>
      </Box>
      <At x={744} y={96} o={io(f, [62, 70], [0, 1])}>
        <div style={kicker(t)}>fallback ladder</div>
      </At>
      {LADDER.map(([rung, trig], i) => {
        const at = 64 + i * 5;
        return (
          <Box key={rung} t={t} x={744 + i * 10} y={120 + i * 52} w={392 - i * 10} h={44} pad="5px 12px" code opacity={io(f, [at, at + 8], [0, 1])}>
            <div style={sans(15, t.ink)}>
              <span style={mono(14, t.muted)}>{i + 1} </span>
              {rung}
            </div>
            {trig ? <div style={sans(15, t.muted)}>{trig}</div> : null}
          </Box>
        );
      })}
      <At x={744} y={346} o={io(f, [86, 96], [0, 1])}>
        <div style={{ ...mono(15, t.accent), marginBottom: 8 }}>read next ▸</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, width: 392 }}>
          {["scroll-conductor", "scroll-adapters", "threejs-r3f-next"].map((c) => (
            <Chip key={c} t={t} color={t.accent} size={13.5}>
              {c}
            </Chip>
          ))}
        </div>
        <div style={{ ...sans(15, t.muted), marginTop: 8 }}>always: design-art-direction · shared-verification</div>
      </At>
      <Caption t={t} a={12} b={dur - 2}>
        Target use picks the pipeline and a <B t={t}>fallback ladder</B> — and names the only files to read next.
      </Caption>
    </Shell>
  );
};

// ---------- S06 build ----------

const CHAIN = ["case-master.glb · kept", "dedup", "weld", "prune --keep-leaves true", "meshopt", "case.glb"];

const Build: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  return (
    <Shell t={t} dur={dur} title="build — Blender, the GLB pipeline, the live scene">
      <At x={64} y={92} o={io(f, [6, 14], [0, 1])}>
        <div style={kicker(t)}>Blender</div>
      </At>
      <At x={64} y={112} o={io(f, [8, 18], [0, 1])}>
        <div style={{ display: "flex", gap: 8 }}>
          <Chip t={t} color={t.accent}>
            headless CLI
          </Chip>
          <Chip t={t} color={t.muted} dashed>
            MCP bridge — consent first
          </Chip>
        </div>
      </At>
      <At x={64} y={148}>
        <Cmd t={t} f={f} a={12} b={30} size={14} cmd="blender -b case.blend --python-exit-code 1 --python export_web.py -- --out case-master.glb" />
      </At>

      <At x={64} y={186} o={io(f, [32, 40], [0, 1])}>
        <div style={kicker(t)}>glTF</div>
      </At>
      <At x={64} y={206}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {CHAIN.map((c, i) => {
            const at = 34 + i * 5;
            return (
              <React.Fragment key={c}>
                {i ? <span style={{ ...mono(15, t.glyph), opacity: io(f, [at, at + 6], [0, 1]) }}>→</span> : null}
                <span style={{ opacity: io(f, [at, at + 8], [0, 1]) }}>
                  <Chip t={t} fill color={i === 0 || i === CHAIN.length - 1 ? t.ink : undefined} size={13.5}>
                    {c}
                  </Chip>
                </span>
              </React.Fragment>
            );
          })}
          <span style={{ marginLeft: 18, opacity: io(f, [66, 72], [0, 1]), display: "inline-flex", alignItems: "center", gap: 8 }}>
            <Chip t={t} color={t.bad} size={13.5} style={{ textDecoration: "line-through" }}>
              optimize
            </Chip>
            <span style={sans(15, t.bad)}>never bare</span>
          </span>
        </div>
      </At>
      <At x={64} y={248}>
        <div style={{ display: "flex", gap: 14, alignItems: "baseline" }}>
          <Cmd t={t} f={f} a={74} b={80} size={14} cmd="glb-report case.glb --budget hero" />
          {f >= 80 ? <Stamp f={f} at={80} color={t.good} size={14}>budget hero (desktop): PASS</Stamp> : null}
        </div>
        <Out t={t} f={f} at={82} size={14} color={t.ink}>
          {"  "}
          <span style={{ color: t.good }}>PASS</span> tris: 84,210 / 100,000 · <span style={{ color: t.good }}>PASS</span> bytes: 1,992,294 / 3,145,728
        </Out>
        <div style={{ display: "flex", gap: 14, alignItems: "baseline" }}>
          <Cmd t={t} f={f} a={86} b={92} size={14} cmd="preview diff master.png case.png" />
          <Out t={t} f={f} at={92} size={14} color={t.ink}>
            {'"ssim": 0.997'}
            <span style={{ color: t.muted }}>{"   lossless passes need ≥ 0.99"}</span>
          </Out>
        </div>
      </At>

      <At x={64} y={340} o={io(f, [96, 104], [0, 1])}>
        <div style={kicker(t)}>three.js / R3F</div>
      </At>
      <At x={64} y={360} o={io(f, [98, 112], [0, 1])}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {["r3f/SceneCanvas.tsx", "conductor.ts", "adapters/motion.ts"].map((c) => (
            <Chip key={c} t={t} fill size={13.5}>
              <span style={{ color: t.amber }}>▤ </span>
              {c}
            </Chip>
          ))}
          <span style={{ ...sans(15, t.muted), marginLeft: 8 }}>copied into the project and owned</span>
        </div>
      </At>
      <Caption t={t} a={12} b={124}>
        Blender runs <B t={t}>headless</B> for anything that must reproduce; the MCP bridge needs your consent.
      </Caption>
      <Caption t={t} a={128} b={dur - 2}>
        Explicit glTF passes from a <B t={t}>kept master</B>, then a budget report and pixel parity.
      </Caption>
    </Shell>
  );
};

// ---------- viewer mock (S07, S09) ----------

const CANVAS_DARK = `radial-gradient(ellipse at 60% 30%, ${REF.bg1} 0%, ${REF.bg0} 75%)`;

const ViewerHead: React.FC<{ t: Theme; version: string; vs: string; active: number; shots?: boolean }> = ({ t, version, vs, active, shots = true }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 10, height: 34, padding: "0 12px", borderBottom: `1.5px solid ${t.line}`, background: t.panel }}>
    <span style={mono(13, t.ink, { fontWeight: 600 })}>3d preview</span>
    <span style={mono(13, t.muted)}>127.0.0.1:4173</span>
    <span style={{ width: 10 }} />
    <Chip t={t} size={13} style={{ padding: "1px 8px" }}>
      {version} ▾
    </Chip>
    <span style={sans(15, t.muted)}>vs</span>
    <Chip t={t} size={13} style={{ padding: "1px 8px" }}>
      {vs} ▾
    </Chip>
    {shots ? (
      <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
        {["S01", "S02", "S03"].map((s, i) => (
          <Chip key={s} t={t} size={13} color={i === active ? t.accent : undefined} style={{ padding: "1px 8px", background: i === active ? t.codeBg : t.panel }}>
            {i + 1} {s}
          </Chip>
        ))}
      </div>
    ) : null}
  </div>
);

const Preview: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const shotO = (i: number) => (i === 0 ? io(f, [72, 82], [1, 0]) : i === 1 ? io(f, [72, 82], [0, 1]) * io(f, [84, 94], [1, 0]) : io(f, [84, 94], [0, 1]));
  const active = f < 77 ? 0 : f < 89 ? 1 : 2;
  const overlay = io(f, [104, 120], [0, 0.5]);
  const cw = 736;
  const ch = 252;
  const pw = 448;
  return (
    <Shell t={t} dur={dur} title="preview every shot of every version">
      <Box t={t} x={64} y={88} w={1072} code pad="6px 16px">
        <div style={{ display: "flex", gap: 16 }}>
          <Cmd t={t} f={f} a={6} b={18} size={14.5} cmd={'preview new-version --note "greybox + look B"'} />
          <Out t={t} f={f} at={20} size={14.5}>
            {'{"version": "v001", "dir": ".3d/versions/v001"}'}
          </Out>
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <Cmd t={t} f={f} a={28} b={40} size={14.5} cmd="preview capture" />
          <Out t={t} f={f} at={42} size={14.5}>
            .3d/evidence/v001/ <span style={{ color: t.ink }}>S01.png  S02.png  S03.png</span>
          </Out>
        </div>
      </Box>
      <Box t={t} x={64} y={160} w={1072} h={288} pad="0" opacity={io(f, [50, 66], [0, 1])}>
        <ViewerHead t={t} version="v001" vs="—" active={active} />
        <div style={{ position: "absolute", left: 0, top: 34, width: cw, height: ch, background: CANVAS_DARK, overflow: "hidden" }}>
          {(["S01", "S02", "S03"] as Framing[]).map((s, i) => (
            <div key={s} style={{ position: "absolute", left: (cw - pw) / 2, top: 0, opacity: shotO(i) }}>
              <Puck t={t} look="v1" framing={s} w={pw} h={ch} bg={false} />
            </div>
          ))}
          <div style={{ position: "absolute", left: (cw - pw) / 2, top: 0, opacity: overlay }}>
            <Puck t={t} look="ref" framing="S03" w={pw} h={ch} bg={false} />
          </div>
        </div>
        <div style={{ position: "absolute", left: cw + 14, top: 46, width: 1072 - cw - 28 }}>
          <div style={{ display: "flex", gap: 14, ...sans(15, t.muted), borderBottom: `1.5px solid ${t.line}`, paddingBottom: 6 }}>
            <span>Look</span>
            <span style={{ color: t.ink, fontWeight: 600, borderBottom: `2px solid ${t.accent}` }}>Compare</span>
            <span>Notes</span>
          </div>
          <div style={{ ...sans(15, t.muted), marginTop: 12 }}>Compare mode</div>
          <Chip t={t} size={13.5} style={{ marginTop: 4 }}>
            Reference overlay ▾
          </Chip>
          <div style={{ ...sans(15, t.glyph), marginTop: 4 }}>Reference split wipe · Version A/B split</div>
          <div style={{ ...sans(15, t.muted), marginTop: 12 }}>Reference image</div>
          <div style={mono(13, t.ink, { marginTop: 2 })}>.3d/refs/ref/frames</div>
          <div style={{ ...sans(15, t.muted), marginTop: 12 }}>Opacity {Math.round(overlay * 100)}%</div>
          <div style={{ marginTop: 6, height: 6, borderRadius: 3, background: t.codeBg, border: `1px solid ${t.line}` }}>
            <div style={{ width: `${overlay * 100}%`, height: "100%", borderRadius: 3, background: t.accent }} />
          </div>
        </div>
      </Box>
      <Caption t={t} a={12} b={120}>
        Each change is a <B t={t}>new version</B>, captured for every shot — not just one.
      </Caption>
      <Caption t={t} a={124} b={dur - 2}>
        The viewer flips named shots and versions, and <B t={t}>lays the reference over the render</B>.
      </Caption>
    </Shell>
  );
};

// ---------- S08 critic (round 1 fails, the fix is a new version, round 2 passes) ----------

const SCORES: [string, number, number][] = [
  ["Composition and hierarchy", 1, 3],
  ["Lighting", 2, 2],
  ["Materials", 2, 2],
  ["Colour and tone", 3, 3],
  ["Motion and timing", 2, 2],
  ["Performance evidence", 2, 2],
  ["Fidelity to the refspec", 3, 3],
];

const Critic: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const fixed = io(f, [180, 194], [0, 1]);
  const r2 = io(f, [208, 218], [0, 1]);
  return (
    <Shell t={t} dur={dur} title="a fresh critic, before you">
      <At x={64} y={96} o={io(f, [8, 20], [0, 1])}>
        <div style={{ display: "flex", gap: 8 }}>
          {(["S01", "S02", "S03"] as Framing[]).map((s) => {
            const bad = s === "S01";
            return (
              <div key={s} style={{ position: "relative" }}>
                <div style={{ borderRadius: 6, overflow: "hidden", border: `2px solid ${bad ? interpolateColors(io(f, [90, 98], [0, 1]) * (1 - fixed), [0, 1], [t.line, t.bad]) : t.line}`, position: "relative", width: 104, height: 59 }}>
                  <Puck t={t} look="v1" framing={s} w={100} h={56} style={{ position: "absolute", opacity: 1 - fixed }} />
                  <Puck t={t} look="v2" framing={s} w={100} h={56} style={{ position: "absolute", opacity: fixed }} />
                </div>
                <div style={mono(13, t.muted, { marginTop: 3 })}>
                  {s}.png
                </div>
              </div>
            );
          })}
        </div>
      </At>
      <At x={64} y={186} o={io(f, [90, 100], [0, 1])}>
        <span style={mono(14, t.bad, { textDecoration: fixed > 0.5 ? "line-through" : "none", opacity: 1 - fixed * 0.5 })}>D1 subject on edge · S01</span>
      </At>
      <At x={64} y={216} o={io(f, [16, 26], [0, 1])}>
        <div style={{ display: "flex", gap: 6 }}>
          <Chip t={t} fill size={13}>
            brief.md
          </Chip>
          <Chip t={t} fill size={13}>
            reference-spec.json
          </Chip>
        </div>
      </At>
      <Box t={t} x={64} y={258} w={346} h={124} code pad="8px 12px" opacity={io(f, [176, 184], [0, 1])}>
        <Cmd t={t} f={f} a={178} b={186} size={13.5} cmd="preview new-version" />
        <Out t={t} f={f} at={184} size={13.5} color={t.ink}>
          {'  --note "recentre (critic D1)"'}
        </Out>
        <Out t={t} f={f} at={188} size={13.5}>
          {'{"version": "v002", …}'}
        </Out>
        <div style={{ display: "flex", gap: 10 }}>
          <Cmd t={t} f={f} a={190} b={196} size={13.5} cmd="preview capture" />
          <Out t={t} f={f} at={196} size={13.5}>
            → evidence/v002/
          </Out>
        </div>
      </Box>
      <svg style={{ position: "absolute", left: 412, top: 236, opacity: io(f, [26, 36], [0, 1]) }} width={40} height={20}>
        <path d="M2 10 H34 M28 4 L36 10 L28 16" stroke={t.glyph} strokeWidth={2} fill="none" />
      </svg>
      <Box t={t} x={448} y={180} w={280} h={120} border={t.accent} opacity={io(f, [26, 42], [0, 1])} style={{ scale: String(io(f, [26, 42], [0.9, 1])) }}>
        <div style={mono(21, t.accent, { fontWeight: 600 })}>fresh critic</div>
        <div style={{ ...sans(14, t.muted), marginTop: 6, whiteSpace: "nowrap" }}>new context · never told what was fixed</div>
        <div style={{ ...mono(14, t.ink), marginTop: 10 }}>round {f < 204 ? 1 : 2}</div>
      </Box>
      <Box t={t} x={744} y={92} w={392} h={300} pad="10px 18px" opacity={io(f, [40, 48], [0, 1])}>
        <div style={{ ...kicker(t), marginBottom: 6 }}>scorecard 0–3 · {f < 204 ? "v001" : "v002"}</div>
        {SCORES.map(([label, s1, s2], i) => {
          const at = 46 + i * 6;
          const score = s1 + (s2 - s1) * r2;
          const flagged = s1 < 2 && r2 < 0.5;
          return (
            <div key={label} style={{ display: "flex", alignItems: "center", height: 36, opacity: io(f, [at, at + 8], [0, 1]) }}>
              <span style={sans(15, flagged && f >= 90 ? t.bad : t.ink, { flex: 1 })}>{label}</span>
              {[0, 1, 2].map((d) => (
                <div
                  key={d}
                  style={{
                    width: 13,
                    height: 13,
                    borderRadius: 7,
                    marginLeft: 6,
                    border: `1.5px solid ${flagged ? t.bad : t.glyph}`,
                    background: interpolateColors(Math.max(0, Math.min(1, score - d)), [0, 1], [t.panel, flagged ? t.bad : t.accent]),
                  }}
                />
              ))}
              <span style={mono(14, t.ink, { width: 22, textAlign: "right" })}>{Math.round(score)}</span>
            </div>
          );
        })}
      </Box>
      <At x={744} y={402} o={io(f, [90, 100], [0, 1]) * (1 - io(f, [204, 212], [0, 1]))}>
        <span style={mono(15, t.bad)}>composition 1 &lt; 2 · avg 2.14 → fix first</span>
      </At>
      <At x={744} y={402} o={io(f, [222, 232], [0, 1])}>
        <span style={mono(15, t.good)}>every ≥ 2 ✓ · avg 2.43 ≥ 2.3 ✓ → show v002</span>
      </At>
      <At x={744} y={428} o={io(f, [226, 234], [0, 1])}>
        <span style={sans(15, t.muted)}>each round logged in 3D.md</span>
      </At>
      <Caption t={t} a={12} b={172}>
        Before you see it, a <B t={t}>fresh critic</B> — never told what was fixed — scores the captures.
      </Caption>
      <Caption t={t} a={176} b={dur - 2}>
        It flags <B t={t}>subject on edge</B>. The fix is a new version, re-captured, re-scored — then shown.
      </Caption>
    </Shell>
  );
};

// ---------- S09 approve (the user's note becomes v003) ----------

const Approve: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const cw = 696;
  const ch = 196;
  const pw = Math.round((ch * 16) / 9);
  const left = (cw - pw) / 2;
  // pin on the rim of the S01 framing: viewBox point -> canvas fraction (what the viewer posts)
  const g = puckGeometry("S01", "v2");
  const vx = g.cx + g.rx * 0.6;
  const vy = g.cy - g.rx * 0.34 * 0.8;
  const px = left + (vx / 320) * pw;
  const py = (vy / 180) * ch;
  const pin = `@(${(px / cw).toFixed(2)},${(py / ch).toFixed(2)})`;
  const split = f >= 122;
  const wipe = io(f, [122, 150], [0.2, 0.5]);
  const NOTE = "rim too thin — match the clip";
  const press = (at: number) => (f >= at && f < at + 6 ? "inset 0 2px 0 rgba(0,0,0,.25)" : "none");
  return (
    <Shell t={t} dur={dur} title="your note becomes v003">
      <Box t={t} x={64} y={92} w={cw} h={ch + 34} pad="0">
        <ViewerHead t={t} version={split ? "v003" : "v002"} vs={split ? "v002" : "—"} active={0} shots={!split} />
        {split ? <div style={{ position: "absolute", right: 12, top: 8, ...mono(13, t.accent, { opacity: io(f, [122, 130], [0, 1]) }) }}>Version A/B split</div> : null}
        <div style={{ position: "absolute", left: 0, top: 34, width: cw, height: ch, background: CANVAS_DARK, overflow: "hidden" }}>
          <div style={{ position: "absolute", left, top: 0 }}>
            <Puck t={t} look="v2" framing="S01" w={pw} h={ch} bg={false} />
          </div>
          {split ? (
            <div style={{ position: "absolute", inset: 0, clipPath: `inset(0 0 0 ${wipe * 100}%)`, opacity: io(f, [122, 128], [0, 1]) }}>
              <div style={{ position: "absolute", left, top: 0 }}>
                <Puck t={t} look="v3" framing="S01" w={pw} h={ch} bg={false} />
              </div>
            </div>
          ) : null}
          {split ? <div style={{ position: "absolute", top: 0, bottom: 0, left: wipe * cw - 1, width: 2, background: t.accent, opacity: io(f, [122, 128], [0, 1]) }} /> : null}
          {split ? (
            <>
              <span style={{ position: "absolute", left: 12, bottom: 8, ...mono(13, REF.text) }}>v002</span>
              <span style={{ position: "absolute", right: 12, bottom: 8, ...mono(13, REF.text) }}>v003</span>
            </>
          ) : null}
          <div
            style={{
              position: "absolute",
              left: px - 11,
              top: py - 11,
              width: 22,
              height: 22,
              borderRadius: 11,
              background: t.accent,
              color: t.accentInk,
              display: "grid",
              placeItems: "center",
              ...mono(13, t.accentInk, { fontWeight: 700 }),
              opacity: io(f, [8, 14], [0, 1]) * (1 - io(f, [118, 124], [0, 1])),
              scale: String(io(f, [8, 18], [1.4, 1])),
              border: "2px solid rgba(0,0,0,.4)",
            }}
          >
            1
          </div>
          {f >= 174 ? (
            <div style={{ position: "absolute", right: 16, top: 14 }}>
              <Stamp f={f} at={174} color={t.good} size={18}>
                v003 · approved
              </Stamp>
            </div>
          ) : null}
        </div>
      </Box>
      <Box t={t} x={64} y={334} w={cw} h={112} pad="10px 14px">
        <div style={{ display: "flex", gap: 14, ...sans(15, t.muted), marginBottom: 6 }}>
          <span>
            Notes · version <b style={{ color: t.ink }}>{split ? "v003" : "v002"}</b> · shot <b style={{ color: t.ink }}>S01</b>
          </span>
          <span style={{ marginLeft: "auto", ...mono(13, t.muted) }}>Pin mode (P) · pin at {pin.slice(1)}</span>
        </div>
        <div style={{ height: 30, border: `1.5px solid ${t.line}`, borderRadius: 6, background: t.codeBg, padding: "4px 8px", ...mono(14, t.ink) }}>
          {split ? "" : typed(f, 18, 40, NOTE)}
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <Chip t={t} size={13} color={t.accent} style={{ boxShadow: press(42), padding: "2px 10px" }}>
            Send note
          </Chip>
          <Chip t={t} size={13} color={t.good} style={{ boxShadow: press(174), padding: "2px 10px", background: f >= 174 ? t.codeBg : t.panel }}>
            Approve version
          </Chip>
          <Chip t={t} size={13} color={t.amber} style={{ boxShadow: press(40), padding: "2px 10px", background: f >= 40 && !split ? t.codeBg : t.panel }}>
            Needs changes
          </Chip>
        </div>
      </Box>
      <Box t={t} x={780} y={92} w={356} h={354} code pad="10px 14px">
        <Cmd t={t} f={f} a={46} b={52} size={13.5} cmd="preview feedback" />
        <Out t={t} f={f} at={52} size={13.5} color={t.ink}>
          == v002  status: <span style={{ color: t.amber }}>changes</span>
        </Out>
        <Out t={t} f={f} at={54} size={13.5} color={t.ink}>
          {"  [S01]"}
        </Out>
        <Out t={t} f={f} at={56} size={13.5} color={t.ink}>
          {`    f0001 ${pin} <changes>`}
        </Out>
        <Out t={t} f={f} at={58} size={13.5} color={t.ink}>
          {`      ${NOTE}`}
        </Out>
        <div style={{ height: 8 }} />
        <Cmd t={t} f={f} a={108} b={114} size={13.5} cmd="preview new-version" />
        <Out t={t} f={f} at={112} size={13.5} color={t.ink}>
          {'  --note "wider rim (f0001)"'}
        </Out>
        <Out t={t} f={f} at={118} size={13.5}>
          {'{"version": "v003", …}'}
        </Out>
        <div style={{ height: 8 }} />
        <Cmd t={t} f={f} a={152} b={158} size={13.5} cmd="preview diff v002 v003" />
        <Out t={t} f={f} at={158} size={13.5} color={t.ink}>
          ssim S01 0.951 · S02 0.932 · S03 0.962
        </Out>
        <Out t={t} f={f} at={160} size={13}>
          0.90–0.98 = visible local change
        </Out>
      </Box>
      <Caption t={t} a={10} b={106}>
        You pin a note on the shot; it maps to <B t={t}>exactly one change</B>.
      </Caption>
      <Caption t={t} a={110} b={dur - 2}>
        That change becomes <B t={t}>v003</B>: A/B against v002, a diff, and the loop ends when you approve.
      </Caption>
    </Shell>
  );
};

// ---------- S10 record ----------

const LOG: [string, string, string, string, string, string][] = [
  ["v001", "greybox + look B", "—", "evidence/v001/", "r1 fail 2.14 · D1 subject on edge", "changes"],
  ["v002", "recentre subject", "D1", "evidence/v002/", "r2 pass 2.43", "changes"],
  ["v003", "wider rim", "f0001", "evidence/v003/", "r3 pass", "approved"],
];

const Record: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const row = (i: number) => io(f, [26 + i * 9, 34 + i * 9], [0, 1]);
  const head: React.CSSProperties = { ...sans(15, t.accent, { fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }), marginTop: 10, marginBottom: 4 };
  const cols = [60, 150, 60, 130, 330, 80];
  return (
    <Shell t={t} dur={dur} title="the record: 3D.md">
      <Box t={t} x={130} y={90} w={940} h={300} pad="12px 22px" opacity={io(f, [8, 22], [0, 1])}>
        <div style={mono(21, t.ink)}>
          <span style={{ color: t.amber, fontSize: 17 }}>▤ </span>3D.md
        </div>
        <div style={{ opacity: row(0) }}>
          <div style={head}>Decisions</div>
          <div style={mono(13.5, t.ink)}>1 · Pipeline · SCROLL world, live R3F · copy synced to chapters</div>
        </div>
        <div style={{ opacity: row(1) }}>
          <div style={head}>Budgets</div>
          <div style={mono(13.5, t.ink)}>
            hero desktop · ≤ 100k tris · ≤ 3 MB GLB · textures ≤ 1024 px · ≤ 300 draw calls
          </div>
          <div style={mono(13.5, t.good, { marginTop: 2 })}>measured: 84,210 tris · 1.90 MB · glb-report PASS</div>
        </div>
        <div style={{ opacity: row(2) }}>
          <div style={head}>Version log</div>
          <div style={{ display: "flex", ...sans(13.5, t.muted) }}>
            {["Version", "Change", "Notes", "Evidence", "Critic round", "Status"].map((h, i) => (
              <span key={h} style={{ width: cols[i] }}>
                {h}
              </span>
            ))}
          </div>
        </div>
        {LOG.map((r, i) => (
          <div key={r[0]} style={{ display: "flex", opacity: row(3 + i), height: 22, alignItems: "center" }}>
            {r.map((c, k) => (
              <span
                key={k}
                style={mono(13.5, k === 5 ? (c === "approved" ? t.good : t.amber) : k === 4 && c.includes("fail") ? t.bad : t.ink, { width: cols[k], overflow: "hidden" })}
              >
                {c}
              </span>
            ))}
          </div>
        ))}
      </Box>
      <At x={130} y={406}>
        <div style={{ display: "flex", gap: 16 }}>
          <Cmd t={t} f={f} a={70} b={76} size={15} cmd="preview stop" />
          <Out t={t} f={f} at={78} size={15}>
            preview: stopped pid 41872 (port 4173)
          </Out>
        </div>
      </At>
      <Caption t={t} a={12} b={dur - 2}>
        Approved means <B t={t}>recorded</B>: decisions, budgets and every version in 3D.md — and the server stopped.
      </Caption>
    </Shell>
  );
};

// ---------- S11 router ----------

const LANES = ["Debug a broken scene", "Add or change one thing", "Build a new 3D piece end to end", "Blender asset", "Review and iterate"];
const GROUPS: [string, string[]][] = [
  ["Front door", ["intake-grill", "intake-references", "refspec", "refspec-mapping", "brief-spec", "brief-lexicon", "brief-approach"]],
  ["Shared", ["shared-preflight", "shared-debug", "shared-performance", "shared-preview", "shared-verification"]],
  ["three.js, R3F, shaders", ["threejs-renderer", "threejs-r3f-next", "threejs-lookdev", "threejs-loading", "threejs-postfx", "threejs-interaction", "shader-glsl", "shader-tsl"]],
  ["Scroll, design, assets", ["scroll-conductor", "scroll-video", "scroll-adapters", "design-art-direction", "design-lookdev-presets", "asset-acquire", "asset-pipeline"]],
  ["Blender", ["blender-channels", "blender-modeling", "blender-lookdev-render", "blender-export", "blender-version-traps"]],
  ["Optional", ["spline", "splats-xr", "cad-print", "SOURCES"]],
];
const ROUTE = ["shared-debug", "threejs-renderer", "shared-verification"];

const Router: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const dim = io(f, [142, 162], [1, 0.5]);
  const lane = io(f, [136, 146], [0, 1]);
  return (
    <Shell t={t} dur={dur} title="a router, not a library">
      <At x={64} y={92} o={io(f, [4, 12], [0, 1])}>
        <div style={kicker(t)}>SKILL.md · lanes</div>
      </At>
      {LANES.map((l, i) => {
        const at = 6 + i * 5;
        const me = i === 0;
        return (
          <Box
            key={l}
            t={t}
            x={64}
            y={116 + i * 46}
            w={250}
            h={38}
            pad="7px 12px"
            border={me ? interpolateColors(lane, [0, 1], [t.line, t.accent]) : t.line}
            opacity={io(f, [at, at + 8], [0, 1])}
            style={{ background: me ? interpolateColors(lane, [0, 1], [t.panel, t.codeBg]) : t.panel }}
          >
            <span style={sans(15, me ? interpolateColors(lane, [0, 1], [t.ink, t.accent]) : t.ink, { fontWeight: me && lane > 0.5 ? 600 : 400 })}>{l}</span>
          </Box>
        );
      })}
      <At x={64} y={354} o={lane}>
        <Chip t={t} color={t.accent} size={14}>
          &quot;black R3F scene&quot;
        </Chip>
      </At>
      <At x={64} y={390} o={io(f, [168, 176], [0, 1])}>
        <span style={mono(16, t.accent, { fontWeight: 600 })}>3 of 36 loaded</span>
      </At>
      {GROUPS.map(([name, files], g) => {
        const at = 32 + g * 8;
        // column widths sized so the longest names wrap into at most five rows
        const col = g % 3;
        const x = [330, 608, 832][col];
        const w = [268, 214, 304][col];
        const y = 88 + Math.floor(g / 3) * 182;
        return (
          <Box key={name} t={t} x={x} y={y} w={w} h={174} pad="8px 9px" opacity={io(f, [at, at + 10], [0, 1])}>
            <div style={{ ...sans(15, t.ink, { fontWeight: 600 }), marginBottom: 6 }}>
              {name} <span style={{ color: t.muted, fontWeight: 400 }}>{files.length}</span>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {files.map((file) => {
                const k = ROUTE.indexOf(file);
                const lit = k >= 0 ? io(f, [142 + k * 10, 150 + k * 10], [0, 1]) : 0;
                return (
                  <span
                    key={file}
                    style={{
                      position: "relative",
                      ...mono(13, interpolateColors(lit, [0, 1], [t.ink, t.accent])),
                      border: `1.2px solid ${interpolateColors(lit, [0, 1], [t.line, t.accent])}`,
                      borderRadius: 6,
                      padding: "1px 5px",
                      opacity: k >= 0 ? 1 : dim,
                      fontWeight: lit > 0.5 ? 600 : 400,
                    }}
                  >
                    {file}
                    {k >= 0 ? (
                      <span
                        style={{
                          position: "absolute",
                          top: -10,
                          right: -9,
                          width: 19,
                          height: 19,
                          borderRadius: 10,
                          background: t.accent,
                          ...mono(13, t.accentInk, { fontWeight: 700 }),
                          display: "grid",
                          placeItems: "center",
                          opacity: lit,
                        }}
                      >
                        {k + 1}
                      </span>
                    ) : null}
                  </span>
                );
              })}
            </div>
          </Box>
        );
      })}
      <At x={64} y={420} o={io(f, [82, 92], [0, 1])}>
        <span style={mono(13.5, t.ink)}>
          36 references <span style={{ color: t.muted }}>· none preloaded</span>
        </span>
      </At>
      <Caption t={t} a={12} b={132}>
        SKILL.md is a <B t={t}>router</B>: 36 references in six areas, and none of them preloaded.
      </Caption>
      <Caption t={t} a={136} b={dur - 2}>
        A lane picks the files. A <B t={t}>black R3F scene</B> loads three of the 36 — debug, renderer, verification.
      </Caption>
    </Shell>
  );
};

// ---------- S12 preflight ----------

const Preflight: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const tools: [string, boolean][] = [
    ["blender", true],
    ["gltf-transform", true],
    ["ffmpeg", true],
    ["playwright + Chrome", true],
    ["ktx", false],
  ];
  return (
    <Shell t={t} dur={dur} title="preflight: detect, then propose">
      <Box t={t} x={64} y={92} w={1072} h={104} code pad="10px 18px">
        <Cmd t={t} f={f} a={6} b={18} cmd="<skill>/scripts/capabilities" />
        <Out t={t} f={f} at={20} color={t.ink}>
          capabilities: 11/14 tools found; wrote &lt;project&gt;/.3d/capabilities.md<span style={{ color: t.glyph }}>   # example run</span>
        </Out>
        <Out t={t} f={f} at={28} color={t.amber}>
          {"  propose: ktx missing (KTX2 textures): KTX-Software release .pkg … [free]"}
        </Out>
      </Box>
      <At x={64} y={212}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {tools.map(([n, ok], i) => (
            <span key={n} style={{ opacity: io(f, [38 + i * 4, 44 + i * 4], [0, 1]) }}>
              <Chip t={t} color={ok ? t.good : t.amber} size={14}>
                {n} {ok ? "✓" : "—"}
              </Chip>
            </span>
          ))}
          <span style={{ ...sans(15, t.muted), marginLeft: 10, opacity: io(f, [52, 58], [0, 1]) }}>stack: next · three · R3F · motion</span>
        </div>
      </At>
      <Box t={t} x={64} y={262} w={1072} h={96} pad="14px 18px" opacity={io(f, [62, 80], [0, 1])}>
        <div style={mono(15, t.ink)}>
          <span style={{ color: t.accent }}>Q1</span> ktx &gt;= 4.4 (<span style={{ color: t.good }}>free</span>): KTX2 textures. Release .pkg from KhronosGroup/KTX-Software (user runs the sudo installer)
        </div>
        <div style={mono(15, t.muted, { marginTop: 6 })}>{"   No: WebP/JPEG textures, larger download."}</div>
      </Box>
      <At x={64} y={378} o={io(f, [84, 92], [0, 1])}>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <span style={{ ...mono(15, t.amber, { fontWeight: 600 }), border: `1.5px solid ${t.amber}`, borderRadius: 999, padding: "4px 14px" }}>waiting for your yes · nothing installed</span>
          <span style={sans(15, t.muted)}>cost labels: free · free-account · PAID</span>
        </div>
      </At>
      <At x={64} y={424} o={io(f, [84, 92], [0, 1])}>
        <span style={mono(14, t.ink)}>
          <span style={{ color: t.muted }}>{"<skill>/scripts/  "}</span>capabilities · ref-extract · spec-check · glb-report · preview
          <span style={{ color: t.muted, fontFamily: SANS }}>{"   run by path from your project root"}</span>
        </span>
      </At>
      <Caption t={t} a={12} b={dur - 2}>
        Preflight detects tools and stack, proposes every install in <B t={t}>one round with its cost</B>, and never installs unasked.
      </Caption>
    </Shell>
  );
};

// ---------- S13 scroll ----------

const Scroll: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  const node = (i: number) => io(f, [24 + i * 9, 32 + i * 9], [0, 1]);
  const arrow = (i: number) => (
    <span style={{ ...mono(17, t.glyph), opacity: node(i) }}>→</span>
  );
  // two quadratic legs through S01 -> S02 -> S03; u = 0.62 is chapter position 1.24 (leg 2, t 0.24)
  const P = [
    [170, 404],
    [560, 300],
    [1020, 392],
  ];
  const C1 = [330, 300];
  const C2 = [800, 300];
  const q = (a: number[], c: number[], b: number[], s: number) => [
    (1 - s) ** 2 * a[0] + 2 * (1 - s) * s * c[0] + s * s * b[0],
    (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * c[1] + s * s * b[1],
  ];
  const cam = q(P[1], C2, P[2], 0.24);
  const draw = io(f, [88, 104], [1, 0]);
  const barX = 140;
  const barW = 920;
  return (
    <Shell t={t} dur={dur} title="scroll inside the pin">
      <Box t={t} x={64} y={88} w={1072} h={360} dashed pad="8px 14px" opacity={io(f, [8, 20], [0, 1])} style={{ background: "transparent" }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={kicker(t)}>the pin — scroll-animation owns it when installed</span>
          <span style={kicker(t, t.accent)}>3d owns what&apos;s inside</span>
        </div>
      </Box>
      <At x={92} y={128}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ opacity: node(0) }}>
            <Chip t={t} size={14}>
              scroll authority
            </Chip>
          </span>
          {arrow(1)}
          <div style={{ display: "flex", flexDirection: "column", gap: 3, opacity: node(1) }}>
            {["native.ts", "motion.ts", "gsap.ts"].map((a, i) => {
              const lit = i === 1 ? io(f, [70, 76], [0, 1]) : 0;
              return (
                <span key={a} style={{ opacity: io(f, [62 + i * 4, 68 + i * 4], [0.3, 1]) }}>
                  <Chip t={t} size={13.5} color={interpolateColors(lit, [0, 1], [t.muted, t.accent])} style={{ padding: "1px 10px" }}>
                    adapters/{a}
                  </Chip>
                </span>
              );
            })}
          </div>
          {arrow(2)}
          <span style={{ opacity: node(2) }}>
            <Chip t={t} size={16} color={t.accent} style={{ fontWeight: 600, padding: "8px 16px" }}>
              conductor
            </Chip>
          </span>
          {arrow(3)}
          <div style={{ ...mono(14, t.ink, { lineHeight: 1.5 }), opacity: io(f, [76, 86], [0, 1]) }}>
            {"{ exact · smooth · position\n  index · direction · reduced }"}
          </div>
          {arrow(3)}
          <span style={{ opacity: io(f, [80, 86], [0, 1]) }}>
            <Chip t={t} size={14}>
              camera · world · DOM
            </Chip>
          </span>
        </div>
      </At>
      <div style={{ position: "absolute", left: barX, top: 250, width: barW, height: 6, borderRadius: 3, background: t.codeBg, border: `1px solid ${t.line}`, opacity: io(f, [88, 96], [0, 1]) }} />
      {(
        [
          ["exact 0.62", "logic: nav, gating", 0.62, t.ink, -1],
          ["smooth 0.58", "visuals only", 0.58, t.accent, 1],
        ] as [string, string, number, string, number][]
      ).map(([label, sub, v, c, side]) => (
        <div key={label} style={{ position: "absolute", left: barX + v * barW - 1, top: 238, opacity: io(f, [94, 104], [0, 1]) }}>
          <div style={{ width: 3, height: 30, background: c, borderRadius: 2 }} />
          <div
            style={{
              position: "absolute",
              top: -2,
              ...(side < 0 ? { left: 10 } : { right: 10 }),
              whiteSpace: "nowrap",
              ...mono(13.5, c),
            }}
          >
            {label} <span style={{ color: t.muted, fontFamily: SANS }}>{sub}</span>
          </div>
        </div>
      ))}
      <svg style={{ position: "absolute", left: 0, top: 0 }} width={1200} height={520}>
        <path
          d={`M ${P[0][0]} ${P[0][1]} Q ${C1[0]} ${C1[1]} ${P[1][0]} ${P[1][1]} Q ${C2[0]} ${C2[1]} ${P[2][0]} ${P[2][1]}`}
          fill="none"
          stroke={t.glyph}
          strokeWidth={2}
          strokeDasharray="1200"
          strokeDashoffset={1200 * draw}
        />
        {P.map(([x, y], i) => (
          <g key={i} opacity={io(f, [90 + i * 4, 98 + i * 4], [0, 1])}>
            <circle cx={x} cy={y} r={7} fill={t.panel} stroke={t.ink} strokeWidth={2} />
            <text x={x} y={y + 26} textAnchor="middle" fontFamily={MONO} fontSize={13.5} fill={t.ink}>
              S0{i + 1}
            </text>
          </g>
        ))}
        <g opacity={io(f, [98, 104], [0, 1])}>
          <circle cx={cam[0]} cy={cam[1]} r={9} fill={t.accent} />
          <text x={cam[0]} y={cam[1] + 30} textAnchor="middle" fontFamily={MONO} fontSize={13} fill={t.accent}>
            camera · position 1.24
          </text>
        </g>
      </svg>
      <At x={420} y={420} o={io(f, [96, 104], [0, 1])}>
        <span style={sans(15, t.muted)}>one authority per route · smoothed once · values are an example</span>
      </At>
      <Caption t={t} a={12} b={118}>
        Inside the pin, <B t={t}>one conductor</B> turns scroll into the state the scene reads.
      </Caption>
      <Caption t={t} a={122} b={dur - 2}>
        Adapters feed it from native, Motion or GSAP. Logic reads <B t={t}>exact</B>; visuals read <B t={t}>smooth</B>.
      </Caption>
    </Shell>
  );
};

// ---------- S14 outputs + adjacent skills ----------

const TREE: [string, string][] = [
  ["3D.md", "decisions · budgets · version log"],
  [".3d/", ""],
  ["  capabilities.md", "tools, stack, proposals"],
  ["  questions.md", "open questions, no live user"],
  ["  brief.md · shots.json · look.json", ""],
  ["  refs/<name>/ · reference-spec.json", ""],
  ["  versions/vNNN/", "never edited once shown"],
  ["  evidence/vNNN/ · diffs/ · boards/", ""],
  ["  feedback.jsonl", "append-only notes"],
];
const ADJ = ["scroll-animation", "fluid-design", "generate-image", "generate-video", "manufacturing-workflow", "frontend"];

const Outputs: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  return (
    <Shell t={t} dur={dur} title="where everything lands">
      <Box t={t} x={64} y={92} w={600} h={352} code pad="14px 20px">
        {TREE.map(([p, d], i) => {
          const at = 8 + i * 6;
          return (
            <div key={p} style={{ display: "flex", alignItems: "baseline", height: 32, opacity: io(f, [at, at + 8], [0, 1]) }}>
              <span style={mono(15, i < 2 ? t.ink : t.ink, { width: 330, fontWeight: i < 2 ? 600 : 400 })}>
                {i < 2 ? <span style={{ color: t.amber }}>{i === 0 ? "▤ " : "▸ "}</span> : null}
                {p}
              </span>
              <span style={sans(15, t.muted)}>{d}</span>
            </div>
          );
        })}
        <div style={{ ...sans(15, t.muted), marginTop: 8, opacity: io(f, [62, 68], [0, 1]) }}>suggest gitignoring .3d/versions and .3d/refs</div>
      </Box>
      <Box t={t} x={688} y={92} w={448} h={352} pad="14px 20px" opacity={io(f, [70, 78], [0, 1])}>
        <div style={{ ...kicker(t), marginBottom: 14 }}>adjacent skills</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {ADJ.map((s, i) => (
            <span key={s} style={{ opacity: io(f, [76 + i * 5, 84 + i * 5], [0, 1]) }}>
              <Chip t={t} dashed size={15} style={{ background: "transparent" }}>
                {s}
              </Chip>
            </span>
          ))}
        </div>
        <div style={{ ...mono(16, t.accent, { fontWeight: 600 }), marginTop: 26, opacity: io(f, [104, 112], [0, 1]) }}>recommended, never invoked</div>
        <div style={{ ...sans(15, t.muted), marginTop: 8, opacity: io(f, [104, 112], [0, 1]) }}>2D scroll, layout scaling, image and video generation, print — each named in the handoff</div>
      </Box>
      <Caption t={t} a={12} b={124}>
        Everything lands in files: <B t={t}>3D.md</B> at the root, the working state in <B t={t}>.3d/</B>.
      </Caption>
      <Caption t={t} a={128} b={dur - 2}>
        Neighbouring work goes to adjacent skills — <B t={t}>recommended, never invoked</B>.
      </Caption>
    </Shell>
  );
};

// ---------- S15 close ----------

const Close: React.FC<{ t: Theme; dur: number }> = ({ t, dur }) => {
  const f = useCurrentFrame();
  return (
    <Shell t={t} dur={dur} out={12}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", textAlign: "center" }}>
        <div style={{ ...mono(32, t.ink, { letterSpacing: "-0.01em" }), opacity: io(f, [8, 26], [0, 1]) }}>nothing is built before it is measured</div>
        <div style={{ ...mono(32, t.ink, { letterSpacing: "-0.01em" }), marginTop: 12, opacity: io(f, [30, 48], [0, 1]) }}>nothing is called done before it is captured</div>
        <div style={{ ...sans(20, t.muted), marginTop: 22, opacity: io(f, [52, 64], [0, 1]) }}>
          a measured spec · an approved brief · versions you sign off · one record in 3D.md
        </div>
        <div style={{ ...mono(24, t.accent, { fontWeight: 600 }), marginTop: 28, opacity: io(f, [66, 78], [0, 1]) }}>
          npx skills add gabros20/3d-skill -g -y
        </div>
        <div style={{ ...mono(17, t.accent), marginTop: 10, opacity: io(f, [66, 78], [0, 1]) }}>then /3d or $3d</div>
      </AbsoluteFill>
    </Shell>
  );
};

// ---------- timeline ----------

// One source of truth. start = previous end − 8 (overlap). Mirror into site/index.html PLAYER-META
// data-chapters (start / 30 s) and the storyboard's §2 when anything moves.
type SceneDef = { id: string; start: number; dur: number; act: 0 | 1 | 2; chapter: string; C: React.FC<{ t: Theme; dur: number }> };
const DEFS: SceneDef[] = [
  { id: "request", start: 0, dur: 126, act: 1, chapter: "The request", C: Request },
  { id: "measure", start: 118, dur: 356, act: 1, chapter: "Measure the reference", C: Measure },
  { id: "grill", start: 466, dur: 290, act: 1, chapter: "Grill only the gaps", C: Grill },
  { id: "brief", start: 748, dur: 268, act: 1, chapter: "Brief, shots, gates", C: Brief },
  { id: "approach", start: 1008, dur: 264, act: 1, chapter: "Pick the pipeline", C: Approach },
  { id: "build", start: 1264, dur: 280, act: 1, chapter: "Build", C: Build },
  { id: "preview", start: 1536, dur: 288, act: 1, chapter: "Preview every shot", C: Preview },
  { id: "critic", start: 1816, dur: 402, act: 1, chapter: "A fresh critic", C: Critic },
  { id: "approve", start: 2210, dur: 354, act: 1, chapter: "Your note, v003, approved", C: Approve },
  { id: "record", start: 2556, dur: 252, act: 1, chapter: "The record", C: Record },
  { id: "router", start: 2800, dur: 344, act: 2, chapter: "A router, not a library", C: Router },
  { id: "preflight", start: 3136, dur: 260, act: 2, chapter: "Preflight", C: Preflight },
  { id: "scroll", start: 3388, dur: 272, act: 2, chapter: "Scroll inside the pin", C: Scroll },
  { id: "outputs", start: 3652, dur: 280, act: 2, chapter: "Where everything lands", C: Outputs },
  { id: "close", start: 3924, dur: 210, act: 0, chapter: "Measured, then captured", C: Close },
];

// The same component is placed on a Track below and registered standalone in Root.tsx
// (remotion-markup/connected-compositions.md); its own background lets it open on its own.
export type SceneProps = { readonly theme: ThemeName; readonly dur: number };
const connect = (id: string, Inner: React.FC<{ t: Theme; dur: number }>) => {
  const SceneInner: React.FC<SceneProps> = ({ theme, dur }) => <Inner t={themes[theme]} dur={dur} />;
  return Interactive.create({
    Component: SceneInner,
    componentName: `${id[0].toUpperCase()}${id.slice(1)}Scene`,
    layout: "absolute-fill",
  });
};
export const SCENES = DEFS.map((d) => ({ ...d, Scene: connect(d.id, d.C) }));
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
      <span style={{ position: "absolute", left: 64, top: 4, ...kicker(t, t.accent) }}>{act === 1 ? "Act 1 · life of a 3D task" : "Act 2 · the pack"}</span>
      <div style={{ position: "absolute", left: 300, right: 64, top: 3, display: "flex", justifyContent: act === 1 ? "space-between" : "flex-start", gap: act === 1 ? 0 : 40 }}>
        {stations.map((s) => (
          <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 7, height: 7, borderRadius: 4, background: mix(dotFill, s.i), border: `1.5px solid ${mix(dotLine, s.i)}` }} />
            <span style={mono(13, mix(label, s.i))}>{s.id}</span>
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
        {SCENES.filter((_, i) => i % 2 === k).map(({ id, start, dur, Scene }) => (
          <Scene key={id} name={id} from={start} durationInFrames={dur} theme={theme} dur={dur} />
        ))}
      </Track>
    ))}
    <Track name="Rail">
      <Rail name="chapter rail" from={0} durationInFrames={RAIL_END} theme={theme} />
    </Track>
  </>
);
