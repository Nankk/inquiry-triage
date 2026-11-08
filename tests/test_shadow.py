"""シャドーモード。spec の 8 シナリオを 1 本ずつ。並列に走る段は順序が入れ替わるので step 名で絞る。"""

import json
from pathlib import Path

import pytest

from inquiry_triage.cli import main
from inquiry_triage.store import RunStore

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def cwd(monkeypatch):
    monkeypatch.chdir(FIX.parent)


def _run(runs: Path, *args) -> RunStore:
    assert main(["--runs", str(runs), "run", *args]) == 0
    return RunStore(runs, RunStore.latest(runs))


def _steps(store: RunStore, inquiry_id: str, step: str) -> list[dict]:
    return [s for s in store.read_steps() if s["inquiry_id"] == inquiry_id and s["step"] == step]


def _item(store: RunStore, inquiry_id: str) -> dict:
    return next(i for i in store.read_queue() if i["inquiry_id"] == inquiry_id)


def test_shadow_runs_and_queue_unchanged(cwd, tmp_path):
    plain = _run(tmp_path / "a")
    shadowed = _run(tmp_path / "b", "--shadow-config", str(FIX / "shadow.json"))
    (sd,) = _steps(shadowed, "INQ-001", "shadow_draft")
    assert sd["agent"] == "billing_specialist_v2" and sd["status"] == "ok"
    assert len(_steps(shadowed, "INQ-001", "shadow_review")) == 1
    assert len(_steps(shadowed, "INQ-001", "shadow_verify")) == 1
    (d,) = _steps(shadowed, "INQ-001", "draft")
    assert d["input"]["articles"] == sd["input"]["articles"]
    a, b = _item(plain, "INQ-001"), _item(shadowed, "INQ-001")
    assert (a["draft"], a["warnings"]) == (b["draft"], b["warnings"])
    assert b["shadow"] == {"agent": "billing_specialist_v2", "verdict": "pass", "warnings": 0, "failed": None}


def test_other_category_has_no_shadow(cwd, tmp_path):
    store = _run(tmp_path, "--shadow-config", str(FIX / "shadow.json"))
    assert not [
        s for s in store.read_steps() if s["inquiry_id"] == "INQ-002" and s["step"].startswith("shadow")
    ]
    assert _item(store, "INQ-002")["shadow"] is None


def test_no_config_means_no_shadow(cwd, tmp_path):
    store = _run(tmp_path)
    assert not [s for s in store.read_steps() if s["step"].startswith("shadow")]
    assert all(i["shadow"] is None for i in store.read_queue())


def test_missing_shadow_fixture_is_isolated(cwd, tmp_path):
    plain = _run(tmp_path / "a")
    shadowed = _run(tmp_path / "b", "--shadow-config", str(FIX / "shadow.json"))
    (sd,) = _steps(shadowed, "INQ-004", "shadow_draft")  # billing_specialist_v2/INQ-004.json は意図的に無い
    assert sd["status"] == "failed" and "fixture missing" in sd["reason"]
    assert _steps(shadowed, "INQ-004", "shadow_review") == []
    assert _steps(shadowed, "INQ-004", "shadow_verify") == []
    a, b = _item(plain, "INQ-004"), _item(shadowed, "INQ-004")
    assert (a["draft"], a["warnings"]) == (b["draft"], b["warnings"])
    assert b["shadow"]["failed"].startswith("LLMError")


def test_shadow_review_failure_alone(cwd, tmp_path):
    # 影の返信案はあるが影のレビュー fixture だけ無い replay を組む
    import shutil

    replay = tmp_path / "replay"
    shutil.copytree(FIX / "replay", replay)
    (replay / "reviewer" / "INQ-001.shadow.json").unlink()
    plain = _run(tmp_path / "a")
    shadowed = _run(tmp_path / "b", "--replay", str(replay), "--shadow-config", str(FIX / "shadow.json"))
    (rv,) = _steps(shadowed, "INQ-001", "shadow_review")
    (vf,) = _steps(shadowed, "INQ-001", "shadow_verify")
    assert rv["status"] == "failed" and vf["status"] == "ok"
    a, b = _item(plain, "INQ-001"), _item(shadowed, "INQ-001")
    assert (a["draft"], a["warnings"]) == (b["draft"], b["warnings"])
    assert b["shadow"]["verdict"].startswith("失敗") and b["shadow"]["warnings"] == 0


def test_unknown_shadow_name_stops_before_run(cwd, tmp_path, capsys):
    cfg = tmp_path / "bad.json"
    cfg.write_text('{"billing": "nobody"}', encoding="utf-8")
    runs = tmp_path / "runs"
    assert main(["--runs", str(runs), "run", "--shadow-config", str(cfg)]) == 2
    assert "nobody" in capsys.readouterr().err
    assert not runs.exists()


def test_shadow_report_table(cwd, tmp_path, capsys):
    store = _run(tmp_path, "--shadow-config", str(FIX / "shadow.json"))
    capsys.readouterr()
    assert main(["--runs", str(tmp_path), "shadow-report"]) == 0
    out = capsys.readouterr().out
    l1 = next(ln for ln in out.splitlines() if ln.startswith("INQ-001"))
    l4 = next(ln for ln in out.splitlines() if ln.startswith("INQ-004"))
    assert "billing_specialist " in l1 and "billing_specialist_v2" in l1 and "pass" in l1
    assert "失敗" in l4 and "fixture missing" in l4
    assert out.splitlines()[-1].startswith("合計 2 件")
    assert "影 pass 1" in out.splitlines()[-1]
    del store


def test_show_inquiry_lists_both_paths(cwd, tmp_path, capsys):
    _run(tmp_path, "--shadow-config", str(FIX / "shadow.json"))
    capsys.readouterr()
    assert main(["--runs", str(tmp_path), "show", "--inquiry", "INQ-001"]) == 0
    lines = [json.loads(ln) for ln in capsys.readouterr().out.splitlines() if ln.startswith('{"')]
    steps = {ln["step"]: ln for ln in lines}
    assert {"draft", "shadow_draft", "review", "shadow_review"} <= set(steps)
    assert steps["draft"]["output"]["body"] != steps["shadow_draft"]["output"]["body"]
    assert steps["review"]["output"]["verdict"] and steps["shadow_review"]["output"]["verdict"]


def test_routing_config_promotes_shadow(cwd, tmp_path):
    routing = tmp_path / "routing.json"
    routing.write_text('{"billing": "billing_specialist_v2"}', encoding="utf-8")
    store = _run(tmp_path / "r", "--routing-config", str(routing), "--only", "INQ-001")
    (d,) = _steps(store, "INQ-001", "draft")
    assert d["agent"] == "billing_specialist_v2"
    assert _steps(store, "INQ-001", "shadow_draft") == []
    assert _item(store, "INQ-001")["specialist"] == "billing_specialist_v2"


def test_routing_equal_to_shadow_is_refused(cwd, tmp_path):
    routing = tmp_path / "routing.json"
    routing.write_text('{"billing": "billing_specialist_v2"}', encoding="utf-8")
    rc = main(
        [
            "--runs",
            str(tmp_path / "r"),
            "run",
            "--routing-config",
            str(routing),
            "--shadow-config",
            str(FIX / "shadow.json"),
        ]
    )
    assert rc == 2
    assert not (tmp_path / "r").exists() or not any((tmp_path / "r").iterdir())
