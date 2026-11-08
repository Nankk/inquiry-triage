"""HTTP API と静的配信。標準ライブラリの http.server のみ。ローカルで 1 人が使う前提（認証なし）。

GET  /api/runs                         run_id の一覧（新しい順）
GET  /api/runs/{id}/queue              キュー（状態を合成）
GET  /api/runs/{id}/inquiries/{iid}    1 件の全段・項目・判断
GET  /api/runs/{id}/shadow-report      本番と影の比較
GET  /api/config                       現在の対応表（既定 + routing.json）と影の設定、既知のエージェント

書き込み（POST）は Content-Type: application/json と、Origin があれば Host と同じことを要求する。
POST /api/runs/{id}/decisions          {inquiry_id, action, reason, body?}
POST /api/routing                      {category, agent} → routing.json に書き出し、shadow.json から外す
GET  /...                              web/dist の静的ファイル
"""

from __future__ import annotations

import json
import mimetypes
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from inquiry_triage.agents import PERSONAS, SPECIALISTS, validate_table
from inquiry_triage.approval import ApprovalError, decide
from inquiry_triage.models import CATEGORIES
from inquiry_triage.store import RunStore
from inquiry_triage.views import inquiry_view, queue_view, shadow_report

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    runs: Path = Path("runs")
    outbox: Path = Path("outbox")
    routing_config: Path = Path("routing.json")
    shadow_config: Path = Path("shadow.json")
    web_dist: Path = ROOT / "web" / "dist"


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _read_table(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return validate_table(json.loads(path.read_text(encoding="utf-8")), str(path))


class Api:
    """ルーティングと処理。HTTP の層から切り離してテストしやすくする。"""

    ROUTES = (
        ("GET", re.compile(r"^/api/runs$"), "runs"),
        ("GET", re.compile(r"^/api/runs/([^/]+)/queue$"), "queue"),
        ("GET", re.compile(r"^/api/runs/([^/]+)/inquiries/([^/]+)$"), "inquiry"),
        ("GET", re.compile(r"^/api/runs/([^/]+)/shadow-report$"), "shadow"),
        ("GET", re.compile(r"^/api/config$"), "config"),
        ("POST", re.compile(r"^/api/runs/([^/]+)/decisions$"), "decide"),
        ("POST", re.compile(r"^/api/routing$"), "promote"),
    )

    def __init__(self, settings: Settings) -> None:
        self.s = settings

    def dispatch(self, method: str, path: str, body: dict[str, Any] | None) -> Any:
        for m, pat, name in self.ROUTES:
            mt = pat.match(path)
            if mt and m == method:
                return getattr(self, name)(*mt.groups(), body=body)
        raise ApiError(404, f"not found: {method} {path}")

    def _store(self, run_id: str) -> RunStore:
        store = RunStore.open(self.s.runs, None if run_id == "latest" else run_id)
        if store is None:
            raise ApiError(404, f"run not found: {run_id!r}")
        return store

    # --- GET -------------------------------------------------------------
    def runs(self, body=None) -> Any:
        if not self.s.runs.exists():
            return []
        ids = sorted((p.name for p in self.s.runs.iterdir() if (p / "queue.json").exists()), reverse=True)
        return [{"run_id": r, "items": len(RunStore(self.s.runs, r).read_queue())} for r in ids]

    def queue(self, run_id: str, body=None) -> Any:
        store = self._store(run_id)
        return {"run_id": store.run_id, "items": queue_view(store)}

    def inquiry(self, run_id: str, inquiry_id: str, body=None) -> Any:
        view = inquiry_view(self._store(run_id), inquiry_id)
        if view is None:
            raise ApiError(404, f"inquiry not found: {inquiry_id}")
        return view

    def shadow(self, run_id: str, body=None) -> Any:
        return shadow_report(self._store(run_id))

    def config(self, body=None) -> Any:
        override = _read_table(self.s.routing_config)
        return {
            "categories": list(CATEGORIES),
            "agents": PERSONAS,
            "defaults": SPECIALISTS,
            "routing": {**SPECIALISTS, **override},
            "routing_override": override,
            "shadow": _read_table(self.s.shadow_config),
            "files": {"routing": str(self.s.routing_config), "shadow": str(self.s.shadow_config)},
        }

    # --- POST ------------------------------------------------------------
    def decide(self, run_id: str, body: dict[str, Any] | None = None) -> Any:
        body = body or {}
        try:
            return decide(
                self._store(run_id),
                str(body.get("inquiry_id", "")),
                str(body.get("action", "")),
                str(body.get("reason", "")),
                body.get("body"),
                self.s.outbox,
            )
        except ApprovalError as e:
            raise ApiError(400, str(e)) from e

    def promote(self, body: dict[str, Any] | None = None) -> Any:
        """影を本番にする。routing.json に書き出し、shadow.json から同じカテゴリを外す。次回の run から有効。"""
        body = body or {}
        cat, agent = body.get("category"), body.get("agent")
        try:
            validate_table({cat: agent}, "昇格")
        except ValueError as e:
            raise ApiError(400, str(e)) from e
        routing = _read_table(self.s.routing_config)
        routing[cat] = agent
        shadow = _read_table(self.s.shadow_config)
        shadow.pop(cat, None)
        self.s.routing_config.write_text(
            json.dumps(routing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.s.shadow_config.write_text(
            json.dumps(shadow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return {"routing": {**SPECIALISTS, **routing}, "routing_override": routing, "shadow": shadow}


def make_handler(api: Api, web_dist: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "inquiry-triage/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:  # 静かに
            pass

        def _json(self, status: int, data: Any) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _api(self, method: str) -> None:
            try:
                body = self._read_body() if method == "POST" else None
                self._json(200, api.dispatch(method, self.path.split("?", 1)[0], body))
            except ApiError as e:
                self._json(e.status, {"error": str(e)})
            except Exception as e:  # noqa: BLE001 — 壊れた記録などで落ちても応答は返す
                self._json(500, {"error": f"{type(e).__name__}: {e}"})

        def _read_body(self) -> dict[str, Any]:
            """書き込み API の入口。JSON 以外、他サイト起点、壊れた長さは受け付けない。"""
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if ctype != "application/json":
                raise ApiError(415, "Content-Type must be application/json")
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != (self.headers.get("Host") or ""):
                raise ApiError(403, "cross-origin request is not allowed")  # ブラウザ経由の CSRF を止める
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError as e:
                raise ApiError(400, "bad Content-Length") from e
            if n > 1_000_000:
                raise ApiError(413, "body too large")
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ApiError(400, "body is not JSON") from e
            if not isinstance(body, dict):
                raise ApiError(400, "body must be an object")
            return body

        def _static(self) -> None:
            rel = self.path.split("?", 1)[0].lstrip("/") or "index.html"
            root = web_dist.resolve()
            target = (root / rel).resolve()
            if root not in target.parents and target != root:
                self._json(404, {"error": "not found"})
                return
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                if not (root / "index.html").is_file():
                    msg = "web/dist がありません。cd web && npm ci && npm run build でフロントエンドをビルドしてください"
                    self._json(404, {"error": msg})
                    return
                target = root / "index.html"  # hash ルーティングなので index にフォールバック
            raw = target.read_bytes()
            ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path.startswith("/api/"):
                self._api("GET")
            else:
                self._static()

        def do_POST(self) -> None:
            if self.path.startswith("/api/"):
                self._api("POST")
            else:
                self._json(405, {"error": "method not allowed"})

    return Handler


def make_server(settings: Settings, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(Api(settings), settings.web_dist))


def serve(settings: Settings, host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = make_server(settings, host, port)
    print(f"inquiry-triage serve: http://{host}:{httpd.server_port}/  runs={settings.runs}")
    if not (settings.web_dist / "index.html").exists():
        print(
            "注意: web/dist が無いので API だけ動きます。cd web && npm ci && npm run build で画面をビルドできます"
        )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
