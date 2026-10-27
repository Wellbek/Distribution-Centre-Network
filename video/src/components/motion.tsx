import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../constants";
import { NUM, SANS } from "../fonts";

// Spring entrance from a delay: opacity and a small rise, never from scale 0
export const useEnter = (delay: number, damping = 18) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping, stiffness: 150 } });
  return { opacity: interpolate(p, [0, 0.4], [0, 1], { extrapolateRight: "clamp" }), transform: `translateY(${interpolate(p, [0, 1], [24, 0])}px) scale(${interpolate(p, [0, 1], [0.96, 1])})` };
};

// Fade out over the last frames of a scene
export const useExit = (start: number, len = 12) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [start, start + len], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
};

export const FadeUp: React.FC<{ delay: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ delay, children, style }) => {
  const s = useEnter(delay);
  return <div style={{ ...style, ...s }}>{children}</div>;
};

// A number that counts up with an ease-out
export const CountUp: React.FC<{ to: number; delay: number; decimals?: number; dur?: number; style?: React.CSSProperties }> = ({ to, delay, decimals = 0, dur = 40, style }) => {
  const frame = useCurrentFrame();
  const f = interpolate(frame, [delay, delay + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const v = to * (1 - Math.pow(1 - f, 3));
  return <span style={{ fontFamily: NUM, fontVariantNumeric: "tabular-nums", ...style }}>{v.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}</span>;
};

export const Kicker: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => (
  <FadeUp delay={delay} style={{ alignSelf: "flex-start", display: "inline-block", background: COLORS.lime, color: "#1f2a08", fontFamily: SANS, fontWeight: 800, fontSize: 22, letterSpacing: 1, borderRadius: 999, padding: "6px 20px", textTransform: "uppercase" }}>{children}</FadeUp>
);

// Dark purple ground with a soft radial glow and a faint dot grid
export const Ground: React.FC<{ glow?: string; children: React.ReactNode }> = ({ glow = "50% 35%", children }) => (
  <div style={{ position: "absolute", inset: 0, background: `radial-gradient(ellipse at ${glow}, #3a0f45 0%, ${COLORS.bg} 62%)`, overflow: "hidden" }}>
    <div style={{ position: "absolute", inset: 0, backgroundImage: `radial-gradient(${COLORS.line} 1.2px, transparent 1.2px)`, backgroundSize: "34px 34px", opacity: 0.45 }} />
    {children}
  </div>
);

export const Corner: React.FC<{ opacity: number }> = ({ opacity }) => {
  const b = { position: "absolute" as const, width: 56, height: 56, borderColor: COLORS.lime, opacity };
  return (
    <>
      <div style={{ ...b, top: 48, left: 48, borderTop: "4px solid", borderLeft: "4px solid" }} />
      <div style={{ ...b, top: 48, right: 48, borderTop: "4px solid", borderRight: "4px solid" }} />
      <div style={{ ...b, bottom: 48, left: 48, borderBottom: "4px solid", borderLeft: "4px solid" }} />
      <div style={{ ...b, bottom: 48, right: 48, borderBottom: "4px solid", borderRight: "4px solid" }} />
    </>
  );
};
