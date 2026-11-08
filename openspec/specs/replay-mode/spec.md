# replay-mode Specification

## Purpose
TBD - created by archiving change pipeline-skeleton. Update Purpose after archive.
## Requirements
### Requirement: LLM 境界の単一インターフェース
全てのエージェントは `LLMClient.complete(agent, key, prompt)` 経由でのみ LLM を呼ばなければならない（SHALL）。実装は差し替え可能（Replay / Recording / Live）。

#### Scenario: リプレイでの一周
- **WHEN** `--replay fixtures/replay` で実行する
- **THEN** ネットワークも API キーも無しに全問い合わせがキューに載る

### Requirement: fixture のキー
fixture は `<agent>/<inquiry_id>.json` で参照され、人が読み書きできる JSON でなければならない（SHALL）。該当 fixture が無い場合は、そのエージェント呼び出しを失敗として扱う。

#### Scenario: 欠けた fixture
- **WHEN** `reviewer/INQ-004.json` が無い
- **THEN** INQ-004 のレビューは failed になり、決定論的検証の結果だけがキュー項目に付く

