import { useEffect, useState } from "react";
import { api, type RunInfo } from "./api";
import { QueueView } from "./views/Queue";
import { InquiryView } from "./views/Inquiry";
import { ShadowView } from "./views/Shadow";

// ルーティングは hash のみ: #/queue, #/queue/INQ-001, #/inquiry/INQ-001, #/shadow
export type Route = { name: "queue"; id?: string } | { name: "inquiry"; id: string } | { name: "shadow" };

export function parseHash(hash: string): Route {
  const parts = hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  if (parts[0] === "inquiry" && parts[1]) return { name: "inquiry", id: decodeURIComponent(parts[1]) };
  if (parts[0] === "shadow") return { name: "shadow" };
  return { name: "queue", id: parts[1] ? decodeURIComponent(parts[1]) : undefined };
}

function useHash(): Route {
  const [route, setRoute] = useState<Route>(() => parseHash(location.hash));
  useEffect(() => {
    const on = () => setRoute(parseHash(location.hash));
    addEventListener("hashchange", on);
    return () => removeEventListener("hashchange", on);
  }, []);
  return route;
}

const TITLES: Record<Route["name"], [string, string]> = {
  queue: ["承認キュー", "返信案を見て、採用・却下・修正を決める"],
  inquiry: ["1 件の追跡", "分類から承認までの各段と、本番と影の比較"],
  shadow: ["影の比較", "新しい担当を本番に出す前に、記録だけの影と本番を比べる"],
};

export function App() {
  const route = useHash();
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [run, setRun] = useState<string>("latest");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .runs()
      .then((rs) => {
        if (!alive) return;
        setRuns(rs);
        // 初回だけ最新の run を選ぶ。利用者が選び直した値は上書きしない
        setRun((cur) => (cur === "latest" && rs.length ? rs[0].run_id : cur));
      })
      .catch((e: Error) => alive && setErr(e.message));
    return () => {
      alive = false;
    };
  }, []);

  const [title, sub] = TITLES[route.name];
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">inquiry-triage<small>問い合わせの仕分けと承認</small></div>
        <nav className="nav" aria-label="画面">
          <a href="#/queue" className={route.name !== "shadow" ? "active" : ""} aria-current={route.name !== "shadow" ? "page" : undefined}>承認キュー</a>
          <a href="#/shadow" className={route.name === "shadow" ? "active" : ""} aria-current={route.name === "shadow" ? "page" : undefined}>影の比較</a>
        </nav>
        <div className="runsel">
          <label htmlFor="run">実行（run）</label>
          <select id="run" value={run} onChange={(e) => setRun(e.target.value)}>
            {runs.length === 0 && <option value="latest">（実行がありません）</option>}
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>{r.run_id}（{r.items} 件）</option>
            ))}
          </select>
        </div>
      </header>
      <main className="main">
        <div className="pagehead"><h1>{title}</h1><span className="sub">{sub}</span></div>
        <div className="content">
          {err && <div className="msg err">{err}</div>}
          {runs.length === 0 && !err && <div className="empty">実行がありません。まず <code>uv run inquiry-triage run</code> を実行してください。</div>}
          {runs.length > 0 && route.name === "queue" && <QueueView run={run} selected={route.id} />}
          {runs.length > 0 && route.name === "inquiry" && <InquiryView run={run} id={route.id} />}
          {runs.length > 0 && route.name === "shadow" && <ShadowView run={run} />}
        </div>
        <div className="foot">
          判断は decisions.jsonl に追記されるだけで、steps.jsonl と queue.json は書き換えません。昇格は routing.json に書き出され、次回の run から有効です。
        </div>
      </main>
    </div>
  );
}
