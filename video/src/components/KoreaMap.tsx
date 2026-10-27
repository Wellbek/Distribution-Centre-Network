import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../constants";
import { SANS } from "../fonts";
import data from "../data.json";

const BB = { lon0: 125.9, lon1: 129.8, lat0: 34.1, lat1: 38.75 }, KX = Math.cos((36.5 * Math.PI) / 180);

// Korea drawn from the registry: outline traced in, stores fade in, DCs pop; colour by network or by change
export const KoreaMap: React.FC<{ width: number; drawAt?: number; storesAt?: number; dcsAt?: number; network?: "today" | "rec"; showChange?: boolean; labels?: boolean }> = ({
  width, drawAt = 0, storesAt = 20, dcsAt = 50, network = "today", showChange = false, labels = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = width / ((BB.lon1 - BB.lon0) * KX), height = (BB.lat1 - BB.lat0) * s;
  const P = (lat: number, lon: number) => [(lon - BB.lon0) * KX * s, (BB.lat1 - lat) * s];
  const draw = interpolate(frame, [drawAt, drawAt + 45], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fill = interpolate(frame, [drawAt + 25, drawAt + 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dcs = network === "today" ? data.dcs_today : data.dcs_rec;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
      {data.provinces.map((ring, i) => (
        <path key={i} d={ring.map(([lo, la], k) => `${k ? "L" : "M"}${P(la, lo).map((v) => v.toFixed(1)).join(" ")}`).join("") + "Z"}
          fill={`rgba(236,220,240,${0.07 * fill})`} stroke={COLORS.purpleSoft} strokeWidth={1.2} pathLength={1} strokeDasharray={1} strokeDashoffset={draw} />
      ))}
      {data.stores_sample.map(([la, lo, moved], i) => {
        const t = storesAt + ((i * 7919) % 60);
        const op = interpolate(frame, [t, t + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const [x, y] = P(la, lo);
        const col = showChange ? (moved ? COLORS.lime : "#6b4f74") : COLORS.limeSoft;
        return <circle key={i} cx={x} cy={y} r={showChange && moved ? 2.3 : 1.7} fill={col} opacity={op * (showChange && !moved ? 0.6 : 0.85)} />;
      })}
      {dcs.map(([la, lo, name, both], i) => {
        const p = spring({ frame: frame - dcsAt - i * 4, fps, config: { damping: 14, stiffness: 160 } });
        const [x, y] = P(la as number, lo as number), z = interpolate(p, [0, 1], [0.93, 1]), op = interpolate(p, [0, 0.4], [0, 1], { extrapolateRight: "clamp" });
        const isNew = network === "rec" && !both;
        return (
          <g key={i} opacity={op} transform={`translate(${x} ${y}) scale(${z})`}>
            <rect x={-11} y={-11} width={22} height={22} rx={6} fill={COLORS.purple} stroke={COLORS.white} strokeWidth={2.5} />
            {isNew && <circle cx={11} cy={-11} r={6.5} fill={COLORS.lime} stroke={COLORS.white} strokeWidth={2} />}
            {labels && <text x={18} y={5} fontFamily={SANS} fontSize={15} fontWeight={700} fill={COLORS.offWhite}>{String(name).split(" ")[0]}</text>}
          </g>
        );
      })}
    </svg>
  );
};
