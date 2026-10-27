import React from "react";
import { AbsoluteFill } from "remotion";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { COLORS } from "./constants";
import { SANS } from "./fonts";
import { Hook } from "./scenes/Hook";
import { Voices } from "./scenes/Voices";
import { Contrast } from "./scenes/Contrast";
import { Engine } from "./scenes/Engine";
import { Footage } from "./scenes/Footage";
import { Sweep } from "./scenes/Sweep";
import { Proof } from "./scenes/Proof";
import { Roadmap } from "./scenes/Roadmap";
import { Close } from "./scenes/Close";
import { FadeUp } from "./components/motion";
import data from "./data.json";

const Side: React.FC = () => (
  <div style={{ position: "absolute", left: 980, top: 230, width: 820 }}>
    <FadeUp delay={30}><div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 64, color: COLORS.white, letterSpacing: -1.5, lineHeight: 1.1 }}>Keep {data.kept.length}. Close {data.today_k - data.kept.length}. <span style={{ color: COLORS.lime }}>Open {data.opened.length}.</span></div></FadeUp>
    <FadeUp delay={50}><div style={{ fontFamily: SANS, fontSize: 30, color: COLORS.offWhite, marginTop: 24 }}>Kept: {data.kept.join(", ")}</div></FadeUp>
    <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 22 }}>
      {data.opened.map((n, i) => <FadeUp key={n} delay={70 + i * 7}><span style={{ display: "inline-block", fontFamily: SANS, fontWeight: 700, fontSize: 26, color: "#1f2a08", background: COLORS.limeSoft, borderRadius: 999, padding: "6px 18px" }}>{n}</span></FadeUp>)}
    </div>
    <FadeUp delay={140}><div style={{ fontFamily: SANS, fontSize: 32, color: COLORS.white, marginTop: 40, borderLeft: `7px solid ${COLORS.lime}`, paddingLeft: 20 }}>{data.moved.toLocaleString("en-US")} stores change DC, every one still served before noon.</div></FadeUp>
  </div>
);

// Timeline (30 fps; each fade overlaps neighbours by 15 frames)
export const SCENES: [React.FC, number][] = [
  [Hook, 240],
  [Voices, 210],
  [Contrast, 240],
  [Engine, 240],
  [() => <Footage src="day.mp4" title="One delivery day, every route on real roads" label="REAL DEMO FOOTAGE · demo.html" videoW={1500} videoH={844} callouts={[
    { at: 70, until: 190, title: "Trucks leave at 04:00", sub: "every DC's routes for one weekday", style: { right: 150, top: 600 } },
    { at: 200, until: 320, title: `${data.service}% before noon`, sub: "every store, every tested day", style: { right: 150, top: 790 } },
  ]} />, 330],
  [() => <Footage src="morph.mp4" title="Today's territories give way to the new network" label="REAL DEMO FOOTAGE · demo.html" videoW={784} videoH={800} side={<Side />} callouts={[]} />, 240],
  [Sweep, 210],
  [Proof, 270],
  [Roadmap, 240],
  [Close, 330],
];
const T = 15;
export const DURATION = SCENES.reduce((a, [, d]) => a + d, 0) - T * (SCENES.length - 1);

export const Trailer: React.FC = () => (
  <AbsoluteFill style={{ background: COLORS.bg }}>
    <TransitionSeries>
      {SCENES.flatMap(([S, d], i) => [
        <TransitionSeries.Sequence key={`s${i}`} durationInFrames={d}><S /></TransitionSeries.Sequence>,
        ...(i < SCENES.length - 1 ? [<TransitionSeries.Transition key={`t${i}`} presentation={fade()} timing={linearTiming({ durationInFrames: T })} />] : []),
      ])}
    </TransitionSeries>
  </AbsoluteFill>
);
