import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";
import { themes, MONO, SANS, type Theme, type ThemeName } from "./theme";

// Story (29s @30fps, 875f): vague prompt + reference -> refspec -> 3 questions -> brief + shots
// -> build -> versioned preview (A/B + note) -> v2 approved. Every scene is IN -> HOLD -> OUT.
const FADE = 10;
const SCENES = [
  { id: "prompt", start: 0, dur: 135 },
  { id: "spec", start: 135, dur: 155 },
  { id: "ask", start: 290, dur: 175 },
  { id: "brief", start: 465, dur: 140 },
  { id: "build", start: 605, dur: 115 },
  { id: "preview", start: 720, dur: 155 },
] as const;
const STEPS = ["prompt", "refspec", "questions", "brief", "build", "preview"];

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.2, 0.7, 0.2, 1);
const rise = (f: number, at: number, len = 10) =>
  interpolate(f, [at, at + len], [0, 1], { ...clamp, easing: ease });

const Reveal: React.FC<{ f: number; at: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ f, at, children, style }) => {
  const k = rise(f, at);
  return <div style={{ opacity: k, transform: `translateY(${(1 - k) * 8}px)`, ...style }}>{children}</div>;
};

// A stand-in "reference image": dark studio, glossy low-angle object, thin rim. Theme-independent
// (it is a photo), `rim` softens in v2.
const Art: React.FC<{ w: number; h: number; rim: number }> = ({ w, h, rim }) => (
  <div style={{ width: w, height: h, position: "relative", overflow: "hidden", background: "radial-gradient(ellipse at 60% 30%, #2a3040 0%, #0c0f16 75%)" }}>
    <div style={{ position: "absolute", left: "50%", top: "46%", width: w * 0.5, height: h * 0.46, transform: "translate(-50%,-50%)", borderRadius: "46% 46% 40% 40%", background: "linear-gradient(160deg,#4a5368 0%,#1b2030 45%,#0a0c12 100%)", boxShadow: `inset 0 ${3 + rim * 4}px 0 rgba(215,230,255,${0.25 + rim * 0.65}), 0 30px 40px -10px rgba(0,0,0,.7)` }} />
    <div style={{ position: "absolute", left: "50%", bottom: h * 0.12, width: w * 0.6, height: h * 0.06, transform: "translateX(-50%)", background: "radial-gradient(ellipse, rgba(0,0,0,.7), transparent 70%)" }} />
  </div>
);

const Shell: React.FC<{ t: Theme; children: React.ReactNode; step: number }> = ({ t, children, step }) => (
  <AbsoluteFill style={{ background: t.bg, padding: 40, fontFamily: MONO }}>
    <div style={{ flex: 1, background: t.codeBg, border: `1.5px solid ${t.line}`, borderRadius: 16, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "14px 22px", borderBottom: `1.5px solid ${t.line}`, background: t.panel }}>
        {[0, 1, 2].map((i) => <div key={i} style={{ width: 12, height: 12, borderRadius: 6, background: t.line }} />)}
        <div style={{ marginLeft: 14, color: t.muted, fontSize: 18 }}>/3d</div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {STEPS.map((s, i) => (
            <div key={s} style={{ fontSize: 15, padding: "3px 12px", borderRadius: 999, border: `1.5px solid ${i === step ? t.accent : t.line}`, color: i === step ? t.accent : t.glyph, background: t.panel, fontWeight: i === step ? 700 : 400 }}>{s}</div>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, position: "relative", padding: "36px 44px" }}>{children}</div>
    </div>
  </AbsoluteFill>
);

const Prompt: React.FC<{ t: Theme; f: number }> = ({ t, f }) => {
  const text = "make the hero feel like this, but ours";
  const n = Math.floor(interpolate(f, [4, 40], [0, text.length], clamp));
  return (
    <div style={{ display: "flex", gap: 48, alignItems: "center", height: "100%" }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 34, color: t.ink, lineHeight: 1.5 }}>
          <span style={{ color: t.accent, fontWeight: 700 }}>/3d </span>
          {text.slice(0, n)}
          <span style={{ opacity: f % 16 < 9 ? 1 : 0, color: t.accent }}>▍</span>
        </div>
        <Reveal f={f} at={34} style={{ marginTop: 22, display: "inline-flex", gap: 10, alignItems: "center", fontSize: 21, color: t.muted, background: t.panel, border: `1.5px solid ${t.line}`, borderRadius: 999, padding: "6px 16px" }}>
          <span style={{ color: t.accent }}>+</span> hero-ref.jpg
        </Reveal>
        <Reveal f={f} at={50} style={{ marginTop: 26, fontSize: 21, color: t.muted, fontFamily: SANS }}>
          A vague prompt and a reference image.
        </Reveal>
      </div>
      <Reveal f={f} at={26} style={{ border: `1.5px solid ${t.line}`, borderRadius: 12, overflow: "hidden" }}>
        <Art w={440} h={300} rim={0.8} />
      </Reveal>
    </div>
  );
};

