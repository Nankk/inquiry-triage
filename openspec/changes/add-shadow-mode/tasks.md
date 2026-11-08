## 1. シャドーモード

- [ ] 1.1 agents.py: 専門エージェント一覧（名前 → 人格）と本番の対応表（カテゴリ → 名前）を分け、影の候補 `billing_specialist_v2`（人格: 確約を避け、確認事項を先に書く）を一覧に足す
- [ ] 1.2 設定の読み込みと検証（JSON、未知の名前は LLMError 以前に ValueError で止める）
- [ ] 1.3 orchestrator: retrieve の後、既存の draft と並列に shadow_draft → shadow_verify を走らせ、QueueItem.shadow に名前・警告数・失敗理由を載せる
- [ ] 1.4 cli: `run --shadow-config FILE`、`shadow-report [run_id]`、show --inquiry は変更なしで影の行が出ることを確認
- [ ] 1.5 fixture: `fixtures/shadow.json`、`fixtures/replay/billing_specialist_v2/INQ-001.json`（INQ-004 は意図的に欠落させ、失敗の隔離のデモにする）
- [ ] 1.6 テスト: spec の 7 シナリオを 1 本ずつ
- [ ] 1.7 docs/architecture.md の運用 4「（予定）」を外し、構成図に影の経路を点線で足す。README に 3 行
