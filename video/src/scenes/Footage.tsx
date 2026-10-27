import React from "react";
import { AbsoluteFill, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import { FadeUp, Ground, useExit } from "../components/motion";

const Callout: React.FC<{ at: number; until: number; title: string; sub: string; style: React.CSSProperties }> = ({ at, until, title, sub, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - at, fps, config: { damping: 18, stiffness: 150 } });
  const op = interpolate(p, [0, 0.4], [0, 1], { extrapolateRight: "clamp" }) * interpolate(frame, [until - 12, until], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", opacity: op, transform: `scale(${interpolate(p, [0, 1], [0.94, 1])})`, background: "rgba(22,5,27,.92)", border: `3px solid ${COLORS.lime}`, borderRadius: 18, padding: "18px 26px", maxWidth: 470, ...style }}>
      <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 32, color: COLORS.lime }}>{title}</div>
      <div style={{ fontFamily: SANS, fontSize: 23, color: COLORS.offWhite, marginTop: 6 }}>{sub}</div>
    </div>
  );
};

// Real demo footage in a browser frame, with a title first and timed callouts
export const Footage: React.FC<{ src: string; title: string; label: string; callouts: { at: number; until: number; title: string; sub: string; style: React.CSSProperties }[]; videoW: number; videoH: number; side?: React.ReactNode }> = ({
  src, title, label, callouts, videoW, videoH, side,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const vin = interpolate(frame, [20, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const settle = interpolate(frame, [20, 80], [1.03, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = useExit(durationInFrames - 14);
  return (
    <Ground glow="50% 50%">
      <AbsoluteFill style={{ opacity: out }}>
        <FadeUp delay={0} style={{ position: "absolute", left: 120, top: 56, fontFamily: SANS, fontWeight: 900, fontSize: 50, color: COLORS.white, letterSpacing: -1 }}>{title}</FadeUp>
        <div style={{ position: "absolute", right: 120, top: 70, fontFamily: SANS, fontWeight: 800, fontSize: 18, letterSpacing: 2, color: COLORS.lime, border: `2px solid ${COLORS.lime}`, borderRadius: 999, padding: "6px 16px", opacity: vin }}>{label}</div>
        <div style={{ position: "absolute", left: side ? 120 : (1920 - videoW) / 2, top: 150, width: videoW, height: videoH, borderRadius: 18, overflow: "hidden", opacity: vin, transform: `scale(${settle})`, boxShadow: "0 30px 80px rgba(0,0,0,.55)", border: `2px solid ${COLORS.line}` }}>
          <Sequence from={20}><OffthreadVideo src={staticFile(src)} style={{ width: videoW, height: videoH }} muted /></Sequence>
        </div>
        {side}
        {callouts.map((c) => <Callout key={c.title} {...c} />)}
      </AbsoluteFill>
    </Ground>
  );
};
