import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "./theme";

const SPEC = ["constitution", "specify", "clarify", "plan", "tasks", "analyze", "implement"];
const LOOP = ["harness", "feedback", "repair", "re-run"];

const Node: React.FC<{ label: string; at: number; color: string; big?: boolean }> = ({
  label, at, color, big,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - at, fps, config: { damping: 18, stiffness: 120 } });
  return (
    <div
      style={{
        fontFamily: MONO, fontSize: big ? 36 : 30, color: C.base, background: color,
        padding: big ? "22px 32px" : "16px 20px", borderRadius: 18, fontWeight: 700,
        opacity: interpolate(s, [0, 0.3], [0, 1], { extrapolateRight: "clamp" }),
        transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})`, whiteSpace: "nowrap",
      }}
    >
      {label}
    </div>
  );
};

const Arrow: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ fontSize: 36, color: C.overlay, opacity: interpolate(frame, [at, at + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
      →
    </div>
  );
};

export const WorkflowScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  // Spread the reveal over the first ~70 % of the narration.
  const step = Math.max(12, Math.floor((durationInFrames * 0.7) / (SPEC.length + LOOP.length + 1)));
  const loopStart = SPEC.length * step;
  const humanAt = loopStart + LOOP.length * step;
  const pulse = 0.5 + 0.5 * Math.sin((frame - loopStart) / 8);
  return (
    <AbsoluteFill style={{ background: C.base, fontFamily: FONT, color: C.text, padding: "100px 110px" }}>
      <div style={{ fontSize: 84, fontWeight: 900 }}>One workflow, both parts</div>
      <div style={{ fontSize: 40, color: C.subtext, marginTop: 12 }}>
        GitHub Spec Kit first · independent harness after · human decides last
      </div>

      <div style={{ fontFamily: MONO, fontSize: 30, color: C.mauve, marginTop: 70, letterSpacing: 2 }}>
        SPECIFICATION (before any code)
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 24 }}>
        {SPEC.map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Node label={s} at={i * step} color={i === 2 ? C.yellow : C.blue} />
            {i < SPEC.length - 1 ? <Arrow at={i * step + step / 2} /> : null}
          </div>
        ))}
      </div>

      <div style={{ fontFamily: MONO, fontSize: 30, color: C.peach, marginTop: 80, letterSpacing: 2 }}>
        VALIDATION LOOP (independent of the generated code)
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 24 }}>
        {LOOP.map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ boxShadow: frame > humanAt ? `0 0 ${30 * pulse}px ${C.peach}` : "none", borderRadius: 18 }}>
              <Node label={s} at={loopStart + i * step} color={C.peach} />
            </div>
            <Arrow at={loopStart + i * step + step / 2} />
          </div>
        ))}
        <Node label="human ACCEPT / REJECT" at={humanAt} color={C.green} big />
      </div>
      <div
        style={{
          fontSize: 34, color: C.subtext, marginTop: 50,
          opacity: interpolate(frame, [humanAt + 10, humanAt + 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        <span style={{ color: C.yellow }}>clarify</span> = student's decisions · failures go back to the agent as
        evidence · the same gates run again
      </div>
    </AbsoluteFill>
  );
};
