import React, { createContext, useContext } from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";

// Beat start times (seconds) for the current scene; slides reveal step i at beat i.
export const BeatCtx = createContext<number[]>([0]);

export const useBeat = () => {
  const beats = useContext(BeatCtx);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  let idx = 0;
  beats.forEach((b, i) => {
    if (t >= b + 0.15) idx = i;
  });
  return { idx, beats, frame, fps };
};

// Fade/slide-in when beat `at` starts (plus optional delay in seconds).
export const Reveal: React.FC<{ at: number; delay?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  at, delay = 0, children, style,
}) => {
  const { beats, frame, fps } = useBeat();
  const start = ((beats[at] ?? 0) + delay) * fps;
  const s = spring({ frame: frame - start, fps, config: { damping: 200 } });
  return (
    <div style={{ opacity: s, transform: `translateY(${interpolate(s, [0, 1], [24, 0])}px)`, ...style }}>{children}</div>
  );
};

export const Slide: React.FC<{ kicker: string; title: string; color?: string; children: React.ReactNode }> = ({
  kicker, title, color = C.blue, children,
}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, ${C.base} 0%, ${C.crust} 100%)`, fontFamily: FONT, color: C.text, padding: "90px 120px", opacity: o }}>
      <div style={{ fontFamily: MONO, fontSize: 30, color, letterSpacing: 3 }}>{kicker}</div>
      <div style={{ fontSize: 76, fontWeight: 850, marginTop: 10, lineHeight: 1.1 }}>{title}</div>
      <div style={{ height: 6, width: 140, background: color, borderRadius: 3, marginTop: 22 }} />
      <div style={{ marginTop: 50, flex: 1 }}>{children}</div>
    </AbsoluteFill>
  );
};

export const Pill: React.FC<{ color: string; children: React.ReactNode; big?: boolean }> = ({ color, children, big }) => (
  <span style={{ background: color, color: C.base, borderRadius: 14, padding: big ? "10px 22px" : "6px 16px", fontWeight: 800, fontSize: big ? 40 : 30 }}>{children}</span>
);

export const Card: React.FC<{ children: React.ReactNode; color?: string; style?: React.CSSProperties }> = ({ children, color = C.surface, style }) => (
  <div style={{ background: C.surface, borderRadius: 24, padding: "28px 36px", borderLeft: `10px solid ${color}`, ...style }}>{children}</div>
);

export const Tick: React.FC = () => <span style={{ color: C.green, fontWeight: 900 }}>✔</span>;
