import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../constants";
import { NUM, SANS } from "../fonts";
import { FadeUp, Ground, useExit } from "../components/motion";
import data from "../data.json";

// Cost against the number of DCs: rent rises, the road cost falls, the total bottoms out
export const Sweep: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = useExit(198);
  const sw = data.sweep, mx = Math.max(...sw.map((s) => s.total), data.today_search) * 1.06, ch = 560, bw = 1640 / sw.length;
  const best = sw.reduce((a, s) => (s.total < a.total ? s : a));
  const Y = (v: number) => ch - (v / mx) * ch;
  const line = interpolate(frame, [70, 95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Ground glow="50% 80%">
      <AbsoluteFill style={{ padding: "90px 140px", opacity: out }}>
        <FadeUp delay={0}><div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 58, color: COLORS.white, letterSpacing: -1.5 }}>Fewer DCs save rent. <span style={{ color: COLORS.lime }}>Until the roads cost more.</span></div></FadeUp>
        <svg width={1640} height={ch + 70} style={{ marginTop: 50, overflow: "visible" }}>
          {sw.map((s, i) => {
            const p = spring({ frame: frame - 12 - i * 4, fps, config: { damping: 20, stiffness: 120 } });
            const x = i * bw + 10, w = bw - 20, hT = (s.total / mx) * ch * p, hF = (s.fixed / mx) * ch * p, isBest = s.k === best.k;
            return (
              <g key={s.k}>
                <rect x={x} y={ch - hT} width={w} height={hT - hF} rx={8} fill={isBest ? COLORS.lime : "#6f4a7a"} />
                <rect x={x} y={ch - hF} width={w} height={hF} rx={6} fill={COLORS.purple} />
                <text x={x + w / 2} y={ch + 44} textAnchor="middle" fontFamily={NUM} fontWeight={isBest ? 900 : 500} fontSize={30} fill={isBest ? COLORS.lime : COLORS.muted}>{s.k}</text>
              </g>
            );
          })}
          <line x1={0} x2={1640 * line} y1={Y(data.today_search)} y2={Y(data.today_search)} stroke={COLORS.red} strokeWidth={4} strokeDasharray="14 10" />
        </svg>
        <FadeUp delay={100}><div style={{ fontFamily: SANS, fontSize: 30, color: COLORS.offWhite, marginTop: 10 }}>
          <span style={{ color: COLORS.purpleSoft, fontWeight: 800 }}>■</span> DC rent &nbsp;&nbsp;<span style={{ color: "#8b6a96", fontWeight: 800 }}>■</span> vehicles, fuel, spot trucks &nbsp;&nbsp;·&nbsp;&nbsp; <span style={{ color: COLORS.red, fontWeight: 800 }}>- - -</span> today's 12 DCs, {data.today_search.toLocaleString("en-US")} M &nbsp;&nbsp;·&nbsp;&nbsp; M KRW a month by number of DCs; <b style={{ color: COLORS.lime }}>{best.k} DCs</b> at the bottom
        </div></FadeUp>
      </AbsoluteFill>
    </Ground>
  );
};
