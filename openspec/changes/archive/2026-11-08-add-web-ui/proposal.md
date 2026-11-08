## Why

承認キュー、1 件の追跡、影との比較は CLI で一通りできるが、人が毎日使うには手数が多い。件数が増えると `show --inquiry` を 1 件ずつ打つのは運用にならず、影の採用可否も表を眺めて別のコマンドを打つ二度手間になる。
人の側の能率を上げるため、CLI と同じ機能を画面にする。業務ロジックは一切足さない（画面は既存の store と orchestrator を呼ぶだけ）。

## What Changes

- `inquiry-triage serve` で、runs/ を読み書きする小さな HTTP API（標準ライブラリ `http.server`）と、ビルド済みのフロントエンドを 1 つのプロセスで配信する。
- フロントエンド（`web/`、Vite + React + TypeScript）に画面 3 枚: 承認キュー（採用・却下・修正をその場で）、1 件の追跡（段ごとのログと、本番と影の返信案・検査結果の左右比較）、影の比較（shadow-report の表と、影を本番に昇格する操作）。
- 昇格は「カテゴリ → 本番の担当」の対応表を `routing.json` に書き出し、`run --routing-config` がそれを読んで SPECIALISTS の既定を上書きする。コードは触らずに昇格できる。
- 人の判断（採用・却下・修正・昇格）はすべて既存の decisions.jsonl / 設定ファイルへの追記・書き出しで、steps.jsonl と queue.json は画面からも書き換えない。

## Non-goals

- 認証・認可、複数ユーザーの同時編集（ローカルで 1 人が使う前提）
- サーバーの公開運用（デモは README のキャプチャと手元起動）
- `run` を画面から起動すること（LLM 呼び出しは CLI のまま）
- 自動昇格、採用率の自動判定
- E2E テスト（フロントは純粋関数の単体テストのみ）

## Capabilities

### New Capabilities
- `web-api`: runs/ の内容を JSON で返し、人の判断を追記する HTTP API
- `web-ui`: 承認キュー・追跡・影の比較の画面

### Modified Capabilities
- `shadow-mode`: 昇格が `routing.json` の書き出しとして定義される（`run --routing-config`）

## Impact

- 新規: `src/inquiry_triage/server.py`（API と静的配信）、`web/`（フロントエンド）、`tests/test_server.py`
- 変更: `cli.py`（`serve`、`run --routing-config`）、`agents.py`（対応表の上書き）、`store.py`（キュー項目に状態を合成するヘルパ）
- 依存: Python 側は標準ライブラリのまま。フロントは Node（Vite / React / TypeScript）、ビルド成果物 `web/dist` はコミットしない（CI でビルドし、README にはキャプチャを置く）
