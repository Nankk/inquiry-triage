---
name: inquiry-triage
description: 問い合わせ 1 件を 1 本の列車として読む、運行図表の世界の承認画面
colors:
  paper: "#f7f6f2"
  card: "#ffffff"
  card-sunk: "#fbfbf9"
  grid: "#dfe5ec"
  rule: "#d6dce3"
  ink: "#1c2430"
  ink-2: "#45505f"
  ink-3: "#637080"
  tint: "#eceff3"
  tint-2: "#e2e7ec"
  high-line: "#d6362c"
  high-text: "#b3261e"
  high-tint: "#f6dbd8"
  normal-line: "#c2661a"
  normal-text: "#9a5210"
  normal-tint: "#f6e3c8"
  low-line: "#1c2430"
  low-text: "#1c2430"
  low-tint: "#e9edf1"
  ok-text: "#1f6b3f"
  ok-tint: "#dcebe1"
typography:
  headline:
    fontFamily: "BIZ UDPGothic, Hiragino Sans, Noto Sans JP, Yu Gothic UI, system-ui, -apple-system, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    letterSpacing: "0.01em"
  title:
    fontFamily: "BIZ UDPGothic, Hiragino Sans, Noto Sans JP, Yu Gothic UI, system-ui, -apple-system, sans-serif"
    fontSize: "15px"
    fontWeight: 700
  body:
    fontFamily: "BIZ UDPGothic, Hiragino Sans, Noto Sans JP, Yu Gothic UI, system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tabular-nums"
  body-draft:
    fontFamily: "BIZ UDPGothic, Hiragino Sans, Noto Sans JP, Yu Gothic UI, system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.75
  label:
    fontFamily: "BIZ UDPGothic, Hiragino Sans, Noto Sans JP, Yu Gothic UI, system-ui, -apple-system, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    letterSpacing: "0.06em"
  identifier:
    fontFamily: "BIZ UDPGothic, Hiragino Sans, Noto Sans JP, Yu Gothic UI, system-ui, -apple-system, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    letterSpacing: "0.04em"
  caption:
    fontFamily: "BIZ UDPGothic, Hiragino Sans, Noto Sans JP, Yu Gothic UI, system-ui, -apple-system, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
rounded:
  control: "2px"
  surface: "3px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "24px"
  gutter: "28px"
  grid: "24px"
components:
  button:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "7px 14px"
  button-hover:
    backgroundColor: "{colors.tint}"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "7px 14px"
  button-danger:
    backgroundColor: "{colors.card}"
    textColor: "{colors.high-text}"
    rounded: "{rounded.control}"
    padding: "7px 14px"
  button-danger-hover:
    backgroundColor: "{colors.high-tint}"
  input:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "6px 9px"
  badge:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.control}"
    padding: "1px 8px"
  badge-high:
    backgroundColor: "{colors.high-tint}"
    textColor: "{colors.high-text}"
  badge-normal:
    backgroundColor: "{colors.normal-tint}"
    textColor: "{colors.normal-text}"
  badge-low:
    backgroundColor: "{colors.low-tint}"
    textColor: "{colors.low-text}"
  badge-ok:
    backgroundColor: "{colors.ok-tint}"
    textColor: "{colors.ok-text}"
  card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.surface}"
    padding: "12px 16px"
  card-click:
    backgroundColor: "{colors.card-sunk}"
    rounded: "{rounded.surface}"
    padding: "12px 16px"
  card-sel:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.surface}"
    padding: "12px 16px"
  detail:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.surface}"
    padding: "18px 22px 20px"
  warn:
    backgroundColor: "{colors.normal-tint}"
    textColor: "{colors.normal-text}"
    rounded: "{rounded.control}"
    padding: "7px 10px"
  warn-llm:
    backgroundColor: "{colors.high-tint}"
    textColor: "{colors.high-text}"
  warn-ok:
    backgroundColor: "{colors.ok-tint}"
    textColor: "{colors.ok-text}"
  topbar:
    textColor: "{colors.ink}"
    height: "56px"
    padding: "0 28px"
---

# Design System: inquiry-triage

## Overview

**Creative North Star: "運行図表"**

問い合わせ 1 件は 1 本の列車である。分類・担当・検査・キューの 4 段は等間隔の駅で、本番の線は実線、影（シャドーモード）の線は担当の駅から並走する破線。緊急度は列車種別の線の太さと色（高 = 赤 3px、中 = 橙 2px、低 = 墨 1.2px）で、失敗・車止め・人の判断は線路記号（三角、二本の縦棒、塗りの四角）で持つ。新しい色は増やさない。

