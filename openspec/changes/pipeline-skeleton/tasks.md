## 1. 骨組み（11/2 夜）

- [x] 1.1 データ構造（Inquiry, Routing, Draft, Review, Verification, QueueItem, Decision）を dataclass で定義し、dict 変換と検証を付ける
- [x] 1.2 LLM 境界 `LLMClient` と `ReplayClient` を実装する
- [x] 1.3 架空データ: 問い合わせ 5 件、FAQ 記事 6 本、規程 1 本、リプレイ用 fixture を作る
- [x] 1.4 決定論的な FAQ 取得（カテゴリ + キーワード）を実装する
- [x] 1.5 エージェント 3 種（Router、Specialist ×3、Reviewer）を `Agent` プロトコルで実装する
- [x] 1.6 決定論的検証（引用 ID、禁止表現、長さ、プレースホルダ）を実装する
- [x] 1.7 オーケストレータ（問い合わせ並列、レビュー/検証並列、失敗の隔離、JSONL 記録）を実装する
- [x] 1.8 CLI `run` / `show` を実装し、fixture で一周動くことを確認する
- [x] 1.9 構成図と工夫・運用・保守の箇条書き（docs/architecture.md）を書く

## 2. 動くところまで（11/7）

- [x] 2.1 CLI `review`（採用・却下・修正、decisions.jsonl、outbox 出力）を実装する
- [x] 2.2 テスト: 表引き、検証、オーケストレータの失敗隔離、承認の記録を ReplayClient で網羅する
- [x] 2.3 `LiveClient`（OpenAI 互換エンドポイント）と `RecordingClient` を実装する（`run --live` / `--record` / `--only ID`）
- [x] 2.3b 1 件だけ実呼び出しで fixture を作り直す（INQ-001、Gemma 4。INQ-004 のレビュー欠落はデモとテストが依存するので触らない）
- [ ] 2.4 シャドーモード（新しい専門エージェントの出力を記録のみ）を設定で切り替えられるようにする
- [ ] 2.5 README（10 秒 → 1 分 → 10 分）と 5 分で話す台本を書く
