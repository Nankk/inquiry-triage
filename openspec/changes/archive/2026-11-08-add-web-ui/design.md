## Context

CLI（run / show / review / shadow-report）は揃っている。画面は「同じ store を読む別の入口」として足す。業務ロジック、記録の形、不変レコードの原則は変えない。

## Decisions

### W1. API は標準ライブラリの `http.server`、1 プロセスで静的配信も行う
- 依存を増やさない方針（design D8 の延長）。エンドポイントは 6 本程度で、フレームワークを入れる量ではない。
- 代替案: FastAPI。却下理由: 依存が増え、「標準ライブラリのみ」という売りが消える。必要になったら `server.py` の差し替えで済む。

### W2. フロントは Vite + React + TypeScript、UI ライブラリは入れない
- 画面 3 枚、状態は「選択中の run と問い合わせ」程度。CSS は変数（色・余白）を 1 ファイルに置いた素の CSS。
- 代替案: HTMX でサーバー側テンプレート。却下理由: 左右比較や修正フォームのような操作が多い画面は、クライアント側で状態を持つ方が短く書ける。TypeScript の型を API の JSON に合わせて置くことで、API の形が文書になる。

### W3. 状態は毎回 API から読む。画面側にキャッシュを持たない
- 判断を送ったら該当 run を読み直す。ローカルで 1 人が使う前提なので、楽観更新や購読は要らない。

### W4. 昇格は `routing.json` の書き出し
- `{"billing": "billing_specialist_v2"}` の形。`run --routing-config routing.json` で SPECIALISTS の既定（カテゴリ → 本番の担当）を上書きする。影の設定（`shadow.json`）と同じ形・同じ検証（未知の名前は止める）。
- 画面の「昇格」ボタンは、routing.json を書き出し、影の設定から該当カテゴリを外した shadow.json も書き出す（影が本番になったので影は空く）。
- 代替案: agents.py の SPECIALISTS を画面から書き換える。却下理由: コードを実行時に書き換えるのは筋が悪い。設定として外に出す方が、add-shadow-mode S1 の「昇格は対応表の名前を書き換えるだけ」とも一致する。
- 経緯: add-shadow-mode の Open Questions「UI の段階で shadow-report を画面に出し、その場で昇格まで決められる動線にする」を実装する。

### W5. 画面からの判断も decisions.jsonl への追記のみ
- POST /decisions は CLI の review と同じ関数を呼ぶ。outbox への出力も同じ。画面専用の書き込み経路を作らない。

### W6. API の形
| メソッド | パス | 返すもの |
|---|---|---|
| GET | /api/runs | run_id の一覧（新しい順） |
| GET | /api/runs/{id}/queue | queue.json に状態（decisions の最新）と影の要約を合成した一覧 |
| GET | /api/runs/{id}/inquiries/{iid} | その問い合わせの steps 全行と queue 項目、decisions |
| GET | /api/runs/{id}/shadow-report | shadow-report と同じ行の JSON |
| GET | /api/config | 既知のエージェント、既定と現在の対応表（routing.json の上書き込み）、影の設定、書き出し先 |
| POST | /api/runs/{id}/decisions | {inquiry_id, action, reason, body?} → 追記して結果を返す |
| POST | /api/routing | {category, agent} → routing.json と shadow.json を書き出す |

POST は Content-Type: application/json を要求し、Origin があれば Host と一致することを確かめる（ブラウザ経由の CSRF 対策。認証は Non-goal だが、他サイトからの書き込みは止める）。想定外の例外は 500 の JSON で返す。

| GET | /（その他） | web/dist の静的ファイル（無ければ 404 とビルド手順の案内） |

## Risks / Trade-offs

- [web/dist をコミットしない] → `uv run inquiry-triage serve` の前に `npm run build` が要る。README に 2 行で書く。CI でビルドが通ることは確認する。
- [http.server は本番向きでない] → Non-goal（ローカル 1 人）。design に明記。
- [フロントのテストが薄い] → ロジックは API 側（Python、テスト済み）に寄せ、フロントは表示と送信だけにする。純粋関数（段のグループ化、比較表の整形）だけ vitest。

## Review（2026-11-09、実装前）

- 作者が承認。W1（標準ライブラリの http.server）は「大きな売りではないが筋が通っている」として維持、W4（昇格は routing.json の書き出し）も承認。
- 画面の参考に作者が画像生成 AI で作ったモックアップを使った（リポジトリ外に保存）。採るのはレイアウトだけ: ダークテーマ、左に一覧・右に詳細のマスター・ディテール、警告をカードで、影との左右比較をトグルで。文言は日本語で CLI と揃え、モックアップの英語ナビ（Inbox / Analytics / AI Specialists）は採らない。
- 実装上の追加決定: 昇格の書き出し先は fixtures/ ではなくリポジトリ直下の routing.json / shadow.json（`serve --routing-config` / `--shadow-config` で指定、gitignore）。fixtures/shadow.json はテストとデモが依存するので書き換えない。`run --routing-config` は本番と影が同じ名前になる設定を拒否する。静的配信は web/dist 配下に解決したパスだけ返す。画面は hash で切り替え（#/queue、#/inquiry/ID、#/shadow）。

## Open Questions

- 修正（edited）の本文入力は textarea で足りるか。差分表示は v2。
