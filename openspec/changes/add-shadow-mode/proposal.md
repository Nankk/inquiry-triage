## Why

新しい専門エージェント（プロンプトを変えた請求担当 v2 など）を足すとき、いきなり承認キューに載せると、出来の悪い返信案を人が毎回却下することになり、運用側の信用を失う。
pipeline-skeleton の design D7 で「運用上の導入はシャドーモードで行う」と決めていたが、未実装。

## What Changes

- 設定ファイルで「カテゴリ → 影の専門エージェント名」を指定すると、該当カテゴリの問い合わせで影のエージェントにも同じ入力（問い合わせ + 同じ候補記事）で返信案を書かせる。
- 影の返信案を既存と同じ 2 系統（LLM レビュー ∥ 決定論的検証）で検査し、結果を steps.jsonl に記録する。承認キューの返信案・警告は既存エージェントのもののまま。
- 影の失敗は既存経路に影響しない（記録だけ残る）。
- `show --inquiry` で既存と影の返信案・検査結果が並んで読める。`shadow-report` で問い合わせごとにレビュー判定と警告数を既存と影で比較できる。
- 影を本番に昇格するのは、対応表（agents.py の SPECIALISTS）を書き換える人の作業。コードは昇格を自動化しない。

## Non-goals

- 影の出力を人が承認キューで採用すること（影はキューに出ない。出すなら昇格する）
- 採用率の自動判定や自動昇格
- 複数の影を同時に走らせること（1 カテゴリに影は 1 つ）

## Capabilities

### New Capabilities
- `shadow-mode`: 新しい専門エージェントを記録のみで走らせ、既存経路と比較する

### Modified Capabilities
- `run-record`: 影の段（shadow_draft / shadow_review / shadow_verify）が記録に加わる

## Impact

- `agents.py`: 利用できる専門エージェントの一覧（名前 → 人格）と、カテゴリ → 本番の対応表を分ける
- `orchestrator.py`: retrieve の後に影の draft + review ∥ verify を走らせる分岐。QueueItem に影の有無の印
- `cli.py`: `run --shadow-config FILE`、`shadow-report`
- `fixtures/shadow.json`（設定の例）、`fixtures/replay/billing_specialist_v2/`（影の返信案）、`fixtures/replay/reviewer/<ID>.shadow.json`（影のレビュー）
