// スジ: 問い合わせ 1 件を 1 本の列車として、4 つの駅（分類・担当・検査・キュー）を等間隔に結ぶ線。
// 本番は実線、影は破線（担当から）。失敗は駅に大きな三角、警告は検査の駅に小さな四角（検証）と三角（レビュー）、
// 返信案なしは線が止まって車止め、人の判断が済んだらキューの駅が塗りの四角。色と太さは緊急度の 3 段だけ。
// 所要時間は位置ではなく駅の下の数字（design.md D2-1）。
import { useEffect, useRef, useState } from "react";
import { STATIONS, fmtMs, type Suji as SujiModel, type Track, type Urgency3 } from "../lib";

const WIDTH: Record<Urgency3, number> = { high: 3, normal: 2, low: 1.2 };
const COLOR: Record<Urgency3, string> = { high: "var(--high-line)", normal: "var(--normal-line)", low: "var(--low-line)" };
const STUB = 12; // 線が最初の駅で止まるときに、止まったと読めるだけ引く長さ

export interface SujiProps {
  suji: SujiModel;
  /** s: 一覧の項目（駅名なし）。l: 詳細と追跡（駅名と ms） */
  size: "s" | "l";
  /** 選択の瞬間に本番の線を左から引く（詳細だけ） */
  animate?: boolean;
}

/** 大きいスジは入れ物の幅に合わせて座標を取り直す（縮めない。狭ければ横に送る） */
function useWidth(min: number) {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(min);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(min, Math.floor(e.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, [min]);
  return { ref, w };
}

export function Suji({ suji, size, animate }: SujiProps) {
  const large = size === "l";
  const { ref, w: measured } = useWidth(640);
  const W = large ? measured : 400;
  const pad = large ? 24 : 6;
  const xs = STATIONS.map((_, i) => pad + ((W - pad * 2) * i) / (STATIONS.length - 1));
  const yMain = large ? 30 : 7;
  const yShadow = large ? 62 : 16;
  const rows = suji.shadow ? 2 : 1;
  const H = large ? (rows === 2 ? 96 : 66) : rows === 2 ? 24 : 14;
  const color = COLOR[suji.urgency];
  const lw = WIDTH[suji.urgency];
  const anchor = (i: number) => (i === 0 ? "start" : i === STATIONS.length - 1 ? "end" : "middle");
  const title = `${STATIONS.slice(0, suji.main.to + 1).join(" → ")}${suji.main.terminal ? "（ここで止まる）" : ""}${suji.shadow ? "、影は担当から" : ""}${suji.decided ? "、判断済み" : ""}`;
  const svg = (
    <svg className={"suji" + (large ? " l" : " s")} viewBox={`0 0 ${W} ${H}`} width={large ? W : "100%"} height={H} preserveAspectRatio="xMinYMid meet" role="img" aria-label={title}>
      {large && (
        <g className="suji-names">
          {STATIONS.map((name, i) => (
            <text key={name} x={xs[i]} y={12} textAnchor={anchor(i)}>
              {name}
              {i === 1 && suji.articles.length > 0 && <tspan className="suji-note">　記事 {suji.articles.join(", ")}</tspan>}
            </text>
          ))}
        </g>
      )}
      <line x1={xs[0]} y1={yMain} x2={xs[xs.length - 1]} y2={yMain} className="suji-bed" />
      <TrackLine track={suji.main} xs={xs} y={yMain} color={color} width={lw} dashed={false} animate={!!animate && large} decided={suji.decided} />
      {suji.shadow && <TrackLine track={suji.shadow} xs={xs} y={yShadow} color={color} width={Math.max(1.2, lw * 0.6)} dashed from={1} />}
      {large && (
        <g className="suji-ms">
          {STATIONS.map((_, i) => (
            <text key={"m" + i} x={xs[i]} y={yMain + 16} textAnchor={anchor(i)}>{i <= suji.main.to && suji.main.elapsed ? fmtMs(suji.main.elapsed[i]) : ""}</text>
          ))}
          {suji.shadow &&
            STATIONS.map((_, i) => (
              <text key={"s" + i} x={xs[i]} y={yShadow + 16} textAnchor={anchor(i)} className="suji-shadow-ms">
                {i >= 1 && i <= suji.shadow!.to && suji.shadow!.elapsed ? fmtMs(suji.shadow!.elapsed[i]) : ""}
              </text>
            ))}
          <g className="suji-legend" transform={`translate(${xs[xs.length - 1]} ${H - 7})`}>
            <text x={suji.shadow ? -96 : -40} y={3} textAnchor="end">本番</text>
            <line x1={suji.shadow ? -92 : -36} y1={0} x2={suji.shadow ? -62 : -6} y2={0} style={{ stroke: color, strokeWidth: lw }} />
            {suji.shadow && (
              <>
                <text x={-40} y={3} textAnchor="end">影</text>
                <line x1={-36} y1={0} x2={-6} y2={0} style={{ stroke: color, strokeWidth: Math.max(1.2, lw * 0.6), strokeDasharray: "6 4" }} />
              </>
            )}
          </g>
        </g>
      )}
    </svg>
  );
  return large ? <div className="suji-fit" ref={ref}>{svg}</div> : svg;
}

function TrackLine({ track, xs, y, color, width, dashed, from = 0, animate, decided }: { track: Track; xs: number[]; y: number; color: string; width: number; dashed: boolean; from?: number; animate?: boolean; decided?: boolean }) {
  const x0 = xs[from];
  let x1 = xs[track.to];
  const stub = track.terminal && x1 - x0 <= 0; // 最初の駅で止まる: 止まったと読めるだけ引く
  if (stub) x1 = x0 + STUB;
  const r = dashed ? 2.6 : 3.4;
  const last = xs.length - 1;
  const xCheck = xs[2];
  return (
    <g>
      <line
        x1={x0} y1={y} x2={x1} y2={y}
        style={{ stroke: color, strokeWidth: width, strokeDasharray: dashed ? "6 4" : undefined }}
        className={animate ? "suji-draw" : undefined}
        pathLength={animate ? 1 : undefined}
      />
      {xs.map((x, i) =>
        i < from || i > track.to ? null : decided && i === last && !dashed ? (
          <rect key={i} x={x - 4.5} y={y - 4.5} width="9" height="9" className="suji-decided" />
        ) : (
          <circle key={i} cx={x} cy={y} r={r} className="suji-station" />
        ),
      )}
      {track.to >= 2 && track.failedAt !== 2 && (track.marks.det || track.marks.flag) && (
        <g className="suji-warn" style={{ fill: color }}>
          {track.marks.det && <rect x={xCheck - (track.marks.flag ? 9 : 3)} y={y - 12} width="6" height="6" />}
          {track.marks.flag && <path d={`M${xCheck + (track.marks.det ? 2 : -3.5)} ${y - 6} h7 l-3.5 -6.5 z`} />}
        </g>
      )}
      {track.failedAt != null && <path d={`M${xs[track.failedAt] - 5.5} ${y - 7} h11 l-5.5 -9 z`} style={{ fill: color }} className="suji-fail" />}
      {track.terminal && <path d={`M${x1 + 8} ${y - 6} v12 M${x1 + 11} ${y - 6} v12`} className="suji-end" style={{ stroke: color }} />}
    </g>
  );
}