地は紙白で、殻（上部の帯と一覧の背景）にだけ 24px の薄い青灰の方眼が敷かれ、本文・返信案・警告の読む面は無地の白。墨 1 色が罫、文字、主ボタンの塗りを兼ねる。字は OS のゴシック 1 族で Web フォントを読み込まず、数字は tabular-nums。日中の明るい事務所で何十件も読む担当者のための業務ツールで、短い事実文で「何を書き換え、何を書き換えないか」を画面が言う（判断は decisions.jsonl に追記されるだけ、昇格は次回の run から有効）。

拒むのは、近黒の地に色札と角丸カードを並べる管理画面と、その裏返しの白地・灰の枠線・青ボタンの管理画面。札に枠線はなく、塗りか文字色だけ。影は選択中の一覧項目 1 つにしか落ちない。

**Key Characteristics:**
- 紙白の地と墨 1 色。色は緊急度の 3 段と合格の緑だけ
- 方眼は殻だけ。読む面（本文・返信案・警告）は無地の白
- 状態は色ではなく線の形（実線・破線・車止め・記号）で持つ
- 1 族のゴシック、tabular-nums、12px 太字 0.06em の節見出し
- 角丸 2〜3px、2px の墨の罫、1px の薄い罫線、枠線なしの札
- 動きは状態の変化だけ（120〜200ms）。唯一の演出は選択時の 180ms の線引き

## Colors

紙白と墨の 2 色に、緊急度の 3 段がそれぞれ「線・文字・塗り」の 3 値で載る抑制された配色。

