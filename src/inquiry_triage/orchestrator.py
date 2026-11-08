"""オーケストレータ。分岐・並列・失敗の隔離・記録はすべてここ（コード）で行う。LLM には任せない。"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from inquiry_triage.agents import Reviewer, Router, Specialist, build_specialists
from inquiry_triage.llm import LLMClient
from inquiry_triage.models import URGENCY_ORDER, Article, Draft, Inquiry, QueueItem, Review, Routing
from inquiry_triage.retrieval import retrieve
from inquiry_triage.store import RunStore
from inquiry_triage.verify import verify

HUMAN_DIRECT = "人が直接対応"


@dataclass
class Orchestrator:
    llm: LLMClient
    kb: list[Article]
    policy: str
    store: RunStore
    workers: int = 4
    shadow: dict[str, str] | None = None  # カテゴリ → 影のエージェント名（記録のみ、キューに出ない）
    router: Router = field(init=False)
    reviewer: Reviewer = field(init=False)
    specialists: dict[str, Specialist] = field(init=False)
    shadows: dict[str, Specialist] = field(init=False)

    def __post_init__(self) -> None:
        self.router = Router(self.llm)
        self.reviewer = Reviewer(self.llm)
        self.specialists = build_specialists(self.llm)
        self.shadows = build_specialists(self.llm, self.shadow) if self.shadow else {}

    # --- 記録付きの 1 段 -------------------------------------------------
    def _step(
        self,
        step: str,
        agent: str,
        inquiry_id: str,
        input_ref: dict[str, Any],
        fn: Callable[[], Any],
        serialize: Callable[[Any], Any] = lambda x: x,
    ) -> tuple[Any | None, str | None]:
        """fn を実行し、成否に関わらず 1 行記録する。失敗は (None, 理由) で返し、例外は外に出さない。"""
        t0 = time.perf_counter()
        try:
            out = fn()
            self.store.append_step(
                {
                    "step": step,
                    "agent": agent,
                    "inquiry_id": inquiry_id,
                    "input": input_ref,
                    "output": serialize(out),
                    "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "status": "ok",
                }
            )
            return out, None
        except Exception as e:  # noqa: BLE001 — 失敗を隔離して記録するのが目的
            reason = f"{type(e).__name__}: {e}"
            self.store.append_step(
                {
                    "step": step,
                    "agent": agent,
                    "inquiry_id": inquiry_id,
                    "input": input_ref,
                    "output": None,
                    "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "status": "failed",
                    "reason": reason,
                }
            )
            return None, reason

    # --- 問い合わせ 1 件 ------------------------------------------------
    def process_one(self, inq: Inquiry) -> QueueItem:
        warnings: list[str] = []

        routing, err = self._step(
            "route",
            self.router.name,
            inq.id,
            {"inquiry_id": inq.id},
            lambda: self.router.run({"inquiry": inq}),
            lambda r: r.__dict__,
        )
        if routing is None:
            return self._enqueue(inq, None, None, [], None, [f"分類失敗: {err}", HUMAN_DIRECT])
        assert isinstance(routing, Routing)

        specialist = self.specialists.get(routing.category)
        if specialist is None:
            return self._enqueue(
                inq, routing, None, [], None, [f"カテゴリ {routing.category} の担当なし", HUMAN_DIRECT]
            )

        articles, _ = self._step(
            "retrieve",
            "retriever",
            inq.id,
            {"category": routing.category},
            lambda: retrieve(self.kb, routing.category, inq.subject + "\n" + inq.body),
            lambda arts: [a.id for a in arts],
        )
        articles = articles or []
        candidate_ids = [a.id for a in articles]

        draft_input = {"inquiry_id": inq.id, "articles": candidate_ids}
        shadow_agent = self.shadows.get(routing.category)
        # 本番の返信案と影の経路を並列に。影は記録だけで、本番の結果に触らない。
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_draft = ex.submit(
                self._step,
                "draft",
                specialist.name,
                inq.id,
                draft_input,
                lambda: specialist.run({"inquiry": inq, "articles": articles}),
                lambda d: d.__dict__,
            )
            f_shadow = (
                ex.submit(self._shadow, shadow_agent, inq, articles, candidate_ids, draft_input)
                if shadow_agent
                else None
            )
        draft, err = f_draft.result()
        shadow = f_shadow.result() if f_shadow else None
        if draft is None:
            return self._enqueue(
                inq,
                routing,
                specialist.name,
                candidate_ids,
                None,
                [f"返信案の生成失敗: {err}", HUMAN_DIRECT],
                shadow,
            )
        assert isinstance(draft, Draft)

        # 検査は 2 系統を並列に。片方が失敗しても他方は残る。
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_review = ex.submit(
                self._step,
                "review",
                self.reviewer.name,
                inq.id,
                {"inquiry_id": inq.id},
                lambda: self.reviewer.run({"inquiry": inq, "draft": draft, "policy": self.policy}),
                lambda r: r.__dict__,
            )
            f_verify = ex.submit(
                self._step,
                "verify",
                "verifier",
                inq.id,
                {"candidates": candidate_ids},
                lambda: verify(draft, candidate_ids),
            )
        review, rerr = f_review.result()
        checks, _ = f_verify.result()

        warnings.extend(checks or [])
        if review is None:
            warnings.append(f"レビュー失敗: {rerr}")
        elif isinstance(review, Review) and review.verdict == "flag":
            warnings.extend(f"レビュー指摘: {r}" for r in review.reasons)

        return self._enqueue(inq, routing, specialist.name, candidate_ids, draft, warnings, shadow)

    # --- 影の経路 ---------------------------------------------------------
    def _shadow(
        self,
        agent: Specialist,
        inq: Inquiry,
        articles: list[Article],
        candidate_ids: list[str],
        draft_input: dict[str, Any],
    ) -> dict[str, Any]:
        """影の担当に同じ入力で返信案を書かせ、同じ 2 系統で検査する。結果は記録と要約だけ。"""
        summary: dict[str, Any] = {"agent": agent.name, "verdict": None, "warnings": None, "failed": None}
        draft, err = self._step(
            "shadow_draft",
            agent.name,
            inq.id,
            draft_input,
            lambda: agent.run({"inquiry": inq, "articles": articles}),
            lambda d: d.__dict__,
        )
        if draft is None:
            summary["failed"] = err
            return summary
        assert isinstance(draft, Draft)
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_review = ex.submit(
                self._step,
                "shadow_review",
                self.reviewer.name,
                inq.id,
                {"inquiry_id": inq.id, "key": f"{inq.id}.shadow"},
                lambda: self.reviewer.run(
                    {"inquiry": inq, "draft": draft, "policy": self.policy, "key": f"{inq.id}.shadow"}
                ),
                lambda r: r.__dict__,
            )
            f_verify = ex.submit(
                self._step,
                "shadow_verify",
                "verifier",
                inq.id,
                {"candidates": candidate_ids},
                lambda: verify(draft, candidate_ids),
            )
        review, rerr = f_review.result()
        checks, _ = f_verify.result()
        summary["warnings"] = len(checks or [])
        summary["verdict"] = review.verdict if isinstance(review, Review) else f"失敗: {rerr}"
        return summary

    def _enqueue(
        self,
        inq: Inquiry,
        routing: Routing | None,
        specialist: str | None,
        candidate_ids: list[str],
        draft: Draft | None,
        warnings: list[str],
        shadow: dict[str, Any] | None = None,
    ) -> QueueItem:
        item = QueueItem(
            inquiry_id=inq.id,
            customer=inq.customer,
            subject=inq.subject,
            urgency=routing.urgency if routing else "high",  # 分類できないものは先頭に出す
            category=routing.category if routing else "unknown",
            specialist=specialist,
            candidate_ids=candidate_ids,
            draft=draft.__dict__ if draft else None,
            warnings=warnings,
            shadow=shadow,
        )
        self.store.append_step(
            {
                "step": "enqueue",
                "agent": "orchestrator",
                "inquiry_id": inq.id,
                "input": {},
                "output": {"urgency": item.urgency, "warnings": len(warnings)},
                "status": "ok",
            }
        )
        return item

    # --- バッチ ---------------------------------------------------------
    def run(self, inquiries: list[Inquiry]) -> list[QueueItem]:
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            items = list(ex.map(self.process_one, inquiries))
        items.sort(key=lambda i: (URGENCY_ORDER.get(i.urgency, 9), i.inquiry_id))
        self.store.write_queue([i.to_dict() for i in items])
        return items
