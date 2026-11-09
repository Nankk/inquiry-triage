import { useCallback, useEffect, useState } from "react";
import { api, type InquiryView as IV, type QueueItem, type Status } from "../api";
import { STATUS_LABEL, URGENCY_LABEL, pairSides } from "../lib";
import { SideBox } from "../components/SideBox";
import { InquiryBody } from "../components/InquiryBody";

export function QueueView({ run, selected }: { run: string; selected?: string }) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let alive = true;
    api
      .queue(run)
      .then((q) => {
        if (!alive) return;
        setItems(q.items);
        setErr(null);
      })
      .catch((e: Error) => alive && setErr(e.message));
    return () => {
      alive = false;
    };
  }, [run, tick]);

  const sel = items.find((i) => i.inquiry_id === selected) ?? items[0];
  return (
    <>
      {err && <div className="msg err">{err}</div>}
      <div className="split">
        <div className="list">
          {items.map((i) => (
            <a key={i.inquiry_id} href={`#/queue/${i.inquiry_id}`} className={"card click" + (sel?.inquiry_id === i.inquiry_id ? " sel" : "")} style={{ color: "inherit" }}>
              <div className="row between">
                <span className="id">{i.inquiry_id}</span>
                <span className={"badge " + i.status}>{STATUS_LABEL[i.status] ?? i.status}</span>
              </div>
              <div className="title">{i.subject}</div>
              <div className="meta">
                <span>緊急度 <span className={"badge " + i.urgency}>{URGENCY_LABEL[i.urgency] ?? i.urgency}</span></span>
                <span>担当 <b className="mono">{i.specialist ?? "人が直接対応"}</b></span>
                <span>警告 <b>{i.warnings.length}</b></span>
                {i.shadow && <span>影 <b className="mono">{i.shadow.agent}</b></span>}
              </div>
            </a>
          ))}
          {items.length === 0 && <div className="empty">キューが空です</div>}
        </div>
        {sel && <Detail key={sel.inquiry_id + run} run={run} item={sel} onChanged={reload} />}
      </div>
    </>
  );
}

function Detail({ run, item, onChanged }: { run: string; item: QueueItem; onChanged: () => void }) {
  const [view, setView] = useState<IV | null>(null);
  const [side, setSide] = useState(true);
  const [editing, setEditing] = useState(false);
  const [body, setBody] = useState(item.draft?.body ?? "");
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .inquiry(run, item.inquiry_id)
      .then((v) => alive && setView(v))
      .catch(() => alive && setView(null));
    return () => {
      alive = false;
    };
  }, [run, item.inquiry_id, item.status]);

  const sides = view ? pairSides(view.steps) : null;
  const llmWarnings = item.warnings.filter((w) => w.startsWith("レビュー"));
  const detWarnings = item.warnings.filter((w) => !w.startsWith("レビュー"));

  async function act(action: Status) {
    setBusy(true);
    setMsg(null);
    try {
      const r = await api.decide(run, { inquiry_id: item.inquiry_id, action, reason, body: action === "edited" ? body : undefined });
      setMsg({ kind: "ok", text: `${STATUS_LABEL[action]} として記録しました` + (r.outbox ? `。送信箱: ${r.outbox}` : "") });
      setEditing(false);
      onChanged();
    } catch (e) {
      setMsg({ kind: "err", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="detail">
      <div className="row between">
        <h2>{item.inquiry_id} <span className={"badge " + item.status}>{STATUS_LABEL[item.status] ?? item.status}</span></h2>
        <a href={`#/inquiry/${item.inquiry_id}`}>各段のログを見る →</a>
      </div>
      <div className="meta">
        <span>差出人 <b>{item.customer}</b></span>
        <span>件名 <b>{item.subject}</b></span>
        <span>緊急度 <span className={"badge " + item.urgency}>{URGENCY_LABEL[item.urgency] ?? item.urgency}</span></span>
        <span>カテゴリ <span className="badge cat">{item.category}</span></span>
      </div>

      {msg && <div className={"msg " + msg.kind} style={{ marginTop: 12 }}>{msg.text}</div>}

      <div className="sec">
        <h3>問い合わせ</h3>
        <InquiryBody body={item.body} />
      </div>

      <div className="sec">
        <div className="row between">
          <h3>返信案 <span className="who mono" style={{ color: "var(--fg-3)", fontWeight: 400 }}>{item.specialist ?? "なし"}</span></h3>
          {item.shadow && sides?.shadow && (
            <label className="toggle"><input type="checkbox" checked={side} onChange={(e) => setSide(e.target.checked)} /> 影（{item.shadow.agent}）と並べる</label>
          )}
        </div>
        {editing ? (
          <textarea value={body} onChange={(e) => setBody(e.target.value)} />
        ) : side && sides?.shadow ? (
          <div className="cols">
            <SideBox label="本番" who={sides.main.agent} body={sides.main.body} verdict={sides.main.verdict} reasons={sides.main.reasons} warnings={sides.main.warnings} failed={sides.main.failed} />
            <SideBox label="影" who={sides.shadow.agent} body={sides.shadow.body} verdict={sides.shadow.verdict} reasons={sides.shadow.reasons} warnings={sides.shadow.warnings} failed={sides.shadow.failed} />
          </div>
        ) : (
          <div className={"draft" + (item.draft ? "" : " empty")}>{item.draft?.body ?? "返信案はありません（人が直接対応）"}</div>
        )}
        {item.draft && !editing && (
          <div className="hint">引用 {item.draft.cited.join(", ") || "なし"} ・ 確信度 {item.draft.confidence}{item.draft.ask_customer.length > 0 && ` ・ 顧客に確認: ${item.draft.ask_customer.join("、")}`}</div>
        )}
      </div>

      {!(side && sides?.shadow && !editing) && (
        <div className="sec">
          <h3>警告（{item.warnings.length}）</h3>
          <div className="warns">
            {detWarnings.map((w, i) => <div className="warn" key={"d" + i}>⚠ {w}</div>)}
            {llmWarnings.map((w, i) => <div className="warn llm" key={"l" + i}>⚑ {w}</div>)}
            {item.warnings.length === 0 && <div className="warn ok">✓ 警告なし</div>}
          </div>
        </div>
      )}

      {view && view.decisions.length > 0 && (
        <div className="sec">
          <h3>判断の履歴</h3>
          {view.decisions.map((d, i) => (
            <div className="dec" key={i}>{d.ts.slice(0, 19).replace("T", " ")} ・ {STATUS_LABEL[d.action]}{d.reason && ` ・ ${d.reason}`}</div>
          ))}
        </div>
      )}

      <div className="actions">
        <input placeholder="理由（任意）" value={reason} onChange={(e) => setReason(e.target.value)} style={{ flex: 1, minWidth: 180 }} />
        {editing ? (
          <>
            <button className="btn" onClick={() => { setEditing(false); setBody(item.draft?.body ?? ""); }} disabled={busy}>やめる</button>
            <button className="btn primary" onClick={() => act("edited")} disabled={busy || !body.trim()}>修正して採用</button>
          </>
        ) : (
          <>
            <button className="btn" onClick={() => setEditing(true)} disabled={busy}>修正</button>
            <button className="btn danger" onClick={() => act("rejected")} disabled={busy}>却下</button>
            <button className="btn primary" onClick={() => act("accepted")} disabled={busy || !item.draft}>採用して送信箱へ</button>
          </>
        )}
      </div>
    </div>
  );
}
