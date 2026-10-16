import React from "react";
import { Composition, Folder } from "remotion";
import { z } from "zod";
import { DURATION, HowThreeDWorks, RAIL_END, Rail, SCENES } from "./HowThreeDWorks";
import { themes } from "./theme";

const schema = z.object({
  theme: z.enum(["light", "dark"]),
});

// 1200×520 · 30 fps, the site's #idea player. One composition per theme so each renders to its
// own file with no --props juggling. Duration comes from the SCENES timeline.
const COMMON = {
  component: HowThreeDWorks,
  schema,
  durationInFrames: DURATION,
  fps: 30,
  width: 1200,
  height: 520,
} as const;

// Connected compositions: the same scene and rail components the parent places on its Tracks,
// registered so each opens standalone in Studio.
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="how-3d-works-light" {...COMMON} defaultProps={{ theme: "light" as const }} />
      <Composition id="how-3d-works-dark" {...COMMON} defaultProps={{ theme: "dark" as const }} />
      <Folder name="Scenes">
        {SCENES.map(({ id, dur, Scene }) => (
          <Composition
            key={id}
            id={`scene-${id}`}
            component={Scene}
            width={1200}
            height={520}
            fps={30}
            durationInFrames={dur}
            defaultProps={{ theme: "light" as const, dur }}
          />
        ))}
        {/* a bounded element: its standalone registration supplies the band's background */}
        <Composition
          id="chapter-rail"
          component={Rail}
          width={1200}
          height={520}
          fps={30}
          durationInFrames={RAIL_END}
          defaultProps={{ theme: "light" as const, style: { background: themes.light.bg } }}
        />
      </Folder>
    </>
  );
};
