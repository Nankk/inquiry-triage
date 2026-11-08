"""エージェント。各エージェントは 1 つの仕事を構造化データで返すだけ。分岐・並列・記録はオーケストレータ。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from inquiry_triage.llm import LLMClient
from inquiry_triage.models import CATEGORIES, Article, Draft, Inquiry, Review, Routing


class Agent(Protocol):
    name: str

    def run(self, ctx: dict[str, Any]) -> Any: ...


def _inquiry_block(inq: Inquiry) -> str:
    return f"[問い合わせ {inq.id}]\n差出人: {inq.customer}\n件名: {inq.subject}\n本文:\n{inq.body}\n"


@dataclass
class Router:
    """分類エージェント。カテゴリ・緊急度・要約・事実を返す。"""

    llm: LLMClient
    name: str = "router"

    def run(self, ctx: dict[str, Any]) -> Routing:
        inq: Inquiry = ctx["inquiry"]
        prompt = (
            "あなたはカスタマーサポートの一次受付です。問い合わせを分類してください。\n"
            "出力は JSON: {category: billing|technical|account|other, urgency: low|normal|high, "
            "summary: 1 文, facts: {注文番号などの事実}}\n\n" + _inquiry_block(inq)
        )
        return Routing.from_dict(self.llm.complete(self.name, inq.id, prompt))


@dataclass
class Specialist:
    """専門エージェント。渡された候補記事だけを根拠に返信案を書く。"""

    llm: LLMClient
    name: str
    persona: str

    def run(self, ctx: dict[str, Any]) -> Draft:
        inq: Inquiry = ctx["inquiry"]
        articles: list[Article] = ctx["articles"]
        kb = "\n\n".join(f"[{a.id}] {a.title}\n{a.body}" for a in articles)
        prompt = (
            f"あなたは{self.persona}です。以下の FAQ 記事だけを根拠に返信案を書いてください。"
            "記事に無いことは書かず、顧客に確認が必要なら ask_customer に列挙してください。\n"
            "出力は JSON: {body: 返信本文, cited: [記事ID], ask_customer: [確認事項], "
            "confidence: high|medium|low}\n\n" + _inquiry_block(inq) + "\n[FAQ 記事]\n" + kb
        )
        return Draft.from_dict(self.llm.complete(self.name, inq.id, prompt))


@dataclass
class Reviewer:
    """レビューエージェント。規程と顧客感情の観点で pass/flag を返す。書き直しはしない。"""

    llm: LLMClient
    name: str = "reviewer"

    def run(self, ctx: dict[str, Any]) -> Review:
        inq: Inquiry = ctx["inquiry"]
        draft: Draft = ctx["draft"]
        policy: str = ctx["policy"]
        key: str = ctx.get("key", inq.id)  # 影のレビューは <ID>.shadow で既存と区別する
        prompt = (
            "あなたはサポート品質の監査担当です。返信案が規程に反していないか、顧客の状況に配慮しているかを"
            "判定してください。書き直しはせず、判定と理由だけを返します。\n"
            "出力は JSON: {verdict: pass|flag, reasons: [理由]}\n\n"
            + _inquiry_block(inq)
            + "\n[返信案]\n"
            + draft.body
            + "\n\n[規程]\n"
            + policy
        )
        return Review.from_dict(self.llm.complete(self.name, key, prompt))


# 利用できる専門エージェント: 名前 → 人格。新しい担当（影の候補を含む）はここに 1 行足す。
PERSONAS: dict[str, str] = {
    "billing_specialist": "請求・決済担当",
    "technical_specialist": "テクニカルサポート担当",
    "account_specialist": "アカウント管理担当",
    "billing_specialist_v2": (
        "請求・決済担当。処理や返金を確約する表現は使わず、担当者が確認したうえで連絡する旨を書く。"
        "顧客に確認したいことがあれば本文の冒頭で先に尋ねる"
    ),
}

# カテゴリ → 本番の専門エージェント名。影を昇格させるときはここの名前を書き換える。
SPECIALISTS: dict[str, str] = {
    "billing": "billing_specialist",
    "technical": "technical_specialist",
    "account": "account_specialist",
}


def build_specialist(llm: LLMClient, name: str) -> Specialist:
    return Specialist(llm, name, PERSONAS[name])


def build_specialists(llm: LLMClient, table: dict[str, str] | None = None) -> dict[str, Specialist]:
    """カテゴリ → Specialist。table を省くと本番の対応表、影の対応表を渡せば影の担当になる。"""
    return {cat: build_specialist(llm, name) for cat, name in (table or SPECIALISTS).items()}


def load_shadow_config(path: Path) -> dict[str, str]:
    """影の設定 {カテゴリ: 影のエージェント名}。未知の名前・カテゴリは実行前に ValueError で止める。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values()):
        raise ValueError(f"影の設定はカテゴリ→エージェント名の対応表にしてください: {path}")
    for cat, name in data.items():
        if cat not in CATEGORIES:
            raise ValueError(f"影の設定: 未知のカテゴリ {cat!r}（{', '.join(CATEGORIES)}）")
        if name not in PERSONAS:
            raise ValueError(f"影の設定: 未知のエージェント {name!r}（{', '.join(PERSONAS)}）")
    return data
