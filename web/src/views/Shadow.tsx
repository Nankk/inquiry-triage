import { useEffect, useState } from "react";
import { api, type Config, type ShadowReport } from "../api";
import { reportLine, summarize } from "../lib";

export function ShadowView({ run }: { run: string }) {
  const [rep, setRep] = useState<ShadowReport | null>(null);
  const [cfg, setCfg] = useState<Config | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<{ category: string; agent: string } | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    Promise.all([api.shadowReport(run), api.config()])
      .then(([r, c]) => {
        if (!alive) return;
        setRep(r);
        setCfg(c);
        setErr(null);
      })
      .catch((e: Error) => alive && setErr(e.message));
    return () => {
      alive = false;
    };
  }, [run, tick]);

  if (err) return <div className="msg err">{err}</div>;
  if (!rep || !cfg) return <div className="empty">読み込み中</div>;

  // 影が走ったカテゴリ → 影のエージェント（この run の記録から）
  const shadowByCat = new Map<string, string>();
  for (const r of rep.rows) if (r.shadow.agent) shadowByCat.set(r.category, r.shadow.agent);

  async function promote(category: string, agent: string) {
    try {
      await api.promote(category, agent);
      setMsg(`${category} の本番を ${agent} にしました。${cfg!.files.routing} に書き出し、${cfg!.files.shadow} から外しました。次回の run から有効です。次回は --routing-config ${cfg!.files.routing} を付け、影の設定は ${cfg!.files.shadow} を渡す（fixtures/shadow.json のままだと本番と影が同じになり run が止まります）`);
      setConfirm(null);
      setTick((t) => t + 1);
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  return (
    <>
      {msg && <div className="msg ok">{msg}</div>}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row between">
          <b>{summarize(rep.totals)}</b>
          <span className="id">run {rep.run_id}</span>
        </div>
        {rep.rows.length > 0 && (
          <table style={{ marginTop: 10 }}>
            <thead>
              <tr>
                <th>ID</th><th>カテゴリ</th>
                <th>本番</th><th>判定</th><th className="num">警告</th>
                <th>影</th><th>判定</th><th className="num">警告</th><th>どちらが良いか</th>
              </tr>
            </thead>
            <tbody>
              {rep.rows.map((r) => {
                const l = reportLine(r);
                return (
                  <tr key={r.inquiry_id} className="click" onClick={() => (location.hash = `#/inquiry/${r.inquiry_id}`)}>
                    <td className="mono">{r.inquiry_id}</td>
                    <td><span className="badge cat">{r.category}</span></td>
                    <td className="mono">{r.main.agent}</td>
                    <td><Verdict v={r.main.verdict} /></td>
                    <td className="num">{r.main.warnings}</td>
                    <td className="mono">{r.shadow.agent}</td>
                    <td><Verdict v={l.verdict} /></td>
                    <td className="num">{l.warnings}</td>
                    <td className={l.better === "shadow" ? "better" : l.better === "main" ? "worse" : ""}>
                      {l.better === "shadow" ? "影" : l.better === "main" ? "本番" : l.better === "even" ? "同じ" : "判定不能"}
                      {r.shadow.failed && <div className="hint">{r.shadow.failed}</div>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3 style={{ margin: "0 0 10px", fontSize: 13, color: "var(--fg-2)" }}>対応表（カテゴリ → 本番の担当）と昇格</h3>
        <table>
          <thead><tr><th>カテゴリ</th><th>本番</th><th>影</th><th></th></tr></thead>
          <tbody>
            {cfg.categories.filter((c) => c !== "other").map((c) => {
              const cur = cfg.routing[c];
              const sh = cfg.shadow[c] ?? shadowByCat.get(c);
              const overridden = cfg.routing_override[c] !== undefined;
              return (
                <tr key={c}>
                  <td><span className="badge cat">{c}</span></td>
                  <td className="mono">{cur}{overridden && <span className="hint" style={{ display: "inline", marginLeft: 8 }}>（routing.json で上書き）</span>}</td>
                  <td className="mono">{sh ?? <span style={{ color: "var(--fg-3)" }}>なし</span>}</td>
                  <td style={{ textAlign: "right" }}>
                    {sh && sh !== cur && (
                      confirm?.category === c ? (
                        <span className="row" style={{ justifyContent: "flex-end" }}>
                          <span className="hint">{sh} を {c} の本番にします。よいですか</span>
                          <button className="btn" onClick={() => setConfirm(null)}>やめる</button>
                          <button className="btn primary" onClick={() => promote(c, sh)}>昇格する</button>
                        </span>
                      ) : (
                        <button className="btn" onClick={() => setConfirm({ category: c, agent: sh })}>影を本番に昇格</button>
                      )
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="hint">
          昇格は {cfg.files.routing} に書き出し、{cfg.files.shadow} から該当カテゴリを外すだけです。コードは変わりません。次回は <code>uv run inquiry-triage run --routing-config {cfg.files.routing} --shadow-config {cfg.files.shadow}</code> で新しい対応表が使われます（影の設定に fixtures/shadow.json を渡し続けると、本番と影が同じになり run が止まります）。
        </div>
      </div>
    </>
  );
}

function Verdict({ v }: { v: string | null }) {
  if (!v || v === "-") return <span style={{ color: "var(--fg-3)" }}>-</span>;
  const cls = v === "pass" ? "pass" : v === "flag" ? "flag" : "fail";
  return <span className={"badge " + cls}>{v}</span>;
}
