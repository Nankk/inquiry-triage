## 1. API（Python、標準ライブラリ）

- [x] 1.1 views.py（新設）: キュー項目に状態を合成する `queue_view(store)`、1 件分（steps / item / decisions）の `inquiry_view(store, iid)`、`shadow_report(store)`。CLI の show / review / shadow-report もこれを使う
- [x] 1.2 review のロジック（検証、decisions 追記、outbox 出力）を cli.py から `approval.py` に移し、CLI と API の両方から呼ぶ
- [x] 1.3 agents.py: `build_specialists(llm, routing=None)` で対応表の上書きを受け、設定の検証を shadow と共通化
- [x] 1.4 server.py: `http.server` で W6 の 6 エンドポイントと静的配信。cli に `serve --port`、`run --routing-config`
- [x] 1.5 tests/test_server.py: スレッドで立てて spec の 6 シナリオを 1 本ずつ

## 2. フロントエンド（web/）

- [x] 2.1 Vite + React + TypeScript の雛形、API の型（`api.ts`）、素の CSS 変数
- [x] 2.2 承認キュー画面（一覧、採用・却下、修正は textarea のモーダル）
- [x] 2.3 追跡画面（段の時系列、本番と影の左右比較）
- [x] 2.4 影の比較画面（表、合計、昇格ボタンと確認）
- [x] 2.5 vitest: 段のグループ化と比較表の整形の純粋関数

## 3. 仕上げ

- [x] 3.1 CI に `npm ci && npm run build && npx vitest run` を足す
- [x] 3.2 Chrome ヘッドレスで画面 3 枚のキャプチャを `docs/img/` に保存し、README と architecture.md に貼る
- [x] 3.3 README を 10 秒 → 1 分 → 10 分の構成に書き直す（pipeline-skeleton 2.5 もここで閉じる）
