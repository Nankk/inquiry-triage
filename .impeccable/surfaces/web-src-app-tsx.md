---
version: 1
slug: "web-src-app-tsx"
primary_target: "web/src/App.tsx"
related_targets: ["web/src/views/Queue.tsx","web/src/views/Inquiry.tsx","web/src/views/Shadow.tsx","web/src/styles.css"]
---

# Surface brief: 画面 3 枚（承認キュー、1 件の追跡、影の比較）

## Scope and mode
- Operate。担当者が問い合わせを読み、返信案を採用・却下・修正する。追跡と影の比較は同じ殻の中。
- 対象: web/src/App.tsx（殻）、web/src/views/Queue.tsx、Inquiry.tsx、Shadow.tsx、web/src/styles.css。
- 変更: openspec/changes/redesign-web-ui（design.md の D1〜D7 が決定、D2 が作者の固定点）。

## Audience, job, constraints
- 主: 架空の一次対応担当者。日中の明るい事務所のモニタで、1 日に何十件も読む。副: README とキャプチャで構成を読む技術者。
- 仕事: 一覧で「どの段まで進み、どこで警告が立ったか」を読み、詳細で 本文 → 返信案（本番｜影）→ 警告 → 操作 の順に判断する。
- 制約: 依存を足さない（react / react-dom のみ、Web フォント無し）、業務ロジックを持ち込まない、hash の URL を維持、docs/img を scripts/screenshots.py（1440×900）で撮り直せること。
- 外したくない点（作者）: 装飾で本文・返信案・警告が読みにくくなる、操作の手数が増える、業務ツールに見えない、キャプチャで今と区別がつかない。

## Direction contract

THESIS: 問い合わせ 1 件を 1 本の列車として、分類から承認までの各段を等間隔の駅を結ぶ一本の線（スジ）で読む。拒むのは、近黒の地に色札と角丸カードを並べる管理画面と、その裏返しの白地・灰の枠線・青ボタンの管理画面。

OWN-WORLD: 紙白（#f7f6f2 付近）の地。殻（上部の帯と一覧の背景）だけに 24px の薄い青灰（#dfe5ec 付近）の方眼。墨（#1c2430 付近）が 2px の罫、文字、主ボタンの塗り。色は緊急度の 3 色だけ: 高 = 赤 #d6362c 3px、中 = 橙 #e08a1e 2px、低 = 墨 1.2px。状態は線の形: 本番 = 実線、影 = 破線（担当から）、失敗・人が直接対応 = 線が止まって終端記号。札に枠線なし、塗りか文字色のみ。角丸 2〜3px。字は "BIZ UDPGothic", "Hiragino Sans", "Noto Sans JP", "Yu Gothic UI", system-ui の 1 族、数字は tabular-nums。補助文字の灰は紙白の上で 4.5:1 以上。

STORY: 担当者は一覧のスジで進行と警告の位置を読み、詳細で本文を読んでから返信案を比べ、警告を見て、右端の「採用して送信箱へ」か却下・修正を押す。読み手はキャプチャ 1 枚で「段のある一方向の流れ」「本番と影の並走」「人の承認」を読む。

FIRST VIEWPORT: 1440×900 の承認キュー（#/queue/INQ-001）。上 56px の帯: 左に名前と副題、タブ 承認キュー／影の比較、右に run 選択。下は左 500px の一覧と右の詳細。一覧の各項目: ID、件名、状態札（枠線なし）、緊急度・担当・警告数・影、下にスジ（4 点等間隔、影は担当から破線）。選択中は持ち上がり（影）、他は一段沈む（不透明度）。詳細: 見出し（ID、件名、状態、「各段のログを見る」）、メタ（差出人、緊急度、カテゴリ、引用、確信度）、段の図（4 駅等間隔、駅名、点の下に ms、本番実線・影破線）、本文、返信案（本番｜影、各々の脇に長さ上限の目盛）、警告（左に 3px の赤罫）、操作列（理由、修正、却下、墨の塗りの「採用して送信箱へ」が右端）。方眼は詳細の面には無い。

FORM: 鉄道の運行図表（ダイヤグラム）と列車種別の色。候補 7 のうち 4 位、ロールの割当を作者が決定ページで確定。スケッチ .impeccable/mocks/decision/assigned.html。seed:edefc5bda0ac66a2

SIGNATURE INTERACTION / MOTION: 一覧で項目を選ぶと、詳細の段の図の線が左から 180ms で引かれる（stroke-dashoffset、ease-out）。判断（採用・却下・修正）の後はキューの点に終端記号が付き、一覧の状態札が同時に変わる。動きは状態の変化だけ（150〜250ms）。読み込みの演出は無し。

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved
- 追跡画面で retrieve（FAQ 表引き）を独立した駅にするか、担当の駅の注記に含めるか（起草案: 注記）。
