import React from "react";
import { AbsoluteFill } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { FadeUp, Ground, Kicker, useExit } from "../components/motion";

const V = [
  ["Strategy & Planning", "Cut from twelve to eight, and lease costs fall.", "a decision"],
  ["Delivery Operations", "Wider areas mean longer drives and more vehicles.", "an evaluation"],
  ["Data Team", "The centre of gravity is the optimal site.", "a method"],
  ["Field Manager", "Close on the map, far by road.", "a claim about the model"],
];

// The four statements of the review meeting in the brief, each a different kind of claim
export const Voices: React.FC = () => {
  const out = useExit(198);
  return (
    <Ground glow="50% 20%">
      <AbsoluteFill style={{ padding: "110px 140px", opacity: out }}>
        <Kicker>The review meeting</Kicker>
        <FadeUp delay={8}><div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 66, color: COLORS.white, marginTop: 22, letterSpacing: -1.5 }}>Four voices. <span style={{ color: COLORS.lime }}>Four kinds of claim.</span></div></FadeUp>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28, marginTop: 50 }}>
          {V.map(([who, q, kind], i) => (
            <FadeUp key={who} delay={30 + i * 22}>
              <div style={{ background: COLORS.bgCard, borderLeft: `8px solid ${COLORS.purpleSoft}`, borderRadius: 20, padding: "26px 32px", height: 190 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontFamily: SANS }}>
                  <span style={{ fontWeight: 800, fontSize: 28, color: COLORS.offWhite }}>{who}</span>
                  <span style={{ fontWeight: 800, fontSize: 20, color: "#1f2a08", background: COLORS.limeSoft, borderRadius: 999, padding: "4px 14px" }}>{kind}</span>
                </div>
                <div style={{ fontFamily: SANS, fontSize: 36, color: COLORS.white, marginTop: 18, fontWeight: 500 }}>"{q}"</div>
              </div>
            </FadeUp>
          ))}
        </div>
        <FadeUp delay={130}><div style={{ fontFamily: SANS, fontSize: 30, color: COLORS.muted, marginTop: 40 }}>They can only be compared on one scale: <b style={{ color: COLORS.white }}>total monthly cost</b>.</div></FadeUp>
      </AbsoluteFill>
    </Ground>
  );
};
