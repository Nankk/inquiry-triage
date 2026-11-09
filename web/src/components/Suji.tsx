// スジ: 問い合わせ 1 件を 1 本の列車として、4 つの駅（分類・担当・検査・キュー）を等間隔に結ぶ線。
// 本番は実線、影は破線（担当から）。失敗は駅に三角の記号、返信案なしは線が止まって車止め。
// 色と太さは緊急度の 3 段だけ。所要時間は位置ではなく駅の下の数字（design.md D2-1）。
import { STATIONS, fmtMs, type Suji as SujiModel, type Track, type Urgency3 } from "../lib";

const WIDTH: Record<Urgency3, number> = { high: 3, normal: 2, low: 1.2 };
const COLOR: Record<Urgency3, string> = { high: "var(--high-line)", normal: "var(--normal-line)", low: "var(--low-line)" };

export interface SujiProps {
  suji: SujiModel;
  /** s: 一覧の項目（駅名なし）。l: 詳細と追跡（駅名と ms） */
  size: "s" | "l";
  /** 選択の瞬間に本番の線を左から引く（詳細だけ） */
  animate?: boolean;
}

export function Suji({ suji, size, animate }: SujiProps) {
  const large = size === "l";
  const W = large ? 800 : 400;
  const pad = large ? 24 : 6;
  const xs = STATIONS.map((_, i) => pad + ((W - pad * 2) * i) / (STATIONS.length - 1));
  const yMain = large ? 30 : 7;
  const yShadow = large ? 62 : 16;
  const rows = suji.shadow ? 2 : 1;
  const H = large ? (rows === 2 ? 96 : 66) : rows === 2 ? 24 : 14;
  const color = COLOR[suji.urgency];
  const w = WIDTH[suji.urgency];
  const labelMain = (i: number) => (suji.main.elapsed ? fmtMs(suji.main.elapsed[i]) : "");
  const labelShadow = (i: number) => (suji.shadow?.elapsed ? fmtMs(suji.shadow.elapsed[i]) : "");
  const title = `${STATIONS.slice(0, suji.main.to + 1).join(" → ")}${suji.main.terminal ? "（ここで止まる）" : ""}${suji.shadow ? "、影は担当から" : ""}`;
  return (
    <svg className={"suji" + (large ? " l" : " s")} viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="xMinYMid meet" role="img" aria-label={title}>
      {large && (
        <g className="suji-names">
          {STATIONS.map((name, i) => (
            <text key={name} x={xs[i]} y={12} textAnchor={i === 0 ? "start" : i === STATIONS.length - 1 ? "end" : "middle"}>
              {name}
              {i === 1 && suji.articles.length > 0 && <tspan className="suji-note">　記事 {suji.articles.join(", ")}</tspan>}
            </text>
          ))}
        </g>
      )}
      {/* 線路の下地: 届かなかった駅までを薄い点線で */}
      <line x1={xs[0]} y1={yMain} x2={xs[xs.length - 1]} y2={yMain} className="suji-bed" />
      <TrackLine track={suji.main} xs={xs} y={yMain} color={color} width={w} dashed={false} animate={!!animate && large} />
      {suji.shadow && <TrackLine track={suji.shadow} xs={xs} y={yShadow} color={color} width={Math.max(1.2, w * 0.6)} dashed from={1} />}
      {large && (
        <g className="suji-ms">
          {STATIONS.map((_, i) => (
            <text key={"m" + i} x={xs[i]} y={yMain + 16} textAnchor={i === 0 ? "start" : i === STATIONS.length - 1 ? "end" : "middle"}>
              {i <= suji.main.to ? labelMain(i) || (i === STATIONS.length - 1 ? "" : "") : ""}
            </text>
          ))}
          {suji.shadow &&
            STATIONS.map((_, i) => (
              <text key={"s" + i} x={xs[i]} y={yShadow + 16} textAnchor={i === 0 ? "start" : i === STATIONS.length - 1 ? "end" : "middle"} className="suji-shadow-ms">
                {i >= 1 && i <= suji.shadow!.to ? labelShadow(i) : ""}
              </text>
            ))}
          <text x={xs[xs.length - 1]} y={H - 4} textAnchor="end" className="suji-legend">
            本番 ── {suji.shadow ? "影 ╌╌" : ""}
          </text>
        </g>
      )}
    </svg>
  );
}

function TrackLine({ track, xs, y, color, width, dashed, from = 0, animate }: { track: Track; xs: number[]; y: number; color: string; width: number; dashed: boolean; from?: number; animate?: boolean }) {
  const x0 = xs[from];
  const x1 = xs[track.to];
  const len = Math.max(0, x1 - x0);
  const r = dashed ? 2.6 : 3.4;
  return (
    <g>
      {len > 0 && (
        <line
          x1={x0} y1={y} x2={x1} y2={y}
          style={{ stroke: color, strokeWidth: width, strokeDasharray: dashed ? "6 4" : undefined }}
          className={animate ? "suji-draw" : undefined}
          pathLength={animate ? 1 : undefined}
        />
      )}
      {xs.map((x, i) =>
        i < from || i > track.to ? null : (
          <circle key={i} cx={x} cy={y} r={r} className="suji-station" />
        ),
      )}
      {track.failedAt != null && (
        <path
          d={`M${xs[track.failedAt] - 5} ${y - 7} h10 l-5 -8 z`}
          style={{ fill: color }}
          className="suji-fail"
        />
      )}
      {track.terminal && (
        <path d={`M${x1 + 8} ${y - 6} v12 M${x1 + 11} ${y - 6} v12`} className="suji-end" style={{ stroke: color }} />
      )}
    </g>
  );
}
