import { Composition, Folder } from "remotion";
import { Demo } from "./Demo";
import { DemoV3 } from "./v3/DemoV3";
import timelineV3 from "./v3/timeline.json";
import { OutroScene } from "./OutroScene";
import timeline from "./timeline.json";
import { TitleScene } from "./TitleScene";
import { WorkflowScene } from "./WorkflowScene";

const W = 1920;
const H = 1080;
const frames = (id: string) => timeline.scenes.find((s) => s.id === id)?.frames ?? 300;

export const RemotionRoot: React.FC = () => (
  <>
    <Folder name="Scenes">
      <Composition id="Title" component={TitleScene} durationInFrames={frames("s01_title")} fps={30} width={W} height={H} />
      <Composition id="Workflow" component={WorkflowScene} durationInFrames={frames("s02_workflow")} fps={30} width={W} height={H} />
      <Composition id="Outro" component={OutroScene} durationInFrames={frames("s10_outro")} fps={30} width={W} height={H} />
    </Folder>
    <Composition id="DemoV3" component={DemoV3} durationInFrames={timelineV3.totalFrames} fps={30} width={W} height={H} />
    <Composition id="Demo" component={Demo} durationInFrames={timeline.totalFrames} fps={30} width={W} height={H} />
  </>
);
