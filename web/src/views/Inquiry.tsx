import { useEffect, useState } from "react";
import { api, type InquiryView as IV } from "../api";
import { STATUS_LABEL, STEP_LABEL, fmtMs, orderSteps, pairSides } from "../lib";
import { SideBox } from "../components/SideBox";

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
  return (
    <>
      <div className="row between" style={{ marginBottom: 14 }}>
        <div>
          <span className="id">{item.inquiry_id}</span> <b>{item.subject}</b>{" "}
          <span className={"badge " + item.status}>{STATUS_LABEL[item.status] ?? item.status}</span>
        </div>
        <a href={`#/queue/${item.inquiry_id}`}>← 承認キューへ戻る</a>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ margin: "0 0 10px", fontSize: 13, color: "var(--fg-2)" }}>返信案の比較</h3>
        <div className={sides.shadow ? "cols" : ""}>
          <SideBox label="本番" who={sides.main.agent} body={sides.main.body} verdict={sides.main.verdict} reasons={sides.main.reasons} warnings={sides.main.warnings} failed={sides.main.failed} />
          {sides.shadow && <SideBox label="影" who={sides.shadow.agent} body={sides.shadow.body} verdict={sides.shadow.verdict} reasons={sides.shadow.reasons} warnings={sides.shadow.warnings} failed={sides.shadow.failed} />}
        </div>
      </div>

      <h3 style={{ margin: "0 0 10px", fontSize: 13, color: "var(--fg-2)" }}>各段のログ（steps.jsonl、{view.steps.length} 行）</h3>
      <div className="timeline">
        {orderSteps(view.steps).map((s, i) => (
          <div key={i} className={"tstep" + (s.step.startsWith("shadow_") ? " shadow" : "") + (s.status === "failed" ? " failed" : "")}>
            <div className="k">
              {STEP_LABEL[s.step] ?? s.step} {s.status === "failed" && <span className="badge fail">失敗</span>}
              <span className="who">{s.agent} ・ {fmtMs(s.elapsed_ms)}</span>
            </div>
            <pre>{s.status === "failed" ? s.reason : JSON.stringify(s.output, null, 1)}</pre>
          </div>
        ))}
      </div>

      {view.decisions.length > 0 && (
        <>
          <h3 style={{ margin: "18px 0 10px", fontSize: 13, color: "var(--fg-2)" }}>判断の履歴（decisions.jsonl）</h3>
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
