"""データ構造。エージェント出力はここで検証してから先へ渡す（境界での構造化出力検証）。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CATEGORIES = ("billing", "technical", "account", "other")
URGENCIES = ("low", "normal", "high")
CONFIDENCES = ("high", "medium", "low")
VERDICTS = ("pass", "flag")
URGENCY_ORDER = {"high": 0, "normal": 1, "low": 2}


class SchemaError(ValueError):
    """LLM 出力が期待する構造を満たさない。"""


def _str(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise SchemaError(f"'{key}' must be a non-empty string")
    return v


def _enum(d: dict[str, Any], key: str, allowed: tuple[str, ...]) -> str:
    v = _str(d, key)
    if v not in allowed:
        raise SchemaError(f"'{key}'={v!r} not in {allowed}")
    return v


def _str_list(d: dict[str, Any], key: str) -> tuple[str, ...]:
    v = d.get(key, [])
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        raise SchemaError(f"'{key}' must be a list of strings")
    return tuple(v)


@dataclass(frozen=True)
class Inquiry:
    id: str
    customer: str
    subject: str
    body: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Inquiry:
        return cls(_str(d, "id"), _str(d, "customer"), _str(d, "subject"), _str(d, "body"))


@dataclass(frozen=True)
class Article:
    id: str
    category: str
    title: str
    keywords: tuple[str, ...]
    body: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Article:
        return cls(
            _str(d, "id"),
            _enum(d, "category", CATEGORIES),
            _str(d, "title"),
            _str_list(d, "keywords"),
            _str(d, "body"),
        )


@dataclass(frozen=True)
class Routing:
    """分類エージェントの出力。"""

    category: str
    urgency: str
    summary: str
    facts: dict[str, Any] = field(default_factory=dict)  # JSON の値をそのまま持つ（配列も可）

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Routing:
        facts = d.get("facts", {})
        if not isinstance(facts, dict):
            raise SchemaError("'facts' must be an object")
        return cls(
            _enum(d, "category", CATEGORIES),
            _enum(d, "urgency", URGENCIES),
            _str(d, "summary"),
            {str(k): v for k, v in facts.items()},
        )


@dataclass(frozen=True)
class Draft:
    """専門エージェントの出力。cited は渡した候補記事の ID に限る（検証は verify 側）。"""

    body: str
    cited: tuple[str, ...]
    ask_customer: tuple[str, ...]
    confidence: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Draft:
        return cls(
            _str(d, "body"),
            _str_list(d, "cited"),
            _str_list(d, "ask_customer"),
            _enum(d, "confidence", CONFIDENCES),
        )


@dataclass(frozen=True)
class Review:
    """レビューエージェントの出力。専門エージェントには戻さない。"""

    verdict: str
    reasons: tuple[str, ...]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Review:
        return cls(_enum(d, "verdict", VERDICTS), _str_list(d, "reasons"))


@dataclass
class QueueItem:
    """承認キューの 1 項目。人が見る単位。"""

    inquiry_id: str
    customer: str
    subject: str
    urgency: str
    category: str
    specialist: str | None
    candidate_ids: list[str]
    draft: dict[str, Any] | None
    warnings: list[str]
    status: str = "pending"
    shadow: dict[str, Any] | None = None  # 影の要約（agent, verdict, warnings, failed）。本文は steps.jsonl

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
