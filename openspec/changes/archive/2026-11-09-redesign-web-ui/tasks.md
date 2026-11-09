## 1. 方向の決定

- [x] 1.1 design.md の D1〜D7 と surface brief（`.impeccable/surfaces/`、方向の契約 6 ブロックと seed）を作者が実装前レビューで承認する。承認後に着手

## 2. 実装

- [x] 2.1 殻: `App.tsx` をサイドバーから上部の帯（名前、承認キュー／影の比較のタブ、run 選択）に、`styles.css` を運行図表の世界（紙白、殻だけの方眼、墨、緊急度 3 色、枠線なしの札、1 族のフォント）へ全面に書き直す。既存の画面 3 枚がそのまま表示できる状態で 1 コミット
- [x] 2.2 スジ: 段の並びと状態（本番・影、失敗、人が直接対応）を導く純粋関数を `lib.ts` に足して vitest で確かめ（INQ-001 / INQ-004 / INQ-005 の形）、SVG を返す部品を `components/` に 1 つ置く。1 コミット
- [x] 2.3 画面 3 枚: `Queue.tsx`（一覧の各項目と詳細にスジ、本文 → 返信案 → 警告 → 操作、長さの目盛、選択の持ち上げ）、`Inquiry.tsx`（4 駅の図と ms、その下に steps.jsonl の行ごとのログはそのまま）、`Shadow.tsx`（表は表のまま、色と字と余白を揃える）。`npm test`、`npm run build`、`uv run pytest -q`、`ruff check` を通して 1 コミット
- [x] 2.4 仕上げ: Impeccable の検出器を変更ファイルに 1 回かけて機械的な指摘を直し、finish reviewer を 1 往復、documenter で `DESIGN.md` と `.impeccable/design.json` を生成する。1 コミット

## 3. キャプチャ

- [x] 3.1 `uv run python scripts/screenshots.py` で docs/img の 3 枚（queue / inquiry / shadow）を撮り直す。影つきの run が runs/ に 1 つあることを先に確かめる

## 4. 文書

- [x] 4.1 README と architecture.md の画像を差し替え（パスが同じなら参照は変えない）、design.md から DESIGN.md へのリンクを確かめ、Review 節に仕上げレビューの結果を写す