### Primary
- **墨** (`ink` #1c2430): 本文、見出し、帯の下の 2px の罫、表頭の罫、主ボタンの塗り、フォーカス輪、選択範囲の地、スジの駅（点）。低緊急度の線もこの色（`low-line` / `low-text` は同値の別トークン）。
- **墨の濃淡** (`ink-2` #45505f、`ink-3` #637080): 補助文字。`ink-2` はメタ情報・札の既定文字・ナビの非選択、`ink-3` は ID・担当名・脚注・プレースホルダ。`ink-3` は紙白の上で 4.67:1、沈んだ札の上で 4.87:1（実測）。

### Secondary（緊急度 3 段）
- **高・赤** (`high-line` #d6362c / `high-text` #b3261e / `high-tint` #f6dbd8): 高緊急度の 3px の線、却下・fail の札、LLM 警告の塗り、危険ボタンの枠と文字。`line` は太さのある線と記号、`text` は塗りの上の小さな文字（4.99:1）、`tint` は札と警告の地。
- **中・橙** (`normal-line` #c2661a / `normal-text` #9a5210 / `normal-tint` #f6e3c8): 中緊急度の 2px の線、flag の札、決定論的検証の警告の塗り（4.67:1）。方向の契約の橙より暗い値で出荷された（小さな文字の対比のため）。
- **低・墨** (`low-line` / `low-text` #1c2430 / `low-tint` #e9edf1): 低緊急度は色を持たず墨 1.2px の線。札の地だけ薄い青灰。

### Tertiary
- **合格の緑** (`ok-text` #1f6b3f / `ok-tint` #dcebe1): pass、採用、修正の札と「警告なし」の行（5.26:1）。作者が受け入れた唯一の緊急度外の色。線には使わない。

### Neutral
- **紙白** (`paper` #f7f6f2): 画面の地。詳細の中の問い合わせ本文と段の図の面にも敷き、白い札の中で一段引いて見せる。
- **白** (`card` #ffffff): 読む面。一覧の選択中の札、詳細、各段のログの行、入力欄。
- **沈んだ白** (`card-sunk` #fbfbf9): 一覧の非選択の札と影の段のログの行。不透明度ではなく明度で沈める。
- **方眼** (`grid` #dfe5ec): 24px 間隔の 1px の線。殻にだけ出る。
- **罫線** (`rule` #d6dce3): 表の 1px の横罫、操作列の上の罫、リンクの下線、スジの線路床（1 4 の点線）、影の段の破線の輪郭。
- **薄墨** (`tint` #eceff3 / `tint-2` #e2e7ec): 既定の札（未決）と通常ボタンのホバーの地。

### Named Rules
**The Three Trains Rule.** 色は緊急度の 3 段（高・中・低）だけで、一覧・詳細・追跡の全画面で同じ太さと色。合格の緑を除き、新しい状態に新しい色を与えない。状態は線の形で持つ。

**The Shell Grid Rule.** 方眼は殻（帯と一覧の背景）にだけ敷く。本文・返信案・警告・表の面は無地の白か紙白。

**The No-Border Chip Rule.** 札に枠線を付けない。塗り（`*-tint`）と文字色（`*-text`）だけで種類を分ける。

## Typography

**Display Font:** なし（見出しも本文と同じ族）
**Body Font:** BIZ UDPGothic（Hiragino Sans、Noto Sans JP、Yu Gothic UI、system-ui の順に代替）
**Label/Mono Font:** 同じ族。等幅は使わず、識別子（ID・担当名・カテゴリ）は同じゴシックに 0.01〜0.04em の字間で置く

**Character:** OS のゴシック 1 族で Web フォントを読み込まない。業務伝票の字で、太さ（400 / 700）と大きさ（11〜20px）だけで階層を作る。数字は全て tabular-nums で桁が揃う。

### Hierarchy
- **Headline** (700, 20px, 字間 0.01em): 画面の h1（承認キュー、1 件の追跡、影の比較）と詳細の h2（ID と件名）。帯の名前は 700 の 17px。
- **Title** (700, 15px): 一覧の札の件名。
- **Body** (400, 14px / 1.55): 本文の既定。返信案と問い合わせ本文は 1.75 で、pre-wrap。textarea は 1.7。
- **Label** (700, 12px, 字間 0.06em): 節見出し（問い合わせ、返信案、警告、各段）。`ink-2`。表頭は同じ 700 の 12px で字間 0.04em、下に 2px の墨の罫。
- **Identifier** (400, 12px, 字間 0.04em): ID（`ink-3`）。担当名・カテゴリは 400 の 12〜13px に 0.01em。
- **Caption** (400, 12〜12.5px): メタ情報、脚注、ヒント、札の文字。札の緊急度・状態は 700。
- **Diagram** (SVG): 駅名 700 の 12px（`ink`）、ms 11px（`ink-2`、影は `ink-3`）、注記 11px、凡例 10.5px（`ink-3`）。

### Named Rules
**The One Family Rule.** 字は 1 族。等幅フォントや Web フォントを読み込まない。識別子は字間で区別し、字体では区別しない。

**The Tabular Rule.** 数字は常に tabular-nums。所要時間（ms）、文字数、警告数は桁が揃って並ぶ。

## Layout

上部 56px の帯（下に 2px の墨の罫）が殻で、左に名前と副題、タブ 2 つ、右端に run 選択。帯の下は見出し行（上 18px）と本体（左右 28px、上 16px、下 32px）。

承認キューは 2 列の分割で、左 `minmax(320px, 5fr)` の一覧と右 `minmax(440px, 7fr)` の詳細、間 24px。一覧の札は 10px 間隔で縦に並び、詳細は `top: 16px` で粘着する。1440×900 では一覧が約 500px。

追跡画面は 1 列。段の図の札、問い合わせの札、返信案の比較（本番｜影の 2 列、間 18px）、各段のログ（左 180px の段名・担当・ms、右に JSON、行の間 8px）。影の比較画面は札 2 枚に表。

間隔は 6 / 8 / 10 / 12 / 14 / 16 / 18 / 20 / 24 / 28px の小刻みな目盛で、密度は高い。方眼は 24px。

1000px 未満: 分割と 2 列は 1 列に落ち、詳細の粘着は解け、帯は折り返して名前 48px・タブ 44px・run 選択は幅いっぱいの 44px。左右の余白は 16px。大きいスジは最小 640px を保って縮めず、入れ物（`.suji-fit`、`.diagram`）が横に送る。表も最小 560px で `.tablewrap` が横に送る。

## Elevation & Depth

ほぼ平坦で、深さは地の明度の段差で持つ。紙白の地 → 沈んだ白の札 → 白の読む面、の 3 段。白い札の中では問い合わせ本文と段の図を紙白に戻してもう一段引く。影（box-shadow）は選択中の一覧項目 1 つにだけ落ち、1px 持ち上がる。それ以外の面に影はない。

### Shadow Vocabulary
- **選択の持ち上がり** (`box-shadow: 0 6px 18px rgba(28, 36, 48, 0.12), 0 1px 2px rgba(28, 36, 48, 0.08)` + `translateY(-1px)`): 一覧で選択中の札だけ。200ms で出入りする。

### Named Rules
**The One Lift Rule.** 影は選択中の一覧項目 1 つにだけ落ちる。非選択の項目は不透明度ではなく地の明度（#fbfbf9）で沈める。補助文字の対比を保つため。

## Shapes

角はごく小さい。操作の部品（ボタン、入力欄、札、警告、フォーカス輪）は 2px、面（札、詳細、ログの行、図の面）は 3px。罫は 3 種: 帯の下と表頭の下の 2px の墨、表の行と操作列の上の 1px の薄い罫、ボタンと入力欄の 1px の墨の枠。札（カード）に枠線はなく、白が紙白の上に置かれることで面になる。影の段のログの行だけ 1px の破線の輪郭（内側）で「影」を示す。

記号は 10px 前後の SVG の幾何で、スジと同じ語彙: 三角 = LLM の指摘や失敗、四角 = 決定論的検証の警告、丸 = 問題なし。グリフアイコンやアイコンフォントは使わない。

## Components

### Buttons
- **Shape:** 2px の角、1px の墨の枠、700 の 14px、内側 7px 14px
- **Primary** (`.btn.primary`): 墨の塗りに紙白の文字。ホバーで少し明るい墨（#2a3444）。「採用して送信箱へ」「修正して採用」「昇格する」。操作列の右端に 1 つ。
- **Default** (`.btn`): 白地に墨の枠と文字。ホバーで薄墨の地。「修正」「やめる」「影を本番に昇格」。
- **Danger** (`.btn.danger`): 枠と文字が高緊急度の赤。ホバーで赤の塗り。「却下」だけ。
- **Hover / Focus:** 背景と文字色が 120ms。フォーカスは 2px の墨の輪郭、2px 外側。無効は不透明度 0.45。

### Chips（札）
- **Style:** 枠線なし、2px の角、12px、内側 1px 8px。塗りと文字色だけ。
- **State:** 緊急度（高・中・低、700）は `*-tint` / `*-text`。状態は 未決 = 薄墨、採用・修正・pass = 緑、却下・fail = 赤、flag = 橙。カテゴリ（`.badge.cat`）は塗りなしの文字だけ。

### Cards / Containers
- **Corner Style:** 3px
- **Background:** 読む面は白。一覧のクリックできる札は沈んだ白（#fbfbf9）で、ホバーと選択で白に。
- **Shadow Strategy:** 選択中の一覧項目だけ（Elevation 参照）。
- **Border:** なし。
- **Internal Padding:** 札 12px 16px、詳細 18px 22px 20px、ログの行 10px 14px、図の面 10px 14px 6px。

### Inputs / Fields
- **Style:** 白地、1px の墨の枠、2px の角、6px 9px、フォントは継承。textarea は最小 220px、行間 1.7。プレースホルダは `ink-3`。
- **Focus:** 2px の墨の輪郭、2px 外側（`:focus-visible` の共通規則）。キャレットとチェックボックスのアクセント色は墨。
- **Error / Disabled:** 専用の様式なし。失敗はメッセージ（`.msg.err`、赤の塗り）で示す。

### Navigation
- 56px の帯、下に 2px の墨の罫。タブは 700、`ink-2`、内側 0 14px、下に 3px の下線（透明）。ホバーで墨、選択中は墨の文字と墨の下線（罫に 2px 重なる）。1000px 未満では折り返し、タブ 44px。

### Warnings（`.warn`）
- 2px の角、7px 10px、13px。左に 10px の記号（Mark）。決定論的検証 = 橙の塗りに四角、LLM の指摘・失敗 = 赤の塗りに三角、問題なし = 緑の塗りに丸。方向の契約の「左に 3px の赤罫」は出荷物にはなく、塗りと記号で分けている。

### Tables
- 行は 1px の薄い罫、表頭は 700 の 12px に 2px の墨の罫。セル 9px 10px、数値は右寄せ。クリックできる行はホバーで紙白。良し悪しは緑（`.better`）と赤（`.worse`）の 700 の文字だけ。

### Suji（スジ、署名部品）
問い合わせ 1 件の進行を 4 駅の運行図表で描く SVG。一覧（`size="s"`、幅 400 の viewBox、駅名なし、高さ 14 / 24）と詳細・追跡（`size="l"`、ResizeObserver で入れ物の幅、最小 640px、駅名と ms つき、高さ 66 / 96）は同じ部品の大きさ違い。

- **駅:** 分類・担当・検査・キューの 4 点を等間隔に置く（左右 24px、小は 6px の余白）。駅は墨の丸（半径 3.4、白の縁 1.5）。線路床は `rule` の 1px 点線（1 4）で全区間に敷く。
- **線:** 本番は実線、影は破線（6 4）で担当の駅から。太さと色は緊急度: 高 3px 赤、中 2px 橙、低 1.2px 墨。影の線は本番の 0.6 倍（最小 1.2px）で同じ色、駅は半径 2.6。
- **記号:** 返信案なしで止まるときは 12px のスタブの後に車止め（2px の縦棒 2 本、高さ 12）。失敗は駅の上に 11px の三角。検査の駅の上に 6px の四角（決定論的検証の警告）と 7px の三角（LLM のレビュー指摘）。人の判断が済むとキューの駅が 9px の塗りの四角になる。全て線と同じ色。
- **文字:** 駅名は 700 の 12px、所要時間は駅の下 16px に 11px の数字（影は `ink-3`）。担当の駅に渡した記事 ID の注記。右下に凡例（本番 / 影）。
- **動き:** 詳細で項目が選ばれたとき、本番の線だけ `stroke-dashoffset` で左から 180ms（`cubic-bezier(0.16, 1, 0.3, 1)`）引かれる。一覧の小さいスジは動かない。

### Mark（記号）
10px の SVG。三角 = LLM の指摘や失敗（`high-text`）、四角 = 決定論的検証の警告（`normal-text`）、丸 = 問題なし（`ok-text`）。警告の行と返信案の比較で使う。

## Do's and Don'ts

### Do:
- **Do** 駅は分類・担当・検査・キューの 4 つを等間隔に置き、所要時間は駅の下の数字（ms）で添える。位置を時間に比例させない。
- **Do** 影の線（破線）は担当の駅から始める。分類は本番と共通なので影の線は分類に無い。
- **Do** 方眼（24px、#dfe5ec）は殻（帯と一覧の背景）だけに敷く。本文・返信案・警告の面は無地の白。
- **Do** 状態は線の形で持つ: 本番 = 実線、影 = 破線、返信案なし = 線が止まって車止め、失敗 = 駅の三角、判断済み = キューの塗りの四角。色は緊急度の 3 段だけ。
- **Do** 詳細の情報の順序は 本文 → 返信案（本番｜影）→ 警告 → 操作 を守る。主ボタンは操作列の右端に 1 つ。
- **Do** 札は枠線なしで、塗り（`*-tint`）か文字色（`*-text`）だけ。小さな文字は地の上で 4.5:1 以上。
- **Do** 非選択の一覧項目は地の明度（#fbfbf9）で沈め、選択中だけ 1 つの影で持ち上げる。
- **Do** 記号はスジと同じ語彙の SVG（三角・四角・丸、10px 前後）で統一する。
- **Do** 動きは状態の変化だけ（120〜200ms、`cubic-bezier(0.16, 1, 0.3, 1)`）。`prefers-reduced-motion` で全て止める。
- **Do** hash の URL（#/queue、#/queue/ID、#/inquiry/ID、#/shadow）を維持する。変えるなら scripts/screenshots.py も同じ change で直す。
- **Do** 返信案には文字数だけを添える。

### Don't:
- **Don't** 緊急度の 3 段と合格の緑以外に色を増やさない。新しい状態は線の形か塗りの濃淡で持つ。
- **Don't** Web フォント、等幅フォント、アイコンフォント、グリフアイコンを読み込まない。字は OS のゴシック 1 族。
- **Don't** 読む面（本文・返信案・警告・表）に方眼や影を置かない。
- **Don't** 札やカードに枠線を付けない。ボタンと入力欄の 1px の墨の枠だけが枠。
- **Don't** 非選択の項目や補助文字を不透明度で沈めない（無効のボタンの 0.45 だけが例外）。
- **Don't** 依存を足さない（react と react-dom のみ、UI ライブラリや CSS フレームワークを入れない）。
- **Don't** 画面に業務ロジックを持ち込まない。verify.py の返信案の長さ上限を画面に写さない。超過は検証の警告が担い、画面は文字数だけを出す。
- **Don't** 近黒の地、色札と角丸の大きいカード、青いボタン、灰の枠線の管理画面に戻さない。
- **Don't** 読み込みの演出や装飾のアニメーションを足さない。
