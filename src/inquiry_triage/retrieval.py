"""根拠記事の決定論的取得。LLM には該当記事だけを渡す（文脈の物理削除）。"""

from __future__ import annotations

import json
from pathlib import Path

from inquiry_triage.models import Article

LIMIT = 5


def load_kb(path: Path) -> list[Article]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Article.from_dict(d) for d in data]


def retrieve(kb: list[Article], category: str, text: str, limit: int = LIMIT) -> list[Article]:
    """カテゴリ内でキーワードが本文に現れる記事。無ければ同カテゴリ全記事（上限付き）に倒す。"""
    same = [a for a in kb if a.category == category]
    hit = [a for a in same if any(k in text for k in a.keywords)]
    return (hit or same)[:limit]
