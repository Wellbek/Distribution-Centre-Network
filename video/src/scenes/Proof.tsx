import React from "react";
import { AbsoluteFill } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { CountUp, FadeUp, Ground, Kicker, useExit } from "../components/motion";
import data from "../data.json";

// The result and why it can be trusted
export const Proof: React.FC = () => {
  const out = useExit(258);
  const tile = { background: COLORS.bgCard, borderRadius: 24, padding: "30px 36px", height: 250 };
  const v = { fontWeight: 900, fontSize: 92, color: COLORS.lime, letterSpacing: -2, lineHeight: 1 };
  const l = { fontFamily: SANS, fontSize: 28, color: COLORS.offWhite, marginTop: 14, lineHeight: 1.3 };
  return (
    <Ground glow="50% 30%">
      <AbsoluteFill style={{ padding: "100px 140px", opacity: out, justifyContent: "center" }}>
        <Kicker>The result</Kicker>
        <FadeUp delay={6}><div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 64, color: COLORS.white, marginTop: 20, letterSpacing: -1.5 }}>Run <span style={{ color: COLORS.lime }}>{data.k} DCs</span>: keep {data.kept.length}, open {data.opened.length}</div></FadeUp>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 26, marginTop: 50 }}>
          <FadeUp delay={24}><div style={tile}><div style={v}><CountUp to={data.saving} delay={30} /></div><div style={l}>M KRW saved every month<br /><span style={{ color: COLORS.muted }}>90% band {data.ci[0]}-{data.ci[1]}</span></div></div></FadeUp>
          <FadeUp delay={40}><div style={tile}><div style={v}><CountUp to={data.held} delay={46} /></div><div style={l}>M KRW on demand days<br />the search never saw</div></div></FadeUp>
          <FadeUp delay={56}><div style={tile}><div style={v}><CountUp to={data.service} delay={62} decimals={0} />%</div><div style={l}>of stores served<br />before noon</div></div></FadeUp>
          <FadeUp delay={72}><div style={tile}><div style={v}><CountUp to={data.networks} delay={78} /></div><div style={l}>networks priced in full;<br />none is cheaper</div></div></FadeUp>
        </div>
        <div style={{ display: "flex", gap: 26, marginTop: 34 }}>
          {[`Found by the search at evaluation ${data.found_at} of ${data.budget}; random picking stops ${data.random_gap} M worse`, `${data.reversals} of ${data.reversal_rows} changed assumptions keep it paying`, `With a stronger router still about ${Math.round(data.pyvrp ?? 0)} M a month`].map((t, i) => (
            <FadeUp key={t} delay={120 + i * 16} style={{ flex: 1 }}><div style={{ fontFamily: SANS, fontSize: 26, color: COLORS.white, borderLeft: `6px solid ${COLORS.lime}`, paddingLeft: 18, lineHeight: 1.35 }}>{t}</div></FadeUp>
          ))}
        </div>
      </AbsoluteFill>
    </Ground>
  );
};
