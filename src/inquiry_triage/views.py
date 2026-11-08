"""読み取り側の整形。CLI（show / review / shadow-report）と HTTP API が同じ関数を使う。store は書き換えない。"""

from __future__ import annotations

from typing import Any

from inquiry_triage.store import RunStore


def queue_view(store: RunStore) -> list[dict[str, Any]]:
    """queue.json の項目に、decisions.jsonl から導いた最新の状態を合成する。順序は queue.json のまま。"""
    statuses = store.statuses()
    items = []
    for i in store.read_queue():
        item = dict(i)
        item["status"] = statuses.get(i["inquiry_id"], i.get("status", "pending"))
        items.append(item)
    return items


def inquiry_view(store: RunStore, inquiry_id: str) -> dict[str, Any] | None:
    """1 件分: 全段のログ（影の段を含む）、キュー項目、判断の履歴。キューに無ければ None。"""
    item = next((i for i in queue_view(store) if i["inquiry_id"] == inquiry_id), None)
    if item is None:
        return None
    return {
        "item": item,
        "steps": [s for s in store.read_steps() if s["inquiry_id"] == inquiry_id],
        "decisions": [d for d in store.read_decisions() if d["inquiry_id"] == inquiry_id],
    }


def _verdict(step: dict[str, Any] | None) -> str | None:
    if step is None:
        return None
    return step["output"]["verdict"] if step["status"] == "ok" else "失敗"


def shadow_report(store: RunStore) -> dict[str, Any]:
    """影が走った問い合わせごとに、本番と影のレビュー判定・警告数を並べる。昇格判断の材料。"""
    reviews = {s["inquiry_id"]: s for s in store.read_steps() if s["step"] == "review"}
    rows: list[dict[str, Any]] = []
    tot = {
        "count": 0,
        "main_pass": 0,
        "main_warnings": 0,
        "shadow_pass": 0,
        "shadow_warnings": 0,
        "shadow_failed": 0,
    }
    for i in store.read_queue():
        sh = i.get("shadow")
        if not sh:
            continue
        mv = _verdict(reviews.get(i["inquiry_id"]))
        row = {
            "inquiry_id": i["inquiry_id"],
            "category": i["category"],
            "main": {"agent": i["specialist"], "verdict": mv, "warnings": len(i["warnings"])},
            "shadow": {
                "agent": sh["agent"],
                "verdict": None if sh["failed"] else sh["verdict"],
                "warnings": None if sh["failed"] else sh["warnings"],
                "failed": sh["failed"],
            },
        }
        rows.append(row)
        tot["count"] += 1
        tot["main_pass"] += mv == "pass"
        tot["main_warnings"] += len(i["warnings"])
        if sh["failed"]:
            tot["shadow_failed"] += 1
        else:
            tot["shadow_pass"] += sh["verdict"] == "pass"
            tot["shadow_warnings"] += sh["warnings"]
    return {"run_id": store.run_id, "rows": rows, "totals": tot}
