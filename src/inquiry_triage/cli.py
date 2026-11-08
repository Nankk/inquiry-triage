"""CLI。run: 一周してキューを作る / show: キューと追跡ログを見る / review: 人の承認（採用・却下・修正）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from inquiry_triage.agents import load_shadow_config
from inquiry_triage.llm import LiveClient, LLMClient, LLMError, RecordingClient, ReplayClient
from inquiry_triage.models import Inquiry
from inquiry_triage.orchestrator import Orchestrator
from inquiry_triage.retrieval import load_kb
from inquiry_triage.store import RunStore

FIX = Path("fixtures")


def _client(a: argparse.Namespace) -> LLMClient:
    """既定はリプレイ。--live で実呼び出し、--record は実呼び出しの結果を --replay の fixture に保存する。"""
    if not (a.live or a.record):
        return ReplayClient(Path(a.replay))
    live = LiveClient.from_env()
    return RecordingClient(live, Path(a.replay)) if a.record else live


def cmd_run(a: argparse.Namespace) -> int:
    inquiries = [Inquiry.from_dict(d) for d in json.loads(Path(a.inbox).read_text(encoding="utf-8"))]
    if a.only:
        inquiries = [i for i in inquiries if i.id in a.only]
        if not inquiries:
            print(f"--only に一致する問い合わせがありません: {a.only}", file=sys.stderr)
            return 2
    try:
        client = _client(a)
        shadow = load_shadow_config(Path(a.shadow_config)) if a.shadow_config else None
    except (LLMError, ValueError) as e:  # 設定の不備は実行を作る前に止める
        print(str(e), file=sys.stderr)
        return 2
    store = RunStore(Path(a.runs))
    orch = Orchestrator(
        client,
        load_kb(Path(a.kb)),
        Path(a.policy).read_text(encoding="utf-8"),
        store,
        workers=a.workers,
        shadow=shadow,
    )
    items = orch.run(inquiries)
    print(f"run {store.run_id}: {len(items)} 件をキューに載せました → {store.dir}")
    _print_queue([i.to_dict() for i in items])
    for st in store.read_steps():
        if st["status"] == "failed":
            print(f"失敗: {st['inquiry_id']} {st['step']} ({st['agent']}): {st['reason']}", file=sys.stderr)
    return 0


def _print_queue(items: list[dict], statuses: dict[str, str] | None = None) -> None:
    statuses = statuses or {}
    print(f"{'ID':8} {'緊急度':6} {'カテゴリ':10} {'担当':22} {'警告':4} {'状態':9} 件名")
    for i in items:
        st = statuses.get(i["inquiry_id"], i["status"])
        print(
            f"{i['inquiry_id']:8} {i['urgency']:6} {i['category']:10} "
            f"{(i['specialist'] or '-'):22} {len(i['warnings']):4} {st:9} {i['subject']}"
        )


def cmd_show(a: argparse.Namespace) -> int:
    run_id = a.run_id or RunStore.latest(Path(a.runs))
    if not run_id:
        print("実行がありません", file=sys.stderr)
        return 1
    store = RunStore(Path(a.runs), run_id)
    if a.inquiry:
        for s in store.read_steps():
            if s["inquiry_id"] == a.inquiry:
                print(json.dumps(s, ensure_ascii=False))
        for i in store.read_queue():
            if i["inquiry_id"] == a.inquiry:
                print("\n--- キュー項目 ---")
                print(json.dumps(i, ensure_ascii=False, indent=2))
        return 0
    print(f"run {run_id}")
    _print_queue(store.read_queue(), store.statuses())
    return 0


def _print_item(item: dict, status: str) -> None:
    print(
        f"[{item['inquiry_id']}] {item['subject']}  緊急度={item['urgency']} 担当={item['specialist'] or '-'} 状態={status}"
    )
    for w in item["warnings"]:
        print(f"  ! {w}")
    d = item["draft"]
    if d:
        print(f"  引用={list(d['cited'])} 確信度={d['confidence']} 顧客への確認={list(d['ask_customer'])}")
        print("  --- 返信案 ---")
        for line in d["body"].splitlines():
            print(f"  {line}")
    else:
        print("  （返信案なし）")


def cmd_review(a: argparse.Namespace) -> int:
    """人の判断。--accept / --reject / --body FILE のどれかで 1 件を決め、decisions.jsonl に追記する。
    指定が無ければ未決の項目を返信案つきで一覧する。queue.json と steps.jsonl は書き換えない。"""
    run_id = a.run_id or RunStore.latest(Path(a.runs))
    if not run_id:
        print("実行がありません", file=sys.stderr)
        return 1
    store = RunStore(Path(a.runs), run_id)
    items = {i["inquiry_id"]: i for i in store.read_queue()}
    statuses = store.statuses()

    action = "accepted" if a.accept else "rejected" if a.reject else "edited" if a.body else None
    if action is None:
        for i in items.values():
            if statuses.get(i["inquiry_id"], "pending") == "pending":
                _print_item(i, "pending")
                print()
        return 0
    if not a.inquiry:
        print("--inquiry を指定してください", file=sys.stderr)
        return 2
    item = items.get(a.inquiry)
    if item is None:
        print(f"{a.inquiry} はこの実行のキューにありません", file=sys.stderr)
        return 2

    if action == "edited":
        body = sys.stdin.read() if a.body == "-" else Path(a.body).read_text(encoding="utf-8")
    elif action == "accepted":
        if not item["draft"]:
            print(f"{a.inquiry} に返信案がありません。--body で本文を渡してください", file=sys.stderr)
            return 2
        body = item["draft"]["body"]
    else:
        body = None

    store.append_decision({"inquiry_id": a.inquiry, "action": action, "reason": a.reason, "body": body})
    if body is not None:
        out = Path(a.outbox) / run_id / f"{a.inquiry}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            f"To: {item['customer']}\nSubject: Re: {item['subject']}\n\n{body.rstrip()}\n", encoding="utf-8"
        )
        print(f"{a.inquiry}: {action} → {out}")
    else:
        print(f"{a.inquiry}: {action}")
    return 0


def cmd_shadow_report(a: argparse.Namespace) -> int:
    """影が走った問い合わせごとに、本番と影のレビュー判定・警告数を並べる。昇格判断の材料。"""
    run_id = a.run_id or RunStore.latest(Path(a.runs))
    if not run_id:
        print("実行がありません", file=sys.stderr)
        return 1
    store = RunStore(Path(a.runs), run_id)
    reviews = {s["inquiry_id"]: s for s in store.read_steps() if s["step"] == "review"}
    rows = [i for i in store.read_queue() if i.get("shadow")]
    if not rows:
        print(f"run {run_id}: 影は走っていません")
        return 0

    def verdict(step: dict | None) -> str:
        if step is None:
            return "-"
        return step["output"]["verdict"] if step["status"] == "ok" else "失敗"

    print(f"run {run_id}")
    print(f"{'ID':8} {'本番':22} {'判定':6} {'警告':4}  {'影':22} {'判定':6} {'警告':4}")
    tot = {"main_pass": 0, "main_warn": 0, "shadow_pass": 0, "shadow_warn": 0}
    for i in rows:
        mv = verdict(reviews.get(i["inquiry_id"]))
        sh = i["shadow"]
        if sh["failed"]:
            sv, sw = "失敗", "-"
            tail = f"  ← {sh['failed']}"
        else:
            sv, sw, tail = sh["verdict"], str(sh["warnings"]), ""
            tot["shadow_pass"] += sv == "pass"
            tot["shadow_warn"] += sh["warnings"]
        tot["main_pass"] += mv == "pass"
        tot["main_warn"] += len(i["warnings"])
        print(
            f"{i['inquiry_id']:8} {i['specialist']:22} {mv:6} {len(i['warnings']):4}  "
            f"{sh['agent']:22} {sv:6} {sw:>4}{tail}"
        )
    print(
        f"合計 {len(rows)} 件: 本番 pass {tot['main_pass']} / 警告 {tot['main_warn']}、"
        f"影 pass {tot['shadow_pass']} / 警告 {tot['shadow_warn']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="inquiry-triage")
    p.add_argument("--runs", default="runs")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="問い合わせを一周してキューを作る")
    r.add_argument("--inbox", default=str(FIX / "inbox.json"))
    r.add_argument("--kb", default=str(FIX / "kb.json"))
    r.add_argument("--policy", default=str(FIX / "policy.md"))
    r.add_argument("--replay", default=str(FIX / "replay"), help="LLM fixture のディレクトリ")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--only", nargs="+", metavar="ID", help="この問い合わせ ID だけ処理する")
    r.add_argument(
        "--shadow-config", metavar="FILE", help="影の設定 {カテゴリ: エージェント名}。影は記録のみ"
    )
    m = r.add_mutually_exclusive_group()
    m.add_argument("--live", action="store_true", help="LLM を実際に呼ぶ（環境変数 INQUIRY_TRIAGE_*）")
    m.add_argument("--record", action="store_true", help="実際に呼び、結果を --replay の fixture に保存する")
    r.set_defaults(fn=cmd_run)

    s = sub.add_parser("show", help="キューを表示。--inquiry で 1 件の追跡ログ")
    s.add_argument("run_id", nargs="?")
    s.add_argument("--inquiry")
    s.set_defaults(fn=cmd_show)

    v = sub.add_parser(
        "review", help="承認。指定なしで未決一覧、--inquiry と --accept/--reject/--body で 1 件を決める"
    )
    v.add_argument("run_id", nargs="?")
    v.add_argument("--inquiry", help="問い合わせ ID")
    g = v.add_mutually_exclusive_group()
    g.add_argument("--accept", action="store_true", help="返信案をそのまま採用")
    g.add_argument("--reject", action="store_true", help="却下（送らない）")
    g.add_argument("--body", help="修正後の本文ファイル（- で標準入力）を採用")
    v.add_argument("--reason", default="", help="判断の理由")
    v.add_argument("--outbox", default="outbox", help="採用した返信の出力先")
    v.set_defaults(fn=cmd_review)

    sr = sub.add_parser("shadow-report", help="本番と影のレビュー判定・警告数を並べる")
    sr.add_argument("run_id", nargs="?")
    sr.set_defaults(fn=cmd_shadow_report)

    a = p.parse_args(argv)
    return a.fn(a)
