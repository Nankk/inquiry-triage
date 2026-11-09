## Why

承認キューの項目には差出人・件名・分類・返信案・警告はあるが、顧客が書いた問い合わせ本文が無い。人が返信案を採用・却下・修正するとき、本文と返信案を見比べられないと判断の根拠が返信案の読みやすさだけになる。CLI の `show --inquiry` も画面も、本文を見るには `fixtures/inbox.json` を別に開くしかない。

## What Changes

- キュー項目（`QueueItem`、`queue.json`）に問い合わせ本文 `body` を持たせる。enqueue 時に inbox の値をそのまま写す。
- 画面の承認キュー詳細と 1 件の追跡で、返信案の上に本文を表示する。CLI の `show --inquiry` と `review` の一覧表示にも本文を出す。
- `body` の無い古い `queue.json`（この change より前の run）は「本文なし（記録に含まれていません）」と表示し、エラーにしない。

## Non-goals

- 分類エージェントが返す `summary` を画面に出すこと（本文があれば要約は要らない。必要なら各段のログで読める）
- 実行時に `inbox.json` をサーバーから読み直すこと（run の記録は `runs/<run_id>/` だけで完結させる。run-record の原則）
- 本文の編集や、本文を基にした自動チェック

## Capabilities

### Modified Capabilities
- `approval-queue`: キュー項目に問い合わせ本文を含める
- `web-ui`: 承認キュー詳細と追跡画面で本文を表示する

## Impact

- 変更: `models.py`（QueueItem に body）、`orchestrator.py`（enqueue で写す）、`cli.py`（`_print_item` に本文）、`web/src/api.ts`（型）、`web/src/views/Queue.tsx` と `Inquiry.tsx`（表示）
- テスト: `tests/test_pipeline.py` に「queue.json の各項目に inbox の本文がそのまま入る」を 1 本。画面側は表示だけなので vitest は増やさない
- 記録の互換: `queue.json` に列が 1 つ増えるだけ。読む側は `body` 欠落を許す
- キャプチャ（docs/img/）は画面の見直しと一緒に撮り直す（この change では撮らない）
