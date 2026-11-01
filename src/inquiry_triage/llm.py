"""LLM 境界。全エージェントはここを通してのみ LLM を呼ぶ。実装は差し替え可能。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class LLMError(Exception):
    """LLM 呼び出しの失敗（fixture 欠落、API エラー等）。"""


class LLMClient(Protocol):
    def complete(self, agent: str, key: str, prompt: str) -> dict[str, Any]:
        """agent 名と業務キー（問い合わせ ID）で呼び出す。JSON 相当の dict を返す。"""
        ...


class ReplayClient:
    """fixture（<root>/<agent>/<key>.json）を返す。ネットワークも API キーも不要。"""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def complete(self, agent: str, key: str, prompt: str) -> dict[str, Any]:
        path = self.root / agent / f"{key}.json"
        if not path.exists():
            raise LLMError(f"fixture missing: {agent}/{key}.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise LLMError(f"fixture is not an object: {path}")
        return data


# LiveClient（OpenAI 互換エンドポイント）と RecordingClient（実出力を fixture に保存）は
# 次の change で追加する。インターフェースは上と同じ。
