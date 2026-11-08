# reply-drafting Specification

## Purpose
TBD - created by archiving change pipeline-skeleton. Update Purpose after archive.
## Requirements
### Requirement: 根拠記事の決定論的取得
オーケストレータは分類結果のカテゴリに属する FAQ 記事のうち、問い合わせ本文とキーワードが一致する記事を候補として専門エージェントに渡さなければならない（SHALL）。一致が無い場合は同カテゴリの全記事（上限 5 本）を渡す。渡した記事 ID は記録する。

#### Scenario: キーワード一致
- **WHEN** 問い合わせ本文に「二重」「請求」が含まれ、FAQ 記事 KB-B01 のキーワードに「二重請求」がある
- **THEN** KB-B01 が候補に含まれる

#### Scenario: 一致なし
- **WHEN** カテゴリの記事にキーワード一致が無い
- **THEN** 同カテゴリの記事が上限 5 本まで候補になる

### Requirement: 返信案の生成
専門エージェントは問い合わせと候補記事から、返信本文、引用した記事 ID の一覧、追加で顧客に確認が必要な事項、確信度（high / medium / low）を構造化データで返さなければならない（SHALL）。候補に無い記事 ID は引用できない。

#### Scenario: 根拠付きの返信案
- **WHEN** 候補記事に KB-B01 が渡される
- **THEN** 返信案の引用一覧に KB-B01 が含まれ、本文はその内容に基づく

#### Scenario: 情報不足
- **WHEN** 顧客が注文番号を書いていない
- **THEN** 返信案は注文番号の確認を求める文を含み、確認事項に「注文番号」が列挙される

