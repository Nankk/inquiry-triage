"""人の承認。CLI を main() 経由で動かし、decisions.jsonl・outbox・状態の導出を確認する。"""

import json
from pathlib import Path

import pytest

from inquiry_triage.cli import main
from inquiry_triage.store import RunStore

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.chdir(FIX.parent)  # fixtures/ の既定パスをそのまま使う
    runs, outbox = tmp_path / "runs", tmp_path / "outbox"
    assert main(["--runs", str(runs), "run"]) == 0
    run_id = RunStore.latest(runs)
    store = RunStore(runs, run_id)
    steps_before = (store.dir / "steps.jsonl").read_bytes()
    queue_before = (store.dir / "queue.json").read_bytes()

    def review(*args):
        return main(["--runs", str(runs), "review", "--outbox", str(outbox), *args])

    return {
        "review": review,
        "store": store,
        "outbox": outbox / run_id,
        "unchanged": lambda: (
            (store.dir / "steps.jsonl").read_bytes() == steps_before
            and (store.dir / "queue.json").read_bytes() == queue_before
        ),
    }


def test_accept_writes_decision_and_outbox(env):
    assert env["review"]("--inquiry", "INQ-001", "--accept", "--reason", "記事どおり") == 0
    (d,) = env["store"].read_decisions()
    assert {d["inquiry_id"], d["action"], d["reason"]} == {"INQ-001", "accepted", "記事どおり"}
    assert "ts" in d
    out = (env["outbox"] / "INQ-001.txt").read_text(encoding="utf-8")
    assert out.startswith("To: 佐藤 美咲\nSubject: Re: 同じ月に 2 回請求されています\n\n")
    assert d["body"] in out
    assert env["unchanged"]()


def test_reject_records_but_sends_nothing(env):
    assert env["review"]("--inquiry", "INQ-004", "--reject", "--reason", "返金の確約") == 0
    assert env["store"].statuses() == {"INQ-004": "rejected"}
    assert not env["outbox"].exists()
    assert env["unchanged"]()


def test_edit_keeps_original_draft(env, tmp_path):
    body = tmp_path / "body.txt"
    body.write_text("鈴木様\n\n手順をご案内します。\n", encoding="utf-8")
    assert env["review"]("--inquiry", "INQ-003", "--body", str(body)) == 0
    (d,) = env["store"].read_decisions()
    assert d["action"] == "edited"
    assert (env["outbox"] / "INQ-003.txt").read_text(encoding="utf-8").endswith("手順をご案内します。\n")
    draft = next(i for i in env["store"].read_queue() if i["inquiry_id"] == "INQ-003")["draft"]
    assert draft["body"] != d["body"]  # 元の返信案は queue.json に残る
    assert env["unchanged"]()


def test_latest_decision_wins(env):
    env["review"]("--inquiry", "INQ-001", "--accept")
    env["review"]("--inquiry", "INQ-001", "--reject", "--reason", "やはり保留")
    assert len(env["store"].read_decisions()) == 2  # 追記のみ
    assert env["store"].statuses()["INQ-001"] == "rejected"


def test_accept_without_draft_is_refused(env):
    assert env["review"]("--inquiry", "INQ-005", "--accept") == 2
    assert env["store"].read_decisions() == []


def test_unknown_inquiry_is_refused(env):
    assert env["review"]("--inquiry", "INQ-999", "--accept") == 2


def test_listing_pending_only(env, capsys):
    env["review"]("--inquiry", "INQ-001", "--accept")
    capsys.readouterr()
    assert env["review"]() == 0
    out = capsys.readouterr().out
    assert "[INQ-001]" not in out
    assert "[INQ-002]" in out and "[INQ-005]" in out
    assert "--- 返信案 ---" in out


def test_show_derives_status(env, capsys):
    env["review"]("--inquiry", "INQ-002", "--reject")
    capsys.readouterr()
    assert main(["--runs", str(env["store"].dir.parent), "show"]) == 0
    line = next(ln for ln in capsys.readouterr().out.splitlines() if ln.startswith("INQ-002"))
    assert "rejected" in line
    assert json.loads((env["store"].dir / "queue.json").read_text(encoding="utf-8"))[0]["status"] == "pending"


def test_show_on_missing_run_is_clean(tmp_path, capsys):
    runs = tmp_path / "runs"
    assert main(["--runs", str(runs), "show", "bogus"]) == 1
    assert not (runs / "bogus").exists()  # 読むだけでディレクトリは作らない
    assert main(["--runs", str(runs), "show"]) == 1  # runs/ 自体が無くてもトレースバックにならない
    assert "実行がありません" in capsys.readouterr().err
