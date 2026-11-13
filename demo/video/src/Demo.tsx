import { AbsoluteFill, Audio, Series, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ClipScene } from "./ClipScene";
import { OutroScene } from "./OutroScene";
import { C } from "./theme";
import timeline from "./timeline.json";
import { TitleScene } from "./TitleScene";
import { WorkflowScene } from "./WorkflowScene";

type Scene = (typeof timeline.scenes)[number] & { clip?: string; clipFrames?: number };

const CARDS: Record<string, React.FC> = {
  s01_title: TitleScene,
  s02_workflow: WorkflowScene,
  s10_outro: OutroScene,
};

const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div style={{ position: "absolute", left: 0, bottom: 0, height: 8, width: `${(frame / durationInFrames) * 100}%`, background: C.mauve, opacity: 0.85 }} />
  );
};

export const Demo: React.FC = () => (
  <AbsoluteFill style={{ background: C.crust }}>
    <Series>
      {(timeline.scenes as Scene[]).map((s) => {
        const Card = CARDS[s.id];
        return (
          <Series.Sequence key={s.id} name={s.id} durationInFrames={s.frames}>
            {Card ? <Card /> : <ClipScene clip={s.clip!} clipFrames={s.clipFrames!} tag={s.tag} caption={s.caption} />}
            <Series>
              <Series.Sequence durationInFrames={12}>{null}</Series.Sequence>
              <Series.Sequence durationInFrames={s.frames - 12}>
                <Audio src={staticFile(s.audio)} />
              </Series.Sequence>
            </Series>
          </Series.Sequence>
        );
      })}
    </Series>
    <Progress />
  </AbsoluteFill>
);
