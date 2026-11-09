"""ReplayClient で一周させ、LLM 前後の決定論的処理を確認する。"""

import json
from pathlib import Path

import pytest

from inquiry_triage.llm import ReplayClient
from inquiry_triage.models import Draft, Inquiry
from inquiry_triage.orchestrator import HUMAN_DIRECT, Orchestrator
from inquiry_triage.retrieval import load_kb, retrieve
from inquiry_triage.store import RunStore
from inquiry_triage.verify import verify

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def run(tmp_path):
    kb = load_kb(FIX / "kb.json")
    store = RunStore(tmp_path)
    orch = Orchestrator(
        ReplayClient(FIX / "replay"), kb, (FIX / "policy.md").read_text(encoding="utf-8"), store
    )
    inquiries = [Inquiry.from_dict(d) for d in json.loads((FIX / "inbox.json").read_text(encoding="utf-8"))]
    return {i.inquiry_id: i for i in orch.run(inquiries)}, store


def test_all_inquiries_reach_queue(run):
    items, _ = run
    assert set(items) == {f"INQ-00{n}" for n in range(1, 6)}


def test_queue_items_carry_inquiry_body(run):
    """人が返信案と見比べるため、queue.json の各項目に inbox の本文がそのまま入る（show-inquiry-body）。"""
    _, store = run
    inbox = {d["id"]: d["body"] for d in json.loads((FIX / "inbox.json").read_text(encoding="utf-8"))}
    recorded = {i["inquiry_id"]: i["body"] for i in store.read_queue()}
    assert recorded == inbox


def test_other_category_goes_to_human(run):
    items, _ = run
    assert items["INQ-005"].specialist is None
    assert HUMAN_DIRECT in items["INQ-005"].warnings


def test_missing_reviewer_fixture_is_isolated(run):
    items, store = run
    w = items["INQ-004"].warnings
    assert any(x.startswith("レビュー失敗") for x in w)
    assert any("KB-B09" in x for x in w)  # 存在しない引用
    assert any("返金の確約" in x for x in w)
    assert any("プレースホルダ" in x for x in w)
    failed = [s for s in store.read_steps() if s["status"] == "failed"]
    assert [s["inquiry_id"] for s in failed] == ["INQ-004"]


def test_review_flag_becomes_warning_not_rewrite(run):
    items, store = run
    assert any(x.startswith("レビュー指摘") for x in items["INQ-002"].warnings)
    drafts = [s for s in store.read_steps() if s["step"] == "draft" and s["inquiry_id"] == "INQ-002"]
    assert len(drafts) == 1  # 書き直しは起きない


def test_urgent_first(run):
    _, store = run
    urgencies = [i["urgency"] for i in store.read_queue()]
    assert "high" in urgencies
    assert urgencies == sorted(urgencies, key=lambda u: {"high": 0, "normal": 1, "low": 2}[u])


def test_retrieve_keyword_then_fallback():
    kb = load_kb(FIX / "kb.json")
    assert [a.id for a in retrieve(kb, "billing", "二重に請求された")] == ["KB-B01"]
    assert {a.id for a in retrieve(kb, "billing", "関係ない話")} == {"KB-B01", "KB-B02"}


def test_verify_rules():
    d = Draft("3 営業日以内に必ず全額返金いたします {{x}}", ("KB-Z1",), (), "low")
    w = verify(d, ["KB-B01"])
    assert len(w) == 6


def test_schema_error_is_isolated(tmp_path):
    """spec inquiry-routing「構造化出力の検証失敗」: 分類が未知のカテゴリを返した 1 件だけ人に回り、他は続く。"""
    import shutil

    replay = tmp_path / "replay"
    shutil.copytree(FIX / "replay", replay)
    broken = json.loads((replay / "router" / "INQ-003.json").read_text(encoding="utf-8"))
    broken["category"] = "shipping"
    (replay / "router" / "INQ-003.json").write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
    store = RunStore(tmp_path / "runs")
    orch = Orchestrator(
        ReplayClient(replay), load_kb(FIX / "kb.json"), (FIX / "policy.md").read_text(encoding="utf-8"), store
    )
    inquiries = [Inquiry.from_dict(d) for d in json.loads((FIX / "inbox.json").read_text(encoding="utf-8"))]
    items = {i.inquiry_id: i for i in orch.run(inquiries)}
    assert len(items) == 5
    assert items["INQ-003"].specialist is None and HUMAN_DIRECT in items["INQ-003"].warnings
    (route,) = [s for s in store.read_steps() if s["inquiry_id"] == "INQ-003" and s["step"] == "route"]
    assert route["status"] == "failed" and "SchemaError" in route["reason"]
    assert items["INQ-001"].draft is not None  # 他は普通に進む


def test_facts_keep_json_values(run):
    _, store = run
    (route,) = [s for s in store.read_steps() if s["inquiry_id"] == "INQ-001" and s["step"] == "route"]
    assert route["output"]["facts"]["billing_dates"] == ["10/5", "10/6"]  # 配列が文字列化されない
