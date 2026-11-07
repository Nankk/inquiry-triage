"""LLM 境界の実装。ネットワークは使わず、記録とレスポンス解釈だけを確認する。"""

import json

import pytest

from inquiry_triage.llm import LLMError, RecordingClient, ReplayClient, parse_json_content


class Fake:
    def __init__(self, data=None, error=None):
        self.data, self.error, self.calls = data, error, []

    def complete(self, agent, key, prompt):
        self.calls.append((agent, key))
        if self.error:
            raise LLMError(self.error)
        return self.data


def test_recording_then_replay(tmp_path):
    inner = Fake({"verdict": "pass", "reasons": []})
    rec = RecordingClient(inner, tmp_path)
    assert rec.complete("reviewer", "INQ-001", "p") == {"verdict": "pass", "reasons": []}
    path = tmp_path / "reviewer" / "INQ-001.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {"verdict": "pass", "reasons": []}
    assert ReplayClient(tmp_path).complete("reviewer", "INQ-001", "p") == {"verdict": "pass", "reasons": []}


def test_recording_does_not_save_failures(tmp_path):
    rec = RecordingClient(Fake(error="HTTP 500"), tmp_path)
    with pytest.raises(LLMError):
        rec.complete("router", "INQ-001", "p")
    assert not (tmp_path / "router").exists()


def test_parse_json_content_strips_fence():
    assert parse_json_content('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_content('  {"a": 1}  ') == {"a": 1}
    with pytest.raises(LLMError):
        parse_json_content("はい、分類します: {")
    with pytest.raises(LLMError):
        parse_json_content("[1, 2]")


def test_replay_missing_fixture_is_error(tmp_path):
    with pytest.raises(LLMError):
        ReplayClient(tmp_path).complete("router", "INQ-404", "p")


def test_live_requires_env(monkeypatch):
    from inquiry_triage.llm import LiveClient

    for k in ("INQUIRY_TRIAGE_BASE_URL", "INQUIRY_TRIAGE_API_KEY", "INQUIRY_TRIAGE_MODEL"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(LLMError, match="INQUIRY_TRIAGE_BASE_URL"):
        LiveClient.from_env()


def test_live_client_against_local_server():
    """OpenAI 互換の形で返すローカル HTTP サーバーに対して 1 往復。送った本文と Authorization を確認する。"""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    from inquiry_triage.llm import LiveClient

    seen = {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["auth"] = self.headers.get("Authorization")
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = json.dumps(
                {"choices": [{"message": {"content": '```json\n{"category": "billing"}\n```'}}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):  # テスト出力を汚さない
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        c = LiveClient(f"http://127.0.0.1:{srv.server_port}/v1", "k", "m")
        assert c.complete("router", "INQ-001", "分類して") == {"category": "billing"}
    finally:
        srv.shutdown()
    assert seen["path"] == "/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
    assert seen["body"]["model"] == "m"
    assert seen["body"]["messages"][1] == {"role": "user", "content": "分類して"}
