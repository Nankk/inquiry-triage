"""CLI。run: 一周してキューを作る / show: キューと追跡ログを見る / review: 人の承認（次の change）。"""

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


def _print_queue(items: list[dict]) -> None:
    print(f"{'ID':8} {'緊急度':6} {'カテゴリ':10} {'担当':22} {'警告':4} 件名")
    for i in items:
        print(
            f"{i['inquiry_id']:8} {i['urgency']:6} {i['category']:10} "
            f"{(i['specialist'] or '-'):22} {len(i['warnings']):4} {i['subject']}"
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
    _print_queue(store.read_queue())
    return 0


def cmd_review(a: argparse.Namespace) -> int:
    print("review は次の change（approval-cli）で実装します", file=sys.stderr)
    return 2


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

    v = sub.add_parser("review", help="承認（採用・却下・修正）")
    v.add_argument("run_id", nargs="?")
    v.set_defaults(fn=cmd_review)

    a = p.parse_args(argv)
    return a.fn(a)
