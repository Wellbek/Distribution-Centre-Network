import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { FadeUp, Ground, Kicker, useExit } from "../components/motion";
import data from "../data.json";

const STEPS = [
  ["Real roads", "OpenStreetMap road distances through OSRM, not map distances"],
  ["Uncertain demand", "Each store's orders as a Poisson-Gamma belief; DCs routed on sampled days"],
  ["Every morning routed", "Savings and 2-opt routes for every DC, every stop before noon"],
  ["A smart search", ""],
];

// How the answer is computed, in four steps joined by a line that draws in
export const Engine: React.FC = () => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [30, 140], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = useExit(228);
  STEPS[3][1] = `Bayesian optimisation: ${data.budget} full evaluations chosen from ${data.networks} candidate networks`;
  return (
    <Ground glow="50% 60%">
      <AbsoluteFill style={{ padding: "110px 140px", opacity: out, justifyContent: "center" }}>
        <Kicker>The decision engine</Kicker>
        <FadeUp delay={8}><div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 66, color: COLORS.white, marginTop: 22, letterSpacing: -1.5 }}>Every network priced <span style={{ color: COLORS.lime }}>the same full way</span></div></FadeUp>
        <div style={{ position: "relative", marginTop: 80 }}>
          <div style={{ position: "absolute", left: 40, right: 40, top: 40, height: 6, background: COLORS.line, borderRadius: 3 }} />
          <div style={{ position: "absolute", left: 40, top: 40, height: 6, width: `calc((100% - 80px) * ${line})`, background: COLORS.lime, borderRadius: 3 }} />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 30 }}>
            {STEPS.map(([t, d], i) => (
              <FadeUp key={t} delay={30 + i * 28}>
                <div style={{ width: 86, height: 86, borderRadius: "50%", background: COLORS.purple, border: `5px solid ${COLORS.lime}`, color: COLORS.lime, fontFamily: SANS, fontWeight: 900, fontSize: 38, display: "grid", placeItems: "center" }}>{i + 1}</div>
                <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 36, color: COLORS.white, marginTop: 26 }}>{t}</div>
                <div style={{ fontFamily: SANS, fontSize: 27, color: COLORS.offWhite, marginTop: 12, lineHeight: 1.35 }}>{d}</div>
              </FadeUp>
            ))}
          </div>
        </div>
      </AbsoluteFill>
    </Ground>
  );
};
