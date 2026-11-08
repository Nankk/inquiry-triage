# web-ui Specification

## Purpose
TBD - created by archiving change add-web-ui. Update Purpose after archive.
## Requirements
### Requirement: 承認キュー画面
画面は最新の実行（または選んだ実行）のキューを、CLI と同じ順序（緊急度 high が先）で一覧し、各項目で採用・却下・修正ができなければならない（SHALL）。判断後は一覧の状態が更新される。

#### Scenario: その場で却下
- **WHEN** INQ-004 の「却下」を押して理由を入れる
- **THEN** 一覧の INQ-004 が rejected になり、他の項目は変わらない

### Requirement: 追跡画面
画面は問い合わせ 1 件の段（route → retrieve → draft → review / verify → enqueue、影があれば shadow_*）を時系列に示し、本番と影の返信案・レビュー判定・警告を左右に並べて見せなければならない（SHALL）。

#### Scenario: 左右比較
- **WHEN** 影つきで run した INQ-001 を開く
- **THEN** 左に本番（billing_specialist）の返信案と flag の理由、右に影（billing_specialist_v2）の返信案と pass が並ぶ

### Requirement: 影の比較画面
画面は shadow-report の表（本番と影のレビュー判定・警告数、失敗理由）と合計を示し、カテゴリごとに「昇格」の操作を持たなければならない（SHALL）。昇格は確認ダイアログを挟む。

#### Scenario: 昇格の動線
- **WHEN** billing の行で「昇格」を押して確認する
- **THEN** routing.json に billing → billing_specialist_v2 が書き出され、画面に「次回の run から有効」と表示される

