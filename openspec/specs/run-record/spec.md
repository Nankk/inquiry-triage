# run-record Specification

## Purpose
TBD - created by archiving change pipeline-skeleton. Update Purpose after archive.
## Requirements
### Requirement: 段ごとの不変レコード
オーケストレータは段（route / retrieve / draft / review / verify / enqueue）ごとに、エージェント名、問い合わせ ID、入力の参照、出力、所要時間、状態（ok / failed）を `runs/<run_id>/steps.jsonl` に追記しなければならない（SHALL）。既存行は書き換えない。

#### Scenario: 1 件の追跡
- **WHEN** 問い合わせ INQ-003 の返信案について根拠を問われる
- **THEN** steps.jsonl を INQ-003 で絞ると route → retrieve → draft → review/verify → enqueue の各行と、渡した記事 ID、返した引用 ID が読める

### Requirement: 失敗の隔離
1 件の問い合わせでエージェントが失敗しても、他の問い合わせの処理は続き、失敗はその問い合わせの行に status failed と理由で記録されなければならない（SHALL）。

#### Scenario: 1 件だけ fixture が無い
- **WHEN** 5 件のうち 1 件のリプレイ fixture が欠けている
- **THEN** 4 件はキューに載り、1 件は failed として記録され「人が直接対応」でキューに載る

