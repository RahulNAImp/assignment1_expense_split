import React from "react";
import { AbsoluteFill, Audio, OffthreadVideo, Series, Sequence, Freeze, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ClipScene } from "../ClipScene";
import { C } from "../theme";
import timeline from "./timeline.json";
import { BeatCtx } from "./kit";
import { EvalSlide, HarnessSlide, Intro, Outro, TxnIdea } from "./OtherSlides";
import { SplitBalance, SplitIdea, SplitSettle, SplitShares } from "./SplitSlides";

const SLIDES: Record<string, React.FC> = {
  intro: Intro, split_idea: SplitIdea, split_shares: SplitShares, split_balance: SplitBalance,
  split_settle: SplitSettle, harness: HarnessSlide, txn_idea: TxnIdea, eval: EvalSlide, outro: Outro,
};

type Scene = {
  id: string; slide?: string; clip?: string; clipFrames?: number; clipFromBeat?: number;
  tag?: string; caption?: string; audio: string; beats: number[]; frames: number;
};

const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return <div style={{ position: "absolute", left: 0, bottom: 0, height: 8, width: `${(frame / durationInFrames) * 100}%`, background: C.mauve, opacity: 0.85 }} />;
};

const SceneView: React.FC<{ s: Scene }> = ({ s }) => {
  const { fps } = useVideoConfig();
  const Slide = s.slide ? SLIDES[s.slide] : null;
  const clipStart = s.clip ? Math.round((s.clipFromBeat ? s.beats[s.clipFromBeat] : 0) * fps) : 0;
  return (
    <BeatCtx.Provider value={s.beats}>
      {Slide ? <Sequence durationInFrames={s.clip ? clipStart || s.frames : s.frames}><Slide /></Sequence> : null}
      {s.clip ? (
        <Sequence from={clipStart}>
          <ClipScene clip={s.clip} clipFrames={s.clipFrames!} tag={s.tag ?? ""} caption={s.caption ?? ""} />
        </Sequence>
      ) : null}
      <Sequence from={10}><Audio src={staticFile(s.audio)} /></Sequence>
    </BeatCtx.Provider>
  );
};

export const DemoV3: React.FC = () => (
  <AbsoluteFill style={{ background: C.crust }}>
    <Series>
      {(timeline.scenes as Scene[]).map((s) => (
        <Series.Sequence key={s.id} name={s.id} durationInFrames={s.frames}>
          <SceneView s={s} />
        </Series.Sequence>
      ))}
    </Series>
    <Progress />
  </AbsoluteFill>
);
// keep imports used for tree-shaking clarity
void OffthreadVideo; void Freeze;
