"""HTTP API。スレッドで本物のサーバーを立て、spec の web-api 6 シナリオを 1 本ずつ。"""

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from inquiry_triage.cli import main
from inquiry_triage.server import Settings, make_server
from inquiry_triage.store import RunStore

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def srv(tmp_path, monkeypatch):
    monkeypatch.chdir(FIX.parent)
    runs = tmp_path / "runs"
    assert main(["--runs", str(runs), "run", "--shadow-config", str(FIX / "shadow.json")]) == 0
    run_id = RunStore.latest(runs)
    settings = Settings(
        runs=runs,
        outbox=tmp_path / "outbox",
        routing_config=tmp_path / "routing.json",
        shadow_config=tmp_path / "shadow.json",
        web_dist=tmp_path / "dist",
    )
    (tmp_path / "shadow.json").write_text((FIX / "shadow.json").read_text(encoding="utf-8"), encoding="utf-8")
    httpd = make_server(settings, port=0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{httpd.server_port}"

    def call(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            base + path, data=data, method=method, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                raw = r.read().decode("utf-8")
                ctype = r.headers.get("Content-Type", "")
                return r.status, (json.loads(raw) if "json" in ctype else raw), ctype
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                return e.code, json.loads(raw), e.headers.get("Content-Type", "")
            except json.JSONDecodeError:
                return e.code, raw, e.headers.get("Content-Type", "")

    yield {
        "call": call,
        "run_id": run_id,
        "store": RunStore(runs, run_id),
        "tmp": tmp_path,
        "settings": settings,
    }
    httpd.shutdown()
    httpd.server_close()


def test_queue_matches_cli_order_and_has_status_and_shadow(srv):
    st, runs, _ = srv["call"]("GET", "/api/runs")
    assert st == 200 and runs[0]["run_id"] == srv["run_id"] and runs[0]["items"] == 5
    st, q, _ = srv["call"]("GET", f"/api/runs/{srv['run_id']}/queue")
    assert st == 200
    ids = [i["inquiry_id"] for i in q["items"]]
    assert ids == [i["inquiry_id"] for i in srv["store"].read_queue()]
    assert all(i["status"] == "pending" for i in q["items"])
    inq1 = next(i for i in q["items"] if i["inquiry_id"] == "INQ-001")
    assert inq1["shadow"]["agent"] == "billing_specialist_v2"
    st, latest, _ = srv["call"]("GET", "/api/runs/latest/queue")
    assert st == 200 and latest["run_id"] == srv["run_id"]


def test_inquiry_view_has_main_and_shadow_steps(srv):
    st, v, _ = srv["call"]("GET", f"/api/runs/{srv['run_id']}/inquiries/INQ-001")
    assert st == 200
    steps = {s["step"] for s in v["steps"]}
    assert {"draft", "shadow_draft", "review", "shadow_review", "verify", "shadow_verify"} <= steps
    assert v["item"]["inquiry_id"] == "INQ-001" and v["decisions"] == []
    st, _, _ = srv["call"]("GET", f"/api/runs/{srv['run_id']}/inquiries/INQ-999")
    assert st == 404


def test_reject_via_api_appends_decision_only(srv):
    before = (srv["store"].dir / "steps.jsonl").read_bytes(), (srv["store"].dir / "queue.json").read_bytes()
    st, d, _ = srv["call"](
        "POST",
        f"/api/runs/{srv['run_id']}/decisions",
        {"inquiry_id": "INQ-004", "action": "rejected", "reason": "確約"},
    )
    assert st == 200 and d["action"] == "rejected" and d["outbox"] is None
    assert len(srv["store"].read_decisions()) == 1
    assert not (srv["tmp"] / "outbox").exists()
    st, q, _ = srv["call"]("GET", f"/api/runs/{srv['run_id']}/queue")
    assert next(i for i in q["items"] if i["inquiry_id"] == "INQ-004")["status"] == "rejected"
    assert (
        (srv["store"].dir / "steps.jsonl").read_bytes(),
        (srv["store"].dir / "queue.json").read_bytes(),
    ) == before


def test_accept_and_edit_write_outbox(srv):
    st, d, _ = srv["call"](
        "POST", f"/api/runs/{srv['run_id']}/decisions", {"inquiry_id": "INQ-001", "action": "accepted"}
    )
    assert st == 200 and d["outbox"].endswith("INQ-001.txt")
    st, d, _ = srv["call"](
        "POST",
        f"/api/runs/{srv['run_id']}/decisions",
        {"inquiry_id": "INQ-003", "action": "edited", "body": "鈴木様\n\n手順です。"},
    )
    assert st == 200
    assert (
        (srv["tmp"] / "outbox" / srv["run_id"] / "INQ-003.txt")
        .read_text(encoding="utf-8")
        .endswith("手順です。\n")
    )


def test_invalid_decisions_are_4xx_and_not_recorded(srv):
    url = f"/api/runs/{srv['run_id']}/decisions"
    assert srv["call"]("POST", url, {"inquiry_id": "INQ-999", "action": "accepted"})[0] == 400
    assert srv["call"]("POST", url, {"inquiry_id": "INQ-005", "action": "accepted"})[0] == 400  # 返信案なし
    assert srv["call"]("POST", url, {"inquiry_id": "INQ-001", "action": "maybe"})[0] == 400
    assert srv["call"]("POST", url, {"inquiry_id": "INQ-001", "action": "edited", "body": "  "})[0] == 400
    assert srv["call"]("GET", "/api/runs/nope/queue")[0] == 404
    assert srv["store"].read_decisions() == []


def test_promote_writes_routing_and_clears_shadow(srv, tmp_path):
    st, cfg, _ = srv["call"]("GET", "/api/config")
    assert (
        st == 200
        and cfg["shadow"] == {"billing": "billing_specialist_v2"}
        and cfg["routing"]["billing"] == "billing_specialist"
    )
    st, r, _ = srv["call"]("POST", "/api/routing", {"category": "billing", "agent": "billing_specialist_v2"})
    assert st == 200 and r["routing"]["billing"] == "billing_specialist_v2" and r["shadow"] == {}
    assert json.loads((tmp_path / "routing.json").read_text(encoding="utf-8")) == {
        "billing": "billing_specialist_v2"
    }
    assert json.loads((tmp_path / "shadow.json").read_text(encoding="utf-8")) == {}
    assert srv["call"]("POST", "/api/routing", {"category": "billing", "agent": "nobody"})[0] == 400
    # 書き出した対応表で run すると billing の draft が v2 になり、影は走らない
    runs2 = tmp_path / "runs2"
    assert (
        main(
            [
                "--runs",
                str(runs2),
                "run",
                "--routing-config",
                str(tmp_path / "routing.json"),
                "--only",
                "INQ-001",
            ]
        )
        == 0
    )
    store2 = RunStore(runs2, RunStore.latest(runs2))
    steps = [s for s in store2.read_steps() if s["inquiry_id"] == "INQ-001"]
    assert next(s for s in steps if s["step"] == "draft")["agent"] == "billing_specialist_v2"
    assert not any(s["step"].startswith("shadow_") for s in steps)


def test_static_without_dist_explains_build(srv):
    st, body, ctype = srv["call"]("GET", "/")
    assert st == 404 and "npm run build" in body["error"]


def test_static_serves_dist_and_blocks_traversal(srv):
    dist = srv["settings"].web_dist
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>t</title>", encoding="utf-8")
    (dist / "assets" / "a.js").write_text("console.log(1)", encoding="utf-8")
    (srv["tmp"] / "secret.txt").write_text("x", encoding="utf-8")
    st, body, ctype = srv["call"]("GET", "/")
    assert st == 200 and ctype.startswith("text/html")
    st, body, ctype = srv["call"]("GET", "/assets/a.js")
    assert st == 200 and "javascript" in ctype
    st, body, _ = srv["call"]("GET", "/no/such/page")
    assert st == 200 and "<title>t</title>" in body  # hash ルーティングのため index にフォールバック
    st, body, _ = srv["call"]("GET", "/../secret.txt")
    assert "x" != body
