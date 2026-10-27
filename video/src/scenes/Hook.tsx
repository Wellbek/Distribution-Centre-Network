import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { FadeUp, Ground, useExit } from "../components/motion";
import { KoreaMap } from "../components/KoreaMap";
import data from "../data.json";

// The stakes: a whole country of stores, today's network, the noon deadline, then the question
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const p1 = interpolate(frame, [118, 134], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p2 = interpolate(frame, [130, 150], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = useExit(228);
  const h = { fontFamily: SANS, fontWeight: 900, color: COLORS.white, fontSize: 74, letterSpacing: -2, lineHeight: 1.1 };
  return (
    <Ground glow="70% 45%">
      <AbsoluteFill style={{ opacity: out }}>
        <div style={{ position: "absolute", right: 150, top: 70 }}><KoreaMap width={620} drawAt={0} storesAt={10} dcsAt={70} /></div>
        <div style={{ position: "absolute", left: 140, top: 320, opacity: p1, width: 1000 }}>
          <FadeUp delay={6}><div style={h}><span style={{ color: COLORS.lime }}>{data.stores.toLocaleString("en-US")}</span> stores.</div></FadeUp>
          <FadeUp delay={30}><div style={h}>{data.today_k} distribution centres.</div></FadeUp>
          <FadeUp delay={54}><div style={{ ...h, color: COLORS.limeSoft }}>Every delivery before noon.</div></FadeUp>
        </div>
        <div style={{ position: "absolute", left: 140, top: 270, opacity: p2, width: 980 }}>
          <FadeUp delay={136}><div style={{ fontFamily: SANS, fontSize: 34, color: COLORS.muted, fontWeight: 600 }}>The leases expire one by one, from 2027 to 2029.</div></FadeUp>
          <FadeUp delay={150}><div style={{ ...h, fontSize: 92, marginTop: 18 }}>How many DCs should Dasol run, <span style={{ color: COLORS.lime }}>and where?</span></div></FadeUp>
        </div>
      </AbsoluteFill>
    </Ground>
  );
};
