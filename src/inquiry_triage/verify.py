"""決定論的検証。LLM に聞かずに判定できることはここで判定する。逸脱は警告であり自動では直さない。"""

from __future__ import annotations

import re

from inquiry_triage.models import Draft

MAX_BODY_CHARS = 800

# (正規表現, 警告ラベル)。規程 fixtures/policy.md と対応させる。
FORBIDDEN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(全額)?返金(いたし|し)ます"), "返金の確約"),
    (re.compile(r"(本日中|明日中|\d+\s*(営業)?日以内|\d+日まで)に"), "期日の約束"),
    (re.compile(r"必ず|確実に|保証(いた|し)ます"), "断定表現"),
)
PLACEHOLDER = re.compile(r"\{\{.*?\}\}|\[\[.*?\]\]|<<.*?>>")


def verify(draft: Draft, candidate_ids: list[str]) -> list[str]:
    warnings: list[str] = []
    unknown = [c for c in draft.cited if c not in candidate_ids]
    if unknown:
        warnings.append("引用記事が候補に無い: " + ", ".join(unknown))
    if not draft.cited:
        warnings.append("根拠記事の引用が無い")
    for pat, label in FORBIDDEN:
        m = pat.search(draft.body)
        if m:
            warnings.append(f"禁止表現: {label}（「{m.group(0)}」）")
    if len(draft.body) > MAX_BODY_CHARS:
        warnings.append(f"本文が長い: {len(draft.body)} 文字 > {MAX_BODY_CHARS}")
    if PLACEHOLDER.search(draft.body):
        warnings.append("プレースホルダが残っている")
    if draft.confidence == "low":
        warnings.append("専門エージェントの確信度が low")
    return warnings
