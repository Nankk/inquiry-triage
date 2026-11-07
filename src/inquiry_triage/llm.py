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


def parse_json_content(text: str) -> dict[str, Any]:
    """モデルの返答本文から JSON オブジェクトを取り出す。```json フェンスは剥がす。"""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    try:
        data = json.loads(t)
    except json.JSONDecodeError as e:
        raise LLMError(f"response is not JSON: {e}: {text[:200]!r}") from e
    if not isinstance(data, dict):
        raise LLMError("response is not an object")
    return data


class LiveClient:
    """OpenAI 互換の chat/completions を標準ライブラリだけで呼ぶ。接続先・鍵・モデルは環境変数。

    INQUIRY_TRIAGE_BASE_URL  例: https://example.com/v1
    INQUIRY_TRIAGE_API_KEY
    INQUIRY_TRIAGE_MODEL
    """

    SYSTEM = (
        "出力は指示された JSON オブジェクトだけを返してください。前置きや説明文、コードフェンスは不要です。"
    )

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> LiveClient:
        import os

        missing = [
            k
            for k in ("INQUIRY_TRIAGE_BASE_URL", "INQUIRY_TRIAGE_API_KEY", "INQUIRY_TRIAGE_MODEL")
            if not os.environ.get(k)
        ]
        if missing:
            raise LLMError(f"environment variables missing: {', '.join(missing)}")
        return cls(
            os.environ["INQUIRY_TRIAGE_BASE_URL"],
            os.environ["INQUIRY_TRIAGE_API_KEY"],
            os.environ["INQUIRY_TRIAGE_MODEL"],
        )

    def complete(self, agent: str, key: str, prompt: str) -> dict[str, Any]:
        import urllib.error
        import urllib.request

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": prompt},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise LLMError(f"HTTP {e.code} from {agent}/{key}: {e.read()[:300]!r}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise LLMError(f"request failed for {agent}/{key}: {e}") from e
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"unexpected response shape: {str(body)[:300]}") from e
        return parse_json_content(content)


class RecordingClient:
    """内側のクライアントを呼び、返った dict を fixture（<root>/<agent>/<key>.json）に保存する。
    実行後は ReplayClient で同じ結果を再現できる。失敗は保存せず、そのまま失敗として伝える。"""

    def __init__(self, inner: LLMClient, root: Path) -> None:
        self.inner = inner
        self.root = Path(root)

    def complete(self, agent: str, key: str, prompt: str) -> dict[str, Any]:
        data = self.inner.complete(agent, key, prompt)
        path = self.root / agent / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return data
