## 1. 記録

- [ ] 1.1 models.py: `QueueItem` に `body: str` を足す（`to_dict` は asdict なので変更なし）
- [ ] 1.2 orchestrator.py: enqueue で `inq.body` を写す
- [ ] 1.3 tests/test_pipeline.py: run 後の queue.json の各項目の `body` が inbox と一致する

## 2. 表示

- [ ] 2.1 cli.py: `_print_item` と `show --inquiry` に本文（欠落なら「本文なし（記録に含まれていません）」）
- [ ] 2.2 web: `api.ts` の `QueueItem` に `body: string | null`（欠落を許す）、`Queue.tsx` の詳細と `Inquiry.tsx` に「問い合わせ」区画
- [ ] 2.3 `npm test`、`npm run build`、`uv run pytest -q`、`ruff check` を通す

## 3. 文書

- [ ] 3.1 README の「記録」に queue.json の項目として本文が入ることを 1 語、architecture.md の表の「承認」行の入力に「問い合わせ本文」を足す
