## ADDED Requirements

### Requirement: 問い合わせの分類
分類エージェントは問い合わせ 1 件から、カテゴリ（billing / technical / account / other）、緊急度（low / normal / high）、要約、抽出した事実（注文番号等）を構造化データで返さなければならない（SHALL）。オーケストレータはカテゴリから専門エージェントを対応表で 1 つ選ぶ。

#### Scenario: 請求の問い合わせ
- **WHEN** 問い合わせ本文が二重請求の指摘である
- **THEN** カテゴリ billing が返り、BillingSpecialist が選ばれる

#### Scenario: 対応表に無いカテゴリ
- **WHEN** カテゴリが other である
- **THEN** 専門エージェントは呼ばれず、問い合わせは「人が直接対応」として承認キューに載る

#### Scenario: 構造化出力の検証失敗
- **WHEN** 分類エージェントの出力に未知のカテゴリ値が含まれる
- **THEN** その問い合わせは失敗として記録され「人が直接対応」としてキューに載り、他の問い合わせの処理は続く
