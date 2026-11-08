## ADDED Requirements

### Requirement: 影の経路
設定ファイルでカテゴリに影の専門エージェントが指定されているとき、オーケストレータはそのカテゴリの問い合わせについて、既存の専門エージェントと同じ入力（問い合わせと同じ候補記事）で影のエージェントにも返信案を書かせ、既存と同じ 2 系統の検査（LLM レビューと決定論的検証）にかけなければならない（SHALL）。影の結果は記録のみで、承認キューの返信案と警告は既存エージェントのもののままでなければならない（SHALL）。

#### Scenario: 影が走る
- **WHEN** `{"billing": "billing_specialist_v2"}` を指定して実行し、INQ-001 が billing に分類される
- **THEN** steps.jsonl に INQ-001 の shadow_draft（agent=billing_specialist_v2）、shadow_review、shadow_verify の行が追記され、draft の行の input.articles と shadow_draft の input.articles が同じであり、queue.json の INQ-001 の draft と warnings は影を指定しない実行と同じである

#### Scenario: 対象外のカテゴリ
- **WHEN** 影が billing にだけ指定されていて、INQ-002 が technical に分類される
- **THEN** INQ-002 には shadow_* の行が記録されない

#### Scenario: 設定なし
- **WHEN** 設定ファイルを指定せずに実行する
- **THEN** steps.jsonl に shadow_* の行は無く、出力は従来と同じである

### Requirement: 影の失敗の隔離
影のエージェントの失敗（fixture 欠落、出力の構造不正）は、既存経路の結果に影響してはならない（SHALL NOT）。失敗は shadow_draft の行に status=failed と理由で記録される。

#### Scenario: 影の fixture が無い
- **WHEN** 影のエージェントのリプレイ fixture が欠けている
- **THEN** shadow_draft が failed で記録され、shadow_review と shadow_verify は記録されず、同じ問い合わせの queue.json の項目は影を指定しない実行と同じである

#### Scenario: 影のレビューだけ失敗
- **WHEN** 影の返信案はあるが影のレビュー fixture（`reviewer/<ID>.shadow.json`）が欠けている
- **THEN** shadow_review が failed、shadow_verify は ok で記録され、既存経路の結果は変わらない

### Requirement: 設定の検証
影の設定に、既知の専門エージェント一覧に無い名前があれば、実行は始まる前に失敗しなければならない（SHALL）。

#### Scenario: 未知の名前
- **WHEN** `{"billing": "nobody"}` を指定する
- **THEN** run は終了コード 2 で止まり、runs/ に新しい実行は作られない

### Requirement: 既存と影の比較
人は実行 1 回分について、問い合わせごとに既存と影のレビュー判定と警告数を並べて見られなければならない（SHALL）。

#### Scenario: 比較表
- **WHEN** 影つきで実行した後に `shadow-report` を実行する
- **THEN** 影が走った問い合わせごとに、本番のエージェント名・レビュー判定・警告数と、影のエージェント名・レビュー判定・警告数（失敗なら理由）が 1 行ずつ出て、末尾に pass 件数と警告合計が出る

#### Scenario: 1 件の追跡
- **WHEN** `show --inquiry INQ-001` を実行する
- **THEN** draft と shadow_draft、review と shadow_review の行が出て、2 つの返信案本文と 2 つのレビュー判定が読める
