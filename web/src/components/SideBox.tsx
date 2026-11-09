// 本番または影の 1 列: 返信案の本文、レビュー判定、警告。Queue と Inquiry の両方で使う。
import { Mark } from "./Mark";

export interface SideBoxProps {
  label: string;
  who: string | null;
  body: string | null;
  verdict: string | null;
  reasons: string[];
  warnings: string[];
  failed: string | null;
}

export function SideBox(p: SideBoxProps) {
  const v = p.verdict;
  const cls = v === "pass" ? "pass" : v === "flag" ? "flag" : v ? "fail" : "pending";
  return (
    <div className="col">
      <h4>
        {p.label} <span className="who">{p.who ?? "-"}</span> {v && <span className={"badge " + cls}>{v}</span>}
        {p.body && <span className="count">{p.body.length} 文字</span>}
      </h4>
      <div className={"draft" + (p.body ? "" : " empty")}>{p.body ?? (p.failed ? `失敗: ${p.failed}` : "返信案なし")}</div>
      <div className="warns">
        {p.warnings.map((w, i) => <div className="warn" key={"w" + i}><Mark kind="warn" />{w}</div>)}
        {v === "flag" && p.reasons.map((r, i) => <div className="warn llm" key={"r" + i}><Mark kind="flag" />レビュー指摘: {r}</div>)}
        {v === "失敗" && p.reasons.map((r, i) => <div className="warn llm" key={"f" + i}><Mark kind="flag" />レビュー失敗: {r}</div>)}
        {p.body && p.warnings.length === 0 && v === "pass" && <div className="warn ok"><Mark kind="ok" />警告なし、レビュー pass</div>}
      </div>
    </div>
  );
}
