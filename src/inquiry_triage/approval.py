"""人の判断（採用・却下・修正）。CLI の review と HTTP API が同じ関数を通る。
decisions.jsonl への追記と outbox への出力だけを行い、queue.json と steps.jsonl は書き換えない。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from inquiry_triage.store import RunStore

ACTIONS = ("accepted", "rejected", "edited")


class ApprovalError(ValueError):
    """判断が成立しない（未知の ID、返信案の無い項目の採用、不正な操作）。"""


def decide(
    store: RunStore,
    inquiry_id: str,
    action: str,
    reason: str = "",
    body: str | None = None,
    outbox_root: Path | str = "outbox",
) -> dict[str, Any]:
    """1 件を決める。accepted は返信案の本文を、edited は body をそのまま outbox に出す。rejected は記録のみ。"""
    if action not in ACTIONS:
        raise ApprovalError(f"操作は {', '.join(ACTIONS)} のどれかです: {action!r}")
    item = next((i for i in store.read_queue() if i["inquiry_id"] == inquiry_id), None)
    if item is None:
        raise ApprovalError(f"{inquiry_id} はこの実行のキューにありません")
    if action == "edited":
        if not body or not body.strip():
            raise ApprovalError("修正には本文が必要です")
    elif action == "accepted":
        if not item["draft"]:
            raise ApprovalError(f"{inquiry_id} に返信案がありません。修正として本文を渡してください")
        body = item["draft"]["body"]
    else:
        body = None

    record = {"inquiry_id": inquiry_id, "action": action, "reason": reason, "body": body}
    store.append_decision(record)
    out_path: Path | None = None
    if body is not None:
        out_path = Path(outbox_root) / store.run_id / f"{inquiry_id}.txt"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            f"To: {item['customer']}\nSubject: Re: {item['subject']}\n\n{body.rstrip()}\n", encoding="utf-8"
        )
    return {**record, "outbox": str(out_path) if out_path else None}
