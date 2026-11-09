# approval-queue Specification

## Purpose
TBD - created by archiving change pipeline-skeleton. Update Purpose after archive.
## Requirements
### Requirement: 承認キュー
各問い合わせは 1 つのキュー項目（問い合わせの差出人・件名・本文、分類、返信案、根拠記事 ID、警告一覧、状態）になり、緊急度 high が先頭に並ばなければならない（SHALL）。状態は pending / accepted / rejected / edited。本文は inbox の値をそのまま写し、後から書き換えない。

#### Scenario: 一覧表示
- **WHEN** 実行を `show` する
- **THEN** 緊急度 high の項目が先に表示され、各項目の警告数が見える

#### Scenario: 本文が記録に入る
- **WHEN** 架空の問い合わせ 5 件を `run` する
- **THEN** `queue.json` の各項目の `body` が `inbox.json` の同じ ID の本文と一致し、`show --inquiry INQ-001` で本文が読める

### Requirement: 人の判断
人は CLI で項目ごとに採用・却下・修正でき、判断（項目 ID、操作、修正後本文、理由、時刻）は追記専用の `decisions.jsonl` に記録されなければならない（SHALL）。採用または修正された返信だけが `outbox/` に出力される。

#### Scenario: 修正して採用
- **WHEN** 人が返信案を修正して採用する
- **THEN** decisions.jsonl に edited の記録が追記され、outbox に修正後本文が出力され、元の返信案の記録は変更されない

