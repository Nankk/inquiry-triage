# inquiry-triage

顧客問い合わせを複数の LLM エージェントで仕分けて返信案を作り、人が承認してから送るプロトタイプ。

LLM を組み込むシステムの基本的な型（一方向の流れ、人の承認ゲート、決定論的な後処理と検証、全段の記録）を、架空の題材で小さく組んだもの。見せたいのは返信の出来ではなく **構成**（[docs/architecture.md](docs/architecture.md)）で、LLM に任せる部分を小さく、周りの決定論的な仕組みを大きくしてある。仕様は [openspec/](openspec/) に置き、実装は Claude Code に委任して監督した。

- 分類エージェント → 専門エージェント（請求 / 技術 / アカウント）→ レビューエージェント ∥ 決定論的検証 → 承認キュー → 人
- オーケストレータはコード。LLM は 1 つの仕事を構造化データで返すだけ。自己修正ループは置かない。
- 全段の入出力は追記専用 JSONL。LLM 呼び出しは fixture でリプレイでき、API キー無しで一周する。

## 動かす

```sh
uv sync
uv run inquiry-triage run                      # fixtures/ の架空データで一周
uv run inquiry-triage show                     # 最新実行のキュー
uv run inquiry-triage show --inquiry INQ-004   # 1 件の追跡ログ（レビュー fixture 欠落、存在しない引用、禁止表現が警告になる例）
uv run inquiry-triage review                   # 未決の項目を返信案つきで一覧
uv run inquiry-triage review --inquiry INQ-001 --accept --reason "記事どおり"   # 採用 → outbox/<run_id>/INQ-001.txt
uv run inquiry-triage review --inquiry INQ-004 --reject --reason "返金の確約"
uv run inquiry-triage review --inquiry INQ-003 --body fixed.txt                # 修正して採用
uv run pytest -q
```

新しい担当エージェントは「影」として試せる。本番と同じ入力で書かせて同じ検査にかけるが、結果は記録だけでキューには出ない。

```sh
uv run inquiry-triage run --shadow-config fixtures/shadow.json   # {"billing": "billing_specialist_v2"}
uv run inquiry-triage shadow-report                              # 本番と影のレビュー判定・警告数を並べる
```

判断は `runs/<run_id>/decisions.jsonl` に追記されるだけで、`queue.json` と `steps.jsonl` は書き換えない。`show` の状態列は decisions.jsonl の最新判断から導く。

実際に LLM を呼ぶときは OpenAI 互換エンドポイントを環境変数で渡す（依存の追加は無い）。

```sh
export INQUIRY_TRIAGE_BASE_URL=https://.../v1 INQUIRY_TRIAGE_API_KEY=... INQUIRY_TRIAGE_MODEL=...
uv run inquiry-triage run --live --only INQ-001            # 1 件だけ実呼び出し
uv run inquiry-triage run --record --only INQ-001          # 実呼び出しの結果を fixtures/replay に保存（次回からリプレイ）
```

## 構成

```
src/inquiry_triage/
  models.py        データ構造。エージェント出力はここで検証
  llm.py           LLM 境界。ReplayClient / LiveClient（OpenAI 互換）/ RecordingClient
  agents.py        Router / Specialist / Reviewer。PERSONAS（名前→人格）と SPECIALISTS（カテゴリ→本番の名前）、影の設定の検証
  retrieval.py     FAQ 記事の決定論的取得
  verify.py        決定論的検証（引用、禁止表現、長さ、プレースホルダ）
  orchestrator.py  分岐・並列・失敗の隔離・記録。影の経路（記録のみ）
  store.py         runs/<run_id>/steps.jsonl, queue.json, decisions.jsonl
  cli.py           run / show / review / shadow-report
fixtures/          架空の問い合わせ 5 件、FAQ 6 本、規程、リプレイ用 LLM 出力、影の設定例
openspec/          仕様（proposal / design / specs / tasks）。実装はここから Claude Code に委任
```

架空データのみ。実在の会社・顧客・業務データは含まない。
