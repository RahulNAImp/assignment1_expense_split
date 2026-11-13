import {
  AbsoluteFill, Freeze, interpolate, OffthreadVideo, Sequence, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { C, FONT, MONO } from "./theme";

export type ClipProps = { clip: string; clipFrames: number; tag: string; caption: string };

const TAG_COLOR: Record<string, string> = { "PART 1A": C.green, "PART 1B": C.peach, ACCEPTANCE: C.mauve };

// The terminal recording sits in a "window" under a caption bar. If the narration outlasts the
// recording, the last frame is held (Freeze) instead of going blank.
export const ClipScene: React.FC<ClipProps> = ({ clip, clipFrames, tag, caption }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 200 } });
  const video = <OffthreadVideo src={staticFile(clip)} muted />;
  const color = TAG_COLOR[tag] ?? C.blue;
  return (
    <AbsoluteFill style={{ background: C.crust, fontFamily: FONT }}>
      <div style={{ position: "absolute", top: 34, left: 80, right: 80, display: "flex", alignItems: "center", gap: 28 }}>
        <div style={{ fontFamily: MONO, fontSize: 30, fontWeight: 800, color: C.base, background: color, padding: "10px 22px", borderRadius: 12, letterSpacing: 2 }}>
          {tag}
        </div>
        <div style={{ fontSize: 46, fontWeight: 700, color: C.text, opacity: enter, transform: `translateX(${interpolate(enter, [0, 1], [-30, 0])}px)` }}>
          {caption}
        </div>
      </div>
      <div
        style={{
          position: "absolute", top: 128, left: 96, width: 1728, height: 1004 - 128 + 28,
          borderRadius: 22, overflow: "hidden", background: C.base,
          boxShadow: `0 30px 80px rgba(0,0,0,0.55), 0 0 0 2px ${C.surface}`,
          opacity: enter, transform: `scale(${interpolate(enter, [0, 1], [0.97, 1])})`,
        }}
      >
        <div style={{ height: 40, background: C.mantle, display: "flex", alignItems: "center", gap: 10, paddingLeft: 18 }}>
          {[C.red, C.yellow, C.green].map((c) => (
            <div key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />
          ))}
          <div style={{ fontFamily: MONO, fontSize: 18, color: C.overlay, marginLeft: 16 }}>
            assignment1_expense_split: real commands, recorded live
          </div>
        </div>
        <div style={{ position: "relative", width: 1728, height: 972 }}>
          <AbsoluteFill>
            <Sequence durationInFrames={Math.min(clipFrames, durationInFrames)}>{video}</Sequence>
            {durationInFrames > clipFrames ? (
              <Sequence from={clipFrames}>
                <Freeze frame={clipFrames - 1}>{video}</Freeze>
              </Sequence>
            ) : null}
          </AbsoluteFill>
        </div>
      </div>
    </AbsoluteFill>
  );
};
