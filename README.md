# inquiry-triage

顧客問い合わせをマルチエージェントで仕分け・下書きし、人が承認してから送るプロトタイプ。
見せたいのは動作の完成度ではなく **構成**（[docs/architecture.md](docs/architecture.md)）。

- 分類エージェント → 専門エージェント（請求 / 技術 / アカウント）→ レビューエージェント ∥ 決定論的検証 → 承認キュー → 人
- オーケストレータはコード。LLM は 1 つの仕事を構造化データで返すだけ。自己修正ループは置かない。
- 全段の入出力は追記専用 JSONL。LLM 呼び出しは fixture でリプレイでき、API キー無しで一周する。

## 動かす

```sh
uv sync
uv run inquiry-triage run                      # fixtures/ の架空データで一周
uv run inquiry-triage show                     # 最新実行のキュー
uv run inquiry-triage show --inquiry INQ-004   # 1 件の追跡ログ（レビュー fixture 欠落、存在しない引用、禁止表現が警告になる例）
uv run pytest -q
```

## 構成

```
src/inquiry_triage/
  models.py        データ構造。エージェント出力はここで検証
  llm.py           LLM 境界（ReplayClient。Live / Recording は次の change）
  agents.py        Router / Specialist ×3 / Reviewer。対応表 SPECIALISTS
  retrieval.py     FAQ 記事の決定論的取得
  verify.py        決定論的検証（引用、禁止表現、長さ、プレースホルダ）
  orchestrator.py  分岐・並列・失敗の隔離・記録
  store.py         runs/<run_id>/steps.jsonl, queue.json, decisions.jsonl
  cli.py           run / show / review
fixtures/          架空の問い合わせ 5 件、FAQ 6 本、規程、リプレイ用 LLM 出力
openspec/          仕様（proposal / design / specs / tasks）。実装はここから Claude Code に委任
```

架空データのみ。実在の会社・顧客・業務データは含まない。
