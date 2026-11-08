"""実行ログ。追記専用 JSONL。後段が前段を書き換えない。"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


class RunStore:
    """runs/<run_id>/ の読み書き。ディレクトリは最初の書き込みで作る（読むだけなら副作用なし）。"""

    def __init__(self, runs_root: Path, run_id: str | None = None) -> None:
        self.run_id = run_id or new_run_id()
        self.dir = Path(runs_root) / self.run_id
        self._lock = threading.Lock()

    def exists(self) -> bool:
        return (self.dir / "queue.json").is_file()

    @classmethod
    def open(cls, runs_root: Path, run_id: str | None) -> RunStore | None:
        """既存の実行を開く。run_id が None なら最新。無ければ None。"""
        run_id = run_id or cls.latest(runs_root)
        if not run_id:
            return None
        store = cls(runs_root, run_id)
        return store if store.exists() else None

    def append_step(self, record: dict[str, Any]) -> None:
        record = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), **record}
        line = json.dumps(record, ensure_ascii=False)
        self.dir.mkdir(parents=True, exist_ok=True)
        with self._lock, (self.dir / "steps.jsonl").open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def append_decision(self, record: dict[str, Any]) -> None:
        record = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), **record}
        self.dir.mkdir(parents=True, exist_ok=True)
        with self._lock, (self.dir / "decisions.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def write_queue(self, items: list[dict[str, Any]]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "queue.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def read_queue(self) -> list[dict[str, Any]]:
        return json.loads((self.dir / "queue.json").read_text(encoding="utf-8"))

    def read_decisions(self) -> list[dict[str, Any]]:
        p = self.dir / "decisions.jsonl"
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line]

    def statuses(self) -> dict[str, str]:
        """問い合わせ ID → 最新の判断。queue.json は書き換えず、状態は decisions.jsonl から導く。"""
        return {d["inquiry_id"]: d["action"] for d in self.read_decisions()}

    def read_steps(self) -> list[dict[str, Any]]:
        p = self.dir / "steps.jsonl"
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line]

    @staticmethod
    def latest(runs_root: Path) -> str | None:
        root = Path(runs_root)
        if not root.is_dir():
            return None
        runs = sorted(p.name for p in root.iterdir() if (p / "queue.json").is_file())
        return runs[-1] if runs else None
