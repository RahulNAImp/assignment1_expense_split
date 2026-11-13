import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "./theme";

const App: React.FC<{ delay: number; tag: string; name: string; desc: string; color: string }> = ({
  delay, tag, name, desc, color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        flex: 1, background: C.surface, borderRadius: 28, padding: "40px 48px",
        borderTop: `8px solid ${color}`, opacity: s,
        transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`,
      }}
    >
      <div style={{ fontFamily: MONO, fontSize: 30, color, letterSpacing: 2 }}>{tag}</div>
      <div style={{ fontSize: 72, fontWeight: 800, color: C.text, marginTop: 8 }}>{name}</div>
      <div style={{ fontSize: 38, color: C.subtext, marginTop: 12, lineHeight: 1.3 }}>{desc}</div>
    </div>
  );
};

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const head = spring({ frame, fps, config: { damping: 200 } });
  const fade = (d: number) => interpolate(frame, [d, d + 20], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 20% 10%, ${C.surface}, ${C.base} 55%, ${C.crust})`,
        fontFamily: FONT, padding: "110px 130px", color: C.text,
      }}
    >
      <div style={{ fontFamily: MONO, fontSize: 32, color: C.mauve, opacity: fade(0), letterSpacing: 3 }}>
        AI-AUGMENTED SDLC · SE ZG534 · ASSIGNMENT 1
      </div>
      <div
        style={{
          fontSize: 104, fontWeight: 900, lineHeight: 1.05, marginTop: 24,
          opacity: head, transform: `translateY(${interpolate(head, [0, 1], [40, 0])}px)`,
        }}
      >
        Spec-Driven Development
        <br />
        <span style={{ color: C.blue }}>&amp; Harness Engineering</span>
      </div>
      <div style={{ fontSize: 44, color: C.subtext, marginTop: 36, opacity: fade(20) }}>
        Rahul Rangnath Nandanwar · 2026NS93095 · BITS Pilani WILP
      </div>
      <div style={{ display: "flex", gap: 48, marginTop: 80 }}>
        <App delay={45} tag="PART 1A · DETERMINISTIC" name="SplitKaro" color={C.green}
          desc="Group expense splitter: exact paise, deterministic settle-up" />
        <App delay={70} tag="PART 1B · NON-DETERMINISTIC" name="TxnSense" color={C.peach}
          desc="Gemini parser for bank & UPI SMS, with safety guardrails" />
      </div>
    </AbsoluteFill>
  );
};