const Spec: React.FC<{ t: Theme; f: number }> = ({ t, f }) => {
  const row = (at: number, k: string, v: string) => (
    <Reveal f={f} at={at} style={{ display: "flex", gap: 20, fontSize: 28, padding: "10px 0", borderBottom: `1.5px solid ${t.line}` }}>
      <span style={{ color: t.muted, width: 190, whiteSpace: "nowrap" }}>{k}</span>
      <span style={{ color: t.ink, fontWeight: 600 }}>{v}</span>
    </Reveal>
  );
  const sw = ["#0c0f16", "#2a3040", "#4a5368", "#d7e6ff", "#c9a36a"];
  return (
    <div style={{ display: "flex", gap: 48, alignItems: "center", height: "100%" }}>
      <div style={{ flex: 1 }}>
        <Reveal f={f} at={0} style={{ fontSize: 20, color: t.accent, marginBottom: 14 }}>.3d/reference-spec.json</Reveal>
        {row(6, "camera", "50 mm · low angle")}
        {row(16, "key light", "45° · warm")}
        <Reveal f={f} at={26} style={{ display: "flex", gap: 20, alignItems: "center", fontSize: 28, padding: "14px 0" }}>
          <span style={{ color: t.muted, width: 190, whiteSpace: "nowrap" }}>palette</span>
          <div style={{ display: "flex", gap: 10 }}>
            {sw.map((c, i) => <div key={c} style={{ width: 44, height: 44, borderRadius: 10, background: c, border: `1.5px solid ${t.line}`, opacity: rise(f, 30 + i * 3), transform: `scale(${0.7 + 0.3 * rise(f, 30 + i * 3)})` }} />)}
          </div>
        </Reveal>
        <Reveal f={f} at={46} style={{ marginTop: 14, fontSize: 21, color: t.muted, fontFamily: SANS }}>The skill measures the reference before asking anything.</Reveal>
      </div>
      <div style={{ position: "relative", border: `1.5px solid ${t.line}`, borderRadius: 12, overflow: "hidden" }}>
        <Art w={440} h={300} rim={0.8} />
        <div style={{ position: "absolute", left: 14, top: 14, fontSize: 17, color: t.accentInk, background: t.accent, borderRadius: 6, padding: "2px 8px", opacity: rise(f, 12), fontWeight: 700 }}>50 mm · low</div>
        <div style={{ position: "absolute", right: 14, top: 14, fontSize: 17, color: "#fff", background: "rgba(0,0,0,.55)", borderRadius: 6, padding: "2px 8px", opacity: rise(f, 22) }}>key 45° ↗</div>
      </div>
    </div>
  );
};

const Ask: React.FC<{ t: Theme; f: number }> = ({ t, f }) => {
  const qs: [string, string][] = [
    ["Real-time in the page, or pre-rendered?", "real-time three.js"],
    ["Where must it hold 60 fps?", "desktop and phone"],
    ["Does scroll drive it?", "no, an ambient loop"],
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%", gap: 22 }}>
      {qs.map(([q, a], i) => (
        <Reveal key={q} f={f} at={4 + i * 16} style={{ background: t.panel, border: `1.5px solid ${t.line}`, borderRadius: 12, padding: "14px 22px", display: "flex", alignItems: "center", gap: 18 }}>
          <span style={{ color: t.accent, fontWeight: 700, fontSize: 26 }}>Q{i + 1}</span>
          <span style={{ color: t.ink, fontSize: 27, flex: 1 }}>{q}</span>
          <span style={{ opacity: rise(f, 12 + i * 16), color: t.accentInk, background: t.accent, borderRadius: 999, padding: "4px 16px", fontSize: 22, fontWeight: 700 }}>{a}</span>
        </Reveal>
      ))}
      <Reveal f={f} at={56} style={{ fontSize: 21, color: t.muted, fontFamily: SANS }}>Three sharp questions, each with a recommended answer.</Reveal>
    </div>
  );
};

