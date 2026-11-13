import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "./theme";

const ROWS: [string, string, string, string][] = [
  ["Part 1A", "SplitKaro harness", "PASS · 6/6 gates", C.green],
  ["", "", "107/107 tests · 96.8 % coverage · 40/40 ACs traced", C.green],
  ["Part 1B", "TxnSense evaluation", "PASS · 25/25 cases", C.peach],
  ["", "", "100 % schema-valid · 0 violations · safety 7/7 · score 0.98", C.peach],
  ["New data", "Acceptance test", "SplitKaro 16/16 · TxnSense 11/11 · 0 leaks", C.mauve],
];

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: C.base, fontFamily: FONT, color: C.text, padding: "100px 120px" }}>
      <div style={{ fontSize: 84, fontWeight: 900 }}>Results</div>
      <div style={{ marginTop: 50, display: "flex", flexDirection: "column", gap: 18 }}>
        {ROWS.map(([part, what, result, color], i) => {
          const s = spring({ frame: frame - i * 8, fps, config: { damping: 200 } });
          return (
            <div key={i} style={{ display: "grid", gridTemplateColumns: "210px 430px 1fr", alignItems: "center", columnGap: 36, opacity: s, transform: `translateX(${interpolate(s, [0, 1], [40, 0])}px)` }}>
              <div style={{ fontFamily: MONO, fontSize: 32, color, fontWeight: 800 }}>{part}</div>
              <div style={{ fontSize: 38, color: C.subtext }}>{what}</div>
              <div style={{ fontSize: 40, fontWeight: 600 }}>{result}</div>
            </div>
          );
        })}
      </div>
      <div
        style={{
          marginTop: 56, padding: "32px 40px", borderRadius: 22, background: C.surface,
          borderLeft: `10px solid ${C.yellow}`, fontSize: 40, lineHeight: 1.35,
          opacity: interpolate(frame, [50, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        Evidence, harness logs and known limitations are in the repository. The final <b style={{ color: C.yellow }}>ACCEPT / REJECT</b> is the engineer's decision.
      </div>
      <div style={{ position: "absolute", bottom: 90, left: 120, fontFamily: MONO, fontSize: 34, color: C.blue }}>
        github.com/RahulNAImp/assignment1_expense_split
      </div>
    </AbsoluteFill>
  );
};
