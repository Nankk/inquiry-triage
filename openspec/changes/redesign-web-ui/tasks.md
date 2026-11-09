## 1. 方向の決定

- [ ] 1.1 design.md の D1〜D7 と surface brief（`.impeccable/surfaces/`、方向の契約 6 ブロックと seed）を作者が実装前レビューで承認する。承認後に着手

## 2. 実装

- [ ] 2.1 画面 3 枚を運行図表の世界に組み直す: `styles.css` 全面、`App.tsx` の殻（上部の帯）、`Queue.tsx` / `Inquiry.tsx` / `Shadow.tsx`、スジの SVG 部品と `lib.ts` の純粋関数（vitest）。固定点 D2 を守り、`npm test` と `npm run build`、`uv run pytest -q`、`ruff check` を通す。Impeccable の検出器と finish reviewer を 1 往復し、documenter で `DESIGN.md` と `.impeccable/design.json` を生成する（1 タスク 30 分の規約は作者の指定で意図的に超える）

## 3. キャプチャ

- [ ] 3.1 `uv run python scripts/screenshots.py` で docs/img の 3 枚（queue / inquiry / shadow）を撮り直す。影つきの run が runs/ に 1 つあることを先に確かめる

## 4. 文書

- [ ] 4.1 README と architecture.md の画像を差し替え（パスが同じなら参照は変えない）、design.md から DESIGN.md へのリンクを確かめ、Review 節に仕上げレビューの結果を写す