const Brief: React.FC<{ t: Theme; f: number }> = ({ t, f }) => {
  const shots = [["s1", "wide", "50 mm · low"], ["s2", "detail", "85 mm · rim"], ["s3", "turn", "35 mm · orbit"]];
  return (
    <div style={{ display: "flex", gap: 40, height: "100%", alignItems: "center" }}>
      <Reveal f={f} at={0} style={{ flex: 1, background: t.panel, border: `1.5px solid ${t.line}`, borderRadius: 12, padding: "20px 26px" }}>
        <div style={{ color: t.accent, fontSize: 20 }}>.3d/brief.md</div>
        <div style={{ color: t.ink, fontSize: 26, marginTop: 12, lineHeight: 1.5 }}>Matte-black product, one cool rim, slow turn.</div>
        <Reveal f={f} at={26} style={{ marginTop: 14, color: t.good, fontSize: 24, fontWeight: 700 }}>✓ approved</Reveal>
      </Reveal>
      <Reveal f={f} at={10} style={{ flex: 1, background: t.panel, border: `1.5px solid ${t.line}`, borderRadius: 12, padding: "20px 26px" }}>
        <div style={{ color: t.accent, fontSize: 20 }}>.3d/shots.json</div>
        {shots.map(([id, n, l], i) => (
          <Reveal key={id} f={f} at={16 + i * 8} style={{ display: "flex", gap: 16, fontSize: 25, marginTop: 12, color: t.ink }}>
            <span style={{ color: t.muted, width: 40 }}>{id}</span><span style={{ width: 90 }}>{n}</span><span style={{ color: t.muted }}>{l}</span>
          </Reveal>
        ))}
      </Reveal>
    </div>
  );
};

const Build: React.FC<{ t: Theme; f: number }> = ({ t, f }) => {
  const lane = (at: number, name: string, note: string) => (
    <Reveal f={f} at={at} style={{ background: t.panel, border: `1.5px solid ${t.line}`, borderRadius: 12, padding: "18px 26px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 28, color: t.ink }}>
        <span style={{ fontWeight: 700 }}>{name}</span><span style={{ color: t.muted }}>{note}</span>
      </div>
      <div style={{ marginTop: 14, height: 10, borderRadius: 5, background: t.line }}>
        <div style={{ height: 10, borderRadius: 5, background: t.accent, width: `${interpolate(f, [at + 4, at + 34], [0, 100], { ...clamp, easing: ease })}%` }} />
      </div>
    </Reveal>
  );
  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 22, height: "100%" }}>
      {lane(0, "three.js", "scene, lights, camera path")}
      {lane(6, "Blender", "model, export GLB")}
    </div>
  );
};

const Preview: React.FC<{ t: Theme; f: number }> = ({ t, f }) => {
  const v2 = f >= 60;
  const tab = (label: string, on: boolean) => (
    <span style={{ fontSize: 22, padding: "4px 18px", borderRadius: 999, border: `1.5px solid ${on ? t.accent : t.line}`, background: on ? t.accent : t.panel, color: on ? t.accentInk : t.muted, fontWeight: 700 }}>{label}</span>
  );
  return (
    <div style={{ display: "flex", gap: 44, alignItems: "center", height: "100%" }}>
      <Reveal f={f} at={0} style={{ border: `1.5px solid ${t.line}`, borderRadius: 12, overflow: "hidden", background: t.panel }}>
        <div style={{ display: "flex", gap: 10, padding: "10px 14px", borderBottom: `1.5px solid ${t.line}`, alignItems: "center" }}>
          {tab("v1", !v2)}{tab("v2", v2)}
          <span style={{ marginLeft: "auto", color: t.muted, fontSize: 18 }}>A/B</span>
        </div>
        <Art w={520} h={320} rim={v2 ? 0.15 : 0.9} />
      </Reveal>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 18 }}>
        <Reveal f={f} at={14} style={{ background: t.amberBg, border: `1.5px solid ${t.amber}`, borderRadius: 12, padding: "14px 20px", color: t.ink, fontSize: 24, lineHeight: 1.4 }}>
          <span style={{ color: t.amber, fontWeight: 700 }}>note </span>rim is too hot, pull it down
        </Reveal>
        <Reveal f={f} at={64} style={{ color: t.good, fontSize: 32, fontWeight: 700 }}>✓ v2 approved</Reveal>
      </div>
    </div>
  );
};

const Scene: React.FC<{ id: string; start: number; dur: number; t: Theme; index: number }> = ({ id, start, dur, t, index }) => {
  const abs = useCurrentFrame();
  const f = abs - start;
  if (f < -2 || f > dur) return null;
  const last = index === SCENES.length - 1;
  const o = Math.min(rise(f, 0, 6), last ? 1 : interpolate(f, [dur - FADE, dur], [1, 0], clamp));
  const body = { prompt: Prompt, spec: Spec, ask: Ask, brief: Brief, build: Build, preview: Preview }[id as "prompt"];
  const B = body;
  return (
    <AbsoluteFill style={{ opacity: o }}>
      <Shell t={t} step={index}><B t={t} f={Math.max(f, 0)} /></Shell>
    </AbsoluteFill>
  );
};

export const HeroAnimation: React.FC<{ theme: ThemeName }> = ({ theme }) => {
  const t = themes[theme];
  return (
    <AbsoluteFill style={{ background: t.bg }}>
      {SCENES.map((s, i) => <Scene key={s.id} {...s} t={t} index={i} />)}
    </AbsoluteFill>
  );
};
