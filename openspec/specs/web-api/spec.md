# web-api Specification

## Purpose
TBD - created by archiving change add-web-ui. Update Purpose after archive.
## Requirements
### Requirement: 実行とキューの取得
API は runs/ 配下の実行一覧と、各実行のキュー項目を返さなければならない（SHALL）。キュー項目には decisions.jsonl から導いた最新の状態と、影の要約（あれば）が含まれる。

#### Scenario: キューの取得
- **WHEN** 影つきで run した後に GET /api/runs/{id}/queue を呼ぶ
- **THEN** CLI の show と同じ順序で項目が返り、各項目に status と shadow が含まれる

### Requirement: 1 件の追跡
API は問い合わせ ID を指定すると、その問い合わせの steps.jsonl の全行（影の段を含む）、キュー項目、判断の履歴を返さなければならない（SHALL）。

#### Scenario: 本番と影の返信案
- **WHEN** GET /api/runs/{id}/inquiries/INQ-001 を呼ぶ
- **THEN** draft と shadow_draft、review と shadow_review、verify と shadow_verify の行が steps に含まれる

### Requirement: 判断の追記
POST /api/runs/{id}/decisions は CLI の review と同じ検証と記録を行わなければならない（SHALL）。queue.json と steps.jsonl は変更されない。

#### Scenario: 画面からの却下
- **WHEN** {inquiry_id: INQ-004, action: rejected, reason: ...} を POST する
- **THEN** decisions.jsonl に 1 行追記され、outbox には何も出ず、直後の GET queue で INQ-004 の status が rejected になる

#### Scenario: 不正な要求
- **WHEN** 存在しない inquiry_id、または返信案の無い項目への accepted を POST する
- **THEN** 4xx が返り、decisions.jsonl は変わらない

### Requirement: 昇格の書き出し
POST /api/routing は {category, agent} を受け取り、既知のエージェント名であれば routing.json に書き出し、shadow.json から同じカテゴリを外さなければならない（SHALL）。未知の名前は 4xx。

#### Scenario: 影を本番にする
- **WHEN** {category: billing, agent: billing_specialist_v2} を POST し、その後 `run --routing-config routing.json` を実行する
- **THEN** billing の問い合わせの draft の agent が billing_specialist_v2 になり、shadow_* の行は記録されない

### Requirement: 静的配信
GET / は web/dist の index.html を返さなければならない（SHALL）。dist が無ければ 404 とビルド手順を返す。

#### Scenario: 未ビルド
- **WHEN** web/dist が無い状態で GET / を呼ぶ
- **THEN** 404 と「npm run build」を含む案内が返る

