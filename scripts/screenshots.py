"""README 用のキャプチャ。サーバーをスレッドで立て、Chrome ヘッドレスで画面 3 枚を撮る。

使い方: uv run python scripts/screenshots.py  （事前に web/ をビルドし、runs/ に影つきの run を 1 つ作っておく）
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inquiry_triage.server import Settings, make_server  # noqa: E402

SHOTS = {
    "queue": "#/queue/INQ-001",
    "inquiry": "#/inquiry/INQ-001",
    "shadow": "#/shadow",
}


def main() -> int:
    if not (ROOT / "web" / "dist" / "index.html").exists():
        print("web/dist がありません。cd web && npm ci && npm run build", file=sys.stderr)
        return 2
    os.chdir(ROOT)  # 画面に出るファイル名を相対パスにする
    settings = Settings()
    httpd = make_server(settings, port=0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/api/runs", timeout=1).read()
            break
        except OSError:
            time.sleep(0.1)
    chrome = next(
        (
            c
            for c in ("google-chrome", "chromium", "chromium-browser")
            if subprocess.run(["which", c], capture_output=True).returncode == 0
        ),
        None,
    )
    if not chrome:
        print("Chrome が見つかりません", file=sys.stderr)
        return 2
    for name, frag in SHOTS.items():
        out = ROOT / "docs" / "img" / f"{name}.png"
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                "--window-size=1440,900",
                "--virtual-time-budget=4000",
                f"--screenshot={out}",
                f"{base}/{frag}",
            ],
            check=True,
            capture_output=True,
        )
        print(out)
    httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
