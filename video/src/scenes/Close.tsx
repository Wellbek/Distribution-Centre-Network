import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { Corner, FadeUp, Ground } from "../components/motion";
import { KoreaMap } from "../components/KoreaMap";
import data from "../data.json";

// Phase 1: the decision asked for; phase 2: where to look
export const Close: React.FC = () => {
  const frame = useCurrentFrame();
  const p1 = interpolate(frame, [150, 170], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p2 = interpolate(frame, [165, 190], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const corner = interpolate(frame, [180, 210], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Ground glow="35% 50%">
      <AbsoluteFill style={{ opacity: p1, padding: "120px 140px" }}>
        <div style={{ position: "absolute", right: 150, top: 90 }}><KoreaMap width={560} drawAt={0} storesAt={0} dcsAt={10} network="rec" labels /></div>
        <FadeUp delay={4}><div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 96, color: COLORS.white, letterSpacing: -2.5, lineHeight: 1.05 }}>Run <span style={{ color: COLORS.lime }}>{data.k} DCs</span>.<br />Measure first.</div></FadeUp>
        <div style={{ marginTop: 50, display: "grid", gap: 18, width: 860 }}>
          {["Real deliveries, vehicle-days and spot hires by February 2027", "One month of GPS traces at one DC", `Renew ${data.kept[0]}; defer the first closure until the real-data check`].map((t, i) => (
            <FadeUp key={t} delay={30 + i * 16}><div style={{ fontFamily: SANS, fontSize: 32, color: COLORS.offWhite, background: COLORS.bgCard, borderLeft: `7px solid ${COLORS.lime}`, borderRadius: 14, padding: "16px 24px" }}>{t}</div></FadeUp>
          ))}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: p2, display: "grid", placeItems: "center", textAlign: "center" }}>
        <Corner opacity={corner} />
        <div>
          <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 120, color: COLORS.purpleSoft, letterSpacing: -4 }}>dasol<span style={{ color: COLORS.lime }}>.</span> <span style={{ fontSize: 46, background: COLORS.purple, color: COLORS.white, borderRadius: 999, padding: "6px 26px", verticalAlign: "middle", letterSpacing: 0 }}>network lab</span></div>
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 44, color: COLORS.white, marginTop: 30 }}>Open <span style={{ color: COLORS.lime }}>demo.html</span> and <span style={{ color: COLORS.lime }}>proposal.html</span></div>
          <div style={{ fontFamily: SANS, fontSize: 30, color: COLORS.offWhite, marginTop: 14 }}>Offline, every number reproducible with three commands</div>
          <div style={{ fontFamily: SANS, fontSize: 22, color: COLORS.muted, marginTop: 60 }}>Dasol Retail is fictional; geography and road distances are real · IE437 midterm project</div>
        </div>
      </AbsoluteFill>
    </Ground>
  );
};
