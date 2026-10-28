import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { CountUp, FadeUp, Ground, useExit } from "../components/motion";
import data from "../data.json";

// The quick estimate against the routed answer
export const Contrast: React.FC = () => {
  const frame = useCurrentFrame();
  const div = interpolate(frame, [40, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = useExit(228);
  const col = (c: string) => ({ background: COLORS.bgCard, borderRadius: 26, padding: "44px 48px", borderTop: `8px solid ${c}`, height: 560 });
  const big = { fontFamily: SANS, fontWeight: 900, fontSize: 64, letterSpacing: -1.5, lineHeight: 1.05 };
  return (
    <Ground>
      <AbsoluteFill style={{ padding: "110px 140px", opacity: out }}>
        <FadeUp delay={0}><div style={{ ...big, color: COLORS.white, fontSize: 58 }}>The fast answer is <span style={{ color: COLORS.red }}>wrong</span>.</div></FadeUp>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 6px 1fr", gap: 46, marginTop: 50 }}>
          <FadeUp delay={14}>
            <div style={col(COLORS.red)}>
              <div style={{ fontFamily: SANS, fontSize: 26, fontWeight: 800, color: COLORS.muted, textTransform: "uppercase", letterSpacing: 1 }}>Quick estimate</div>
              <div style={{ fontFamily: SANS, fontSize: 30, color: COLORS.offWhite, marginTop: 14 }}>Counts vehicles by load. Ignores the clock.</div>
              <div style={{ ...big, color: COLORS.white, marginTop: 40 }}>Picks {data.proxy_k} DCs</div>
              <div style={{ ...big, color: COLORS.red, marginTop: 24 }}>+<CountUp to={data.proxy_loss} delay={60} /> M KRW</div>
              <div style={{ fontFamily: SANS, fontSize: 28, color: COLORS.muted, marginTop: 8 }}>a month more, once the routes are driven</div>
            </div>
          </FadeUp>
          <div style={{ background: `linear-gradient(${COLORS.lime}, transparent)`, opacity: div, borderRadius: 3 }} />
          <FadeUp delay={60}>
            <div style={col(COLORS.lime)}>
              <div style={{ fontFamily: SANS, fontSize: 26, fontWeight: 800, color: COLORS.muted, textTransform: "uppercase", letterSpacing: 1 }}>Every DC routed on real roads</div>
              <div style={{ fontFamily: SANS, fontSize: 30, color: COLORS.offWhite, marginTop: 14 }}>Vehicles must reach every store by noon.</div>
              <div style={{ ...big, color: COLORS.white, marginTop: 40 }}>Picks <span style={{ color: COLORS.lime }}>{data.k} DCs</span></div>
              <div style={{ ...big, color: COLORS.lime, marginTop: 24 }}>Cheapest found</div>
              <div style={{ fontFamily: SANS, fontSize: 28, color: COLORS.muted, marginTop: 8 }}>R² against the full cost: {data.r2_g1} → {data.r2_g2} with the clock</div>
            </div>
          </FadeUp>
        </div>
      </AbsoluteFill>
    </Ground>
  );
};
