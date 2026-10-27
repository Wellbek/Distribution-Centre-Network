import React from "react";
import { Composition } from "remotion";
import { DURATION, Trailer } from "./Trailer";
import { FPS, H, W } from "./constants";

export const RemotionRoot: React.FC = () => <Composition id="Trailer" component={Trailer} durationInFrames={DURATION} fps={FPS} width={W} height={H} />;
