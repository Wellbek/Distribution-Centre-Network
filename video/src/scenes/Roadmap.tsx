import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { FadeUp, Ground, Kicker, useExit } from "../components/motion";
import data from "../data.json";

// The lease sequence: one expiry at a time, drawn along a time line
export const Roadmap: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = useExit(228);
  const t0 = new Date("2027-01-01").getTime(), t1 = new Date("2030-01-01").getTime(), X = (d: string) => 40 + ((new Date(`${d}-15`).getTime() - t0) / (t1 - t0)) * 1560;
  const draw = interpolate(frame, [20, 170], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Ground glow="50% 55%">
      <AbsoluteFill style={{ padding: "100px 140px", opacity: out, justifyContent: "center" }}>
        <Kicker>The plan</Kicker>
        <FadeUp delay={6}><div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 64, color: COLORS.white, marginTop: 20, letterSpacing: -1.5 }}>Follow the leases, <span style={{ color: COLORS.lime }}>one expiry at a time</span></div></FadeUp>
        <div style={{ position: "relative", height: 380, marginTop: 50 }}>
          <div style={{ position: "absolute", left: 30, top: 186, width: 1580, height: 8, background: COLORS.line, borderRadius: 4 }} />
          <div style={{ position: "absolute", left: 30, top: 186, width: 1580 * draw, height: 8, background: COLORS.lime, borderRadius: 4 }} />
          {[2027, 2028, 2029].map((y) => <div key={y} style={{ position: "absolute", left: X(`${y}-01`) - 30, top: 150, fontFamily: SANS, fontWeight: 800, fontSize: 24, color: COLORS.muted }}>{y}</div>)}
          {data.steps.map((s, i) => {
            const at = 20 + ((X(s.date) - 40) / 1560) * 150, p = spring({ frame: frame - at, fps, config: { damping: 16, stiffness: 170 } });
            const up = i % 2 === 0, col = s.action === "renew" ? COLORS.purpleSoft : s.opened.length ? COLORS.lime : COLORS.muted;
            const op = interpolate(p, [0, 0.4], [0, 1], { extrapolateRight: "clamp" });
            return (
              <div key={s.date} style={{ position: "absolute", left: X(s.date) - 100, top: up ? 10 : 214, width: 200, textAlign: "center", opacity: op, transform: `translateY(${interpolate(p, [0, 1], [up ? -12 : 12, 0])}px)` }}>
                {!up && <div style={{ width: 22, height: 22, borderRadius: "50%", background: col, margin: "-34px auto 14px", border: `4px solid ${COLORS.bg}` }} />}
                <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 24, color: col }}>{s.date} · {s.site}</div>
                <div style={{ fontFamily: SANS, fontSize: 21, color: COLORS.offWhite, marginTop: 4 }}>{s.action === "renew" ? "renew" : s.opened.length ? `open ${s.opened.join(", ")}` : "close"}</div>
                {up && <div style={{ width: 22, height: 22, borderRadius: "50%", background: col, margin: "60px auto 0", border: `4px solid ${COLORS.bg}` }} />}
              </div>
            );
          })}
        </div>
        <FadeUp delay={170}><div style={{ fontFamily: SANS, fontSize: 34, color: COLORS.white }}><b style={{ color: COLORS.lime }}>{data.seq_saving} bn KRW</b> saved over 36 months, {data.seq_redraw} bn of it by redrawing territories, no lease needed. Switching everything at once would cost {data.one_shot} bn <i>more</i> than doing nothing.</div></FadeUp>
      </AbsoluteFill>
    </Ground>
  );
};
