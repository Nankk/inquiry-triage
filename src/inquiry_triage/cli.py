"""CLI。run: 一周してキューを作る / show: キューと追跡ログを見る / review: 人の承認（採用・却下・修正）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from inquiry_triage.llm import ReplayClient
from inquiry_triage.models import Inquiry
from inquiry_triage.orchestrator import Orchestrator
from inquiry_triage.retrieval import load_kb
from inquiry_triage.store import RunStore

FIX = Path("fixtures")


def cmd_run(a: argparse.Namespace) -> int:
    inquiries = [Inquiry.from_dict(d) for d in json.loads(Path(a.inbox).read_text(encoding="utf-8"))]
    store = RunStore(Path(a.runs))
    orch = Orchestrator(
        ReplayClient(Path(a.replay)),
        load_kb(Path(a.kb)),
        Path(a.policy).read_text(encoding="utf-8"),
        store,
        workers=a.workers,
    )
    items = orch.run(inquiries)
    print(f"run {store.run_id}: {len(items)} 件をキューに載せました → {store.dir}")
    _print_queue([i.to_dict() for i in items])
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

    a = p.parse_args(argv)
    return a.fn(a)
