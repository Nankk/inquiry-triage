import { useEffect, useState } from "react";
import { api, type InquiryView as IV } from "../api";
import { STATUS_LABEL, STEP_LABEL, URGENCY_LABEL, fmtMs, orderSteps, pairSides, sujiFromSteps } from "../lib";
import { SideBox } from "../components/SideBox";
import { InquiryBody } from "../components/InquiryBody";
import { Suji } from "../components/Suji";

export function InquiryView({ run, id }: { run: string; id: string }) {
  const [view, setView] = useState<IV | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    api
      .inquiry(run, id)
      .then((v) => {
        if (!alive) return;
        setView(v);
        setErr(null);
      })
      .catch((e: Error) => alive && setErr(e.message));
    return () => {
      alive = false;
    };
  }, [run, id]);
  if (err) return <div className="msg err">{err}</div>;
  if (!view) return <div className="empty">読み込み中</div>;
  const { item } = view;
  const sides = pairSides(view.steps);
  const suji = sujiFromSteps(view.steps, item);
  return (
    <>
      <div className="row between" style={{ marginBottom: 14 }}>
        <h2 className="h2"><span className="id">{item.inquiry_id}</span>{item.subject} <span className={"badge " + item.status}>{STATUS_LABEL[item.status] ?? item.status}</span></h2>
        <a href={`#/queue/${item.inquiry_id}`}>← 承認キューへ戻る</a>
      </div>
      <div className="meta" style={{ marginBottom: 14 }}>
        <span>差出人 <b>{item.customer}</b></span>
        <span>緊急度 <span className={"badge " + item.urgency}>{URGENCY_LABEL[item.urgency] ?? item.urgency}</span></span>
        <span>カテゴリ <b className="mono">{item.category}</b></span>
        <span>担当 <b className="mono">{item.specialist ?? "人が直接対応"}</b></span>
        {item.shadow && <span>影 <b className="mono">{item.shadow.agent}</b></span>}
      </div>

      <div className="card diagram-card">
        <h3>各段 <span className="who">所要時間は駅の下の数字。間隔は時間に比例しない</span></h3>
        <Suji suji={suji} size="l" animate />
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>問い合わせ <span className="who">{item.customer}</span></h3>
        <InquiryBody body={item.body} />
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>返信案の比較</h3>
        <div className={sides.shadow ? "cols" : ""}>
          <SideBox label="本番" who={sides.main.agent} body={sides.main.body} verdict={sides.main.verdict} reasons={sides.main.reasons} warnings={sides.main.warnings} failed={sides.main.failed} />
          {sides.shadow && <SideBox label="影" who={sides.shadow.agent} body={sides.shadow.body} verdict={sides.shadow.verdict} reasons={sides.shadow.reasons} warnings={sides.shadow.warnings} failed={sides.shadow.failed} />}
        </div>
      </div>

      <h3 className="sec-h">各段のログ（steps.jsonl、{view.steps.length} 行） <span className="who">スジはこの要約。記録はそのまま</span></h3>
      <div className="timeline">
        {orderSteps(view.steps).map((s, i) => (
          <div key={i} className={"tstep" + (s.step.startsWith("shadow_") ? " shadow" : "") + (s.status === "failed" ? " failed" : "")}>
            <div className="k">
              {STEP_LABEL[s.step] ?? s.step} {s.status === "failed" && <span className="badge fail">失敗</span>}
              <span className="who">{s.agent}{s.elapsed_ms != null && ` ・ ${fmtMs(s.elapsed_ms)}`}</span>
            </div>
            <pre>{s.status === "failed" ? s.reason : JSON.stringify(s.output, null, 1)}</pre>
          </div>
        ))}
      </div>

      {view.decisions.length > 0 && (
        <>
          <h3 className="sec-h" style={{ marginTop: 18 }}>判断の履歴（decisions.jsonl）</h3>
          <div className="timeline">
            {view.decisions.map((d, i) => (
              <div key={i} className="tstep">
                <div className="k">{STATUS_LABEL[d.action]}<span className="who">{d.ts.slice(0, 19).replace("T", " ")}</span></div>
                <pre>{d.reason || "（理由なし）"}{d.body && d.action === "edited" ? "\n\n" + d.body : ""}</pre>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  );
}
