## MODIFIED Requirements

### Requirement: 承認キュー
各問い合わせは 1 つのキュー項目（問い合わせの差出人・件名・本文、分類、返信案、根拠記事 ID、警告一覧、状態）になり、緊急度 high が先頭に並ばなければならない（SHALL）。状態は pending / accepted / rejected / edited。本文は inbox の値をそのまま写し、後から書き換えない。

#### Scenario: 一覧表示
- **WHEN** 実行を `show` する
- **THEN** 緊急度 high の項目が先に表示され、各項目の警告数が見える

#### Scenario: 本文が記録に入る
- **WHEN** 架空の問い合わせ 5 件を `run` する
- **THEN** `queue.json` の各項目の `body` が `inbox.json` の同じ ID の本文と一致し、`show --inquiry INQ-001` で本文が読める
