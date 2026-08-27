"""Troupe の画面の決まり — 見た目の正本（設計/人に見えるもの §5 が指す1枚。CSS が執行者）。

主題は「静かな自動化」。臨床の静けさの上に、脈が打っていることだけを感じさせる。

1. **モチーフは「帳簿・脈」——器は原稿どおり平らな白い窓。** 上のインクの帯と
   その下の横一列ナビが骨格。内容は白地に**温かい灰の罫**で切る（#edebe7/#dedcd7）。
   箱は1段まで・枠と拡散影を併用しない。節の札は .sec-label（大文字+インクの下線）。
   脈＝動きの語彙（下の4）。
1b. **書体は2系統で決める。** 見出し・銘は Source Serif 4（紙の記録＝文書の書体。
   Georgia が控え）。本文は system、**数字と ID は等幅数字**。角丸は 8/10/14 の3段だけ。
2. **頁の頭は「見出し・数・次の一手」**（.page-head）。数えられるものは数を先に言う
   （"3 decisions waiting"）。最初の一画面で「何件・次に何を」が読める。
   スクロールは詳細のためだけ。
3. **塗るのは判断だけ。** 塗りボタンは Sign / Approve / Reply / Confirm の4つ。
4. **動きの語彙は「脈・到着・灯」の3つ。** 脈=60秒の拍の帯・機械が支度した/人を待つ
   チップの淡い鼓動・帳簿の最新行の引いていく色——**同期は装わない**（リズムを見せるだけで、
   瞬間を主張しない）。それ以外は動かさない。prefers-reduced-motion では全部止まる。
5. **色は語彙**: 緑=署名済み/通った・琥珀=人が要る・赤=破壊/期限切れ・青=情報・灰=不活性。
   人格の色（who の点・地図の担当色）は状態の5色と混ぜない。
   到着=新しい行のスライドイン+5秒の退色(row-in)・灯=環の段が出来事で一瞬点る(is-lit)。
   トーストは出さない・予告のカウントダウンも出さない——**起きた事実だけが動く**。
6. **表は貼り付く頭と件数を持つ。** 長い一覧は頁送り（100件）か絞りを持つ。
7. **携帯（≤900px）は棚が上バーに畳まれ、2ペインは1列に落ちる。** 横スクロールは表の中だけ。
8. **言葉は用語集の橋そのまま。** 和語を画面に出さない。
"""

_STYLE = """
/* ================================================================
   Troupe — style.css  ·  design “clinical calm”
   ui/web.py の _STYLE を丸ごと置き換える1枚。
   外部アセットなし・システムフォントのみ・JSはGoogle Maps スロットだけ。
   ライト/ダーク: color-scheme + #fff/var(--ink) + color-mix（現行方式踏襲）。

   原則:
     · 色は状態にだけ使う。
         緑  = 署名済み / 承認済み / 完了
         琥珀 = 下書き / あなたの判断待ち / 期限接近
         赤  = 破壊的操作 / 失敗 / 期限切れ
         青  = 情報（下書き準備済み / AI稼働中）・唯一の塗りボタン
         灰  = 不活性（中止・未着手・使用済み）
     · 塗りつぶしボタンは Sign / Approve（質問カードの Reply）だけ。
     · 階層は余白・罫線・字の大きさで作る。飾りは作らない。
     · チップの記号（✓ / ⚠）は HTML 側の文字として入れる（白黒印刷でも残る）。

   目次:
     0. tokens & reset          8. Visit (/visit)
     1. shell（sidebar/nav/page） 9. Inbox
     2. text & links           10. Patient chart
     3. cards & folds          11. Agreements · Automations
     4. chips·badges·seals·who 12. markdown (.md) · guide · how
     5. buttons & forms        13. banners · refusal · empty
     6. tables · pager         14. focus & a11y
     7. My Day (/day)          15. narrow（top bar）· 16. print（day sheet）
   ================================================================ */

/* ---------- 0. tokens & reset ---------- */
:root {
  /* 原稿(Troupe UI.dc.html)はライト1本に決め打ち——こちらも明示的に寄せる */
  color-scheme: light;

  /* 状態の色相 — UI に存在する有彩色はこの5つだけ */
  /* 状態の色は自前の値——既定パレットの色相から少し外す(照明と印刷で見た) */
  --ok:      #1b7a4a;
  --warn:    #a86206;
  --danger:  #b3271e;
  --info:    #2158c9;
  --primary: #1f5f9e;   /* 塗りつぶし: Sign / Approve / Reply / Confirm */
  --r-sm: 6px; --r-md: 6px; --r-lg: 12px;  /* 原稿は6px基調・大枠だけ12px */
  --serif: "Source Serif 4", "Source Serif Pro", Georgia, "Times New Roman", serif;

  /* 無彩色は原稿の温かい灰(生成り寄り)——冷たい灰と混ぜない */
  --line:        #edebe7;
  --line-strong: #dedcd7;
  --line-hard:   #cbc8c2;   /* 枠線(ボタン・入力) */
  --muted:       #6b7076;
  --muted-strong:#55595f;
  --faint:       #f4f3f0;
  --tint:        #fbfaf8;   /* 淡い生成りのパネル */
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;

  /* 舞台の色 — インクの棚（両テーマで不変）と、脈の鼓動 */
  --ink:       #10161d;
  --ink-line:  #232c36;
  --ink-text:  #e8edf2;
  --ink-muted: #93a1af;
  --beat:      #4cc3ff;
}
* { box-sizing: border-box; }
html { height: 100%; }
body {
  min-height: 100%;
  margin: 0;
  font: 14.5px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, "Hiragino Sans", "Noto Sans JP", sans-serif;
  color: #10161d;
  background: #fff;   /* モックの窓=画面そのもの。台紙(#e9e8e4)は文書の飾りで製品には無い */
  -webkit-text-size-adjust: 100%;
}

/* ---------- 1. shell — モックの1440×900の窓は「画面そのもの」の見立て ----------
   帯は画面の端から端まで。中身(bar-inner・main)だけ max 1440 で中央・側余白28px固定。
   .topbar = 銘・クリニック名・拍の帯・席(右端) — インクの帯(高さ44)
   .navbar = 平らな1列(今すぐ→記録) + 右端に How/Ask — 白い帯(高さ52・インクの下線) */
.window { min-height: 100vh; display: flex; flex-direction: column; }
.window > main { flex: 1 1 auto; }
.topbar { background: var(--ink); color: var(--ink-text); }
.topbar .bar-inner { height: 44px; gap: 14px; }
/* 幅の正本は1つ——帯の中身と本文が同じ内寸(max 1440・側余白28px)で端がそろう */
.bar-inner, main, .page {
  width: 100%; max-width: 1440px; margin: 0 auto;
  padding-left: 28px; padding-right: 28px;
}
.bar-inner { display: flex; align-items: center; gap: 16px; }
.brand {
  display: flex; align-items: center; gap: 8px; flex: none;
  font-family: var(--serif);
  font-size: 17px; font-weight: 600; letter-spacing: .01em;
  color: var(--ink-text); text-decoration: none;
}
.topbar__clinic {
  flex: none; font-size: 12px; color: var(--ink-muted); white-space: nowrap;
}
.topbar .cadence { flex: 1 1 auto; margin: 0 8px; }
.topbar__beat {
  flex: none; font-family: var(--mono); font-size: 11px;
  letter-spacing: .05em; color: var(--ink-muted); white-space: nowrap;
}
.cadence {
  display: block; height: 3px;
  background: rgba(255,255,255,.09); overflow: hidden;
}
.cadence__fill {
  display: block; height: 100%; width: 100%;
  background: linear-gradient(90deg, rgba(76,195,255,0), rgba(76,195,255,.35) 65%, #4cc3ff);
  transform-origin: left;
  animation: cadence 60s linear infinite;
}
@keyframes cadence { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.whoami { flex: none; display: flex; align-items: center; gap: 8px; font-size: 12px; }
.whoami small {
  color: var(--ink-muted); font-size: 10px;
  letter-spacing: .06em; text-transform: uppercase;
}
.seat-form { display: flex; gap: 6px; margin: 0; }
.seat-form select {
  font-size: 12px; padding: 3px 6px; max-width: 200px;
  background: rgba(255,255,255,.06); color: var(--ink-text);
  border: 1px solid var(--ink-line); border-radius: var(--r-sm);
}
.seat-form .btn {
  font-size: 12px; padding: 3px 10px;
  background: rgba(255,255,255,.06); color: var(--ink-text);
  border-color: var(--ink-line);
}
.seat-form .btn:hover { background: rgba(255,255,255,.12); }

.navbar {
  background: #fff; border-bottom: 1px solid var(--ink);
  position: sticky; top: 0; z-index: 30;
}
.navbar .bar-inner { height: 52px; gap: 20px; }
.nav {
  display: flex; align-items: stretch; gap: 20px; height: 100%;
  flex: 1 1 auto; min-width: 0;
  overflow-x: auto; -webkit-overflow-scrolling: touch;
}
.nav a {
  display: flex; align-items: center; text-decoration: none;
  color: var(--muted-strong); font-size: 14px; white-space: nowrap;
}
.nav a:hover { color: var(--ink); }
.nav a[aria-current="page"], .nav a.is-active {
  color: var(--ink); font-weight: 650;
  box-shadow: inset 0 -2px 0 0 var(--ink);
}
.nav-badge {
  margin-left: 5px; font-family: var(--mono);
  font-size: 12px; font-weight: 700; color: var(--warn);
  font-variant-numeric: tabular-nums;
}
.nav-help { flex: none; display: flex; align-items: center; gap: 20px; }
.nav-ask {
  display: flex; align-items: center; gap: 7px;
  font-size: 13px; font-weight: 600; text-decoration: none;
  color: #fff; padding: 7px 16px; border-radius: var(--r-sm);
  background: var(--ink); border: 1px solid var(--ink); cursor: pointer;
}
.nav-ask:hover { background: #1a232d; }
.nav-quiet {
  font-size: 12.5px; color: var(--muted); text-decoration: none; white-space: nowrap;
}
.nav-quiet:hover { color: var(--ink); text-decoration: underline; }

/* 開示バー — 合成の座長が動いているあいだの、細い琥珀の帯 */
.notice-bar {
  font-size: 12.5px; line-height: 1.5; padding: 6px 28px;
  color: color-mix(in srgb, var(--warn) 72%, var(--ink));
  background: color-mix(in srgb, var(--warn) 8%, #fff);
  border-bottom: 1px solid color-mix(in srgb, var(--warn) 26%, transparent);
}

main, .page { padding-top: 22px; padding-bottom: 48px; }
.paper { background: transparent; }  /* 原稿は平らな窓——包みは残すが箱にしない */
/* 頁の頭 — 見出し・数・次の一手(§5)。数えられるものは数を先に言う */
.page-head {
  display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
  margin: 0 0 6px;
}
.page-head .page-title { margin: 0; }
.page-head__aside { margin-left: auto; font-size: 13.5px; color: var(--muted); }
.count-pill {
  display: inline-block; font-size: 12.5px; font-weight: 600;
  font-variant-numeric: tabular-nums; white-space: nowrap;
  padding: 2px 11px; border-radius: 999px;
  color: var(--muted); background: var(--faint); border: 1px solid var(--line);
}
.count-pill strong { color: var(--ink); }
.page-title {
  font-family: var(--serif); font-size: 24px; font-weight: 600;
  letter-spacing: 0; margin: 0 0 4px;
}
.page-sub { font-size: 13.5px; color: var(--muted); margin: 0 0 22px; max-width: 68ch; }
.section-title { font-size: 15px; font-weight: 650; margin: 30px 0 10px; }
.crumbs { font-size: 13px; color: var(--muted); margin: 0 0 6px; }
.crumbs a { color: inherit; }

/* ---------- 2. text & links ---------- */
a { color: inherit; }
main a { text-decoration-color: var(--line-strong); text-underline-offset: 2px; }
main a:hover { text-decoration-color: currentColor; }
.link-action { text-decoration: none; font-weight: 550; white-space: nowrap; }
.link-action:hover { text-decoration: underline; }
.sub { font-size: 13px; color: var(--muted); }
.mono { font-family: var(--mono); font-size: 12.5px; }
.id { font-family: var(--mono); font-size: 12.5px; color: var(--muted); }
.num { font-variant-numeric: tabular-nums; }
.visually-hidden {
  position: absolute; width: 1px; height: 1px; margin: -1px;
  overflow: hidden; clip-path: inset(50%); white-space: nowrap;
}

/* ---------- 3. cards & folds ---------- */
.card, .row {
  border: 1px solid var(--line); border-radius: var(--r-md);
  padding: 16px 18px; margin-bottom: 14px; background: #fff;
}
.card__head, .head {
  display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap;
  margin-bottom: 8px;
}
.card__title, .head .title, .ref-name { font-weight: 600; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 5px 16px; margin: 8px 0 0; }
dt { font-size: 13px; color: var(--muted); }
dd { margin: 0; white-space: pre-wrap; }
.fold { margin-top: 10px; }
.fold > summary {
  cursor: pointer; user-select: none; font-size: 13px; color: var(--muted);
  padding: 3px 0; width: max-content;
}
.fold > summary:hover { color: var(--ink); }
.fold[open] > summary { margin-bottom: 6px; }

/* ---------- 4. chips · badges · seals ----------
   chip  = 状態。色を持つ唯一の常連。記号は HTML の文字で: “Signed ✓” “⚠ Needs your answer”
   badge = 種類（Visit note / Weekly report / Request / Task）。常に無彩色の枠。
   seal  = 記録の印（DRAFT / SIGNED / USED）。カルテと下書きパネルの見出しに捺す。 */
.chip {
  --c: var(--ink);
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600; line-height: 1.5;
  padding: 1.5px 9px; border-radius: 999px; white-space: nowrap;
  color: color-mix(in srgb, var(--c) 70%, var(--ink));
  background: color-mix(in srgb, var(--c) 9%, #fff);
  border: 1px solid color-mix(in srgb, var(--c) 32%, transparent);
}
a.chip { text-decoration: none; }
a.chip:hover { border-color: color-mix(in srgb, var(--c) 60%, transparent); }
/* 状態 → 色。この対応が正本 */
.chip--signed, .chip--approved, .chip--done      { --c: var(--ok); }
.chip--draft-ready, .chip--working               { --c: var(--info); }
.chip--needs-approval, .chip--needs-answer,
.chip--expiring                                  { --c: var(--warn); }
/* 淡い鼓動 — 機械が支度した印と、人を待つ印だけが静かに脈打つ */
.chip--draft-ready, .chip--needs-approval, .chip--needs-answer {
  animation: chipbeat 3.2s ease-out infinite;
}
@keyframes chipbeat {
  0%   { box-shadow: 0 0 0 0 color-mix(in srgb, var(--c) 30%, transparent); }
  55%  { box-shadow: 0 0 0 5px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}
.chip--failed, .chip--expired                    { --c: var(--danger); }
/* 無彩色のまま: scheduled / queued / submitted / no-draft / used / cancelled / stopped */
.chip--no-draft, .chip--used { color: var(--muted); font-weight: 500; }
.chip--cancelled, .chip--stopped {
  color: var(--muted); font-weight: 500; text-decoration: line-through;
}
.badge {
  display: inline-block; font-size: 11px; font-weight: 600;
  letter-spacing: .07em; text-transform: uppercase;
  padding: 1px 7px; border-radius: 4px;
  color: var(--muted); border: 1px solid var(--line-strong); background: transparent;
}
.seal {
  display: inline-block; font-size: 11px; font-weight: 700;
  letter-spacing: .09em; padding: 1.5px 8px; border-radius: 4px;
}
.seal--draft, .state-draft {
  color: color-mix(in srgb, var(--warn) 70%, var(--ink));
  background: color-mix(in srgb, var(--warn) 13%, #fff);
}
.seal--signed, .state-final {
  color: color-mix(in srgb, var(--ok) 70%, var(--ink));
  background: color-mix(in srgb, var(--ok) 12%, #fff);
}
.seal--used { color: var(--muted); background: var(--faint); }
/* 旧 .state 互換 — 無彩チップとして残す */
.state {
  font-size: 12px; padding: 1.5px 9px; border-radius: 999px;
  background: var(--faint);
}
/* who = 履歴の「誰が」。状態でなく人格の見分け——点にだけ色を置く。
   紫は地図の担当色と同系（状態の5色とは別の、人格の色）。 */
.who {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 13px; white-space: nowrap;
}
.who small {
  font-size: 10px; font-weight: 600; letter-spacing: .07em;
  text-transform: uppercase; color: var(--muted);
}
.who-dot {
  flex: none; width: 8px; height: 8px; border-radius: 50%;
  background: var(--line-hard);   /* 原稿の点の無彩 #cbc8c2 */
}
.who--human .who-dot { background: var(--ok); }
.who--agent .who-dot { background: #7c3aed; }
.who--clock .who-dot { background: var(--line-hard); }

/* ---------- 5. buttons & forms ----------
   3階層:  primary(塗り) = Sign / Approve / Reply だけ
           secondary(枠) = 既定。それ以外の操作すべて
           destructive(赤テキスト) = 取り消し系。2段階目は .is-confirm を付ける */
button, .btn {
  font: inherit; font-size: 14px; font-weight: 500;
  padding: 6px 16px; border-radius: var(--r-sm); cursor: pointer;
  border: 1px solid var(--line-hard); background: #fff; color: inherit;
}
button:hover, .btn:hover { background: var(--faint); }
.btn--small { padding: 3.5px 11px; font-size: 13px; }
.btn--primary {
  background: var(--primary); border-color: var(--primary);
  color: #fff; font-weight: 600;
}
.btn--primary:hover {
  background: color-mix(in srgb, var(--primary) 86%, black);
  border-color: color-mix(in srgb, var(--primary) 86%, black);
}
.btn--primary.is-confirm {
  background: color-mix(in srgb, var(--primary) 80%, black);
  border-color: color-mix(in srgb, var(--primary) 80%, black);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 22%, transparent);
}
.btn--destructive {
  border-color: transparent; background: none; padding: 6px 6px;
  color: color-mix(in srgb, var(--danger) 72%, var(--ink));
}
.btn--destructive:hover { background: none; text-decoration: underline; }
.btn--destructive.is-confirm {
  border-color: color-mix(in srgb, var(--danger) 55%, transparent);
  background: color-mix(in srgb, var(--danger) 9%, #fff);
  padding: 6px 14px; text-decoration: none; font-weight: 600;
}
.btn--destructive.is-confirm:hover {
  background: color-mix(in srgb, var(--danger) 14%, #fff);
}
.confirm-note { font-size: 12.5px; color: color-mix(in srgb, var(--danger) 70%, var(--ink)); }
input[type=text], input[type=date], input[type=number], select, textarea {
  font: inherit; padding: 6px 10px; border-radius: var(--r-sm);
  border: 1px solid var(--line-hard); background: #fff; color: inherit;
}
textarea { width: 100%; min-height: 112px; line-height: 1.6; padding: 10px 12px; resize: vertical; }
input[type=checkbox] { accent-color: var(--primary); width: 15px; height: 15px; }
.field { display: grid; gap: 4px; align-content: start; }
.field > label { font-size: 13px; font-weight: 600; }
.field .hint { font-size: 12.5px; color: var(--muted); font-weight: 400; }
form.act { display: inline-flex; gap: 8px; margin: 0; align-items: center; } /* 旧互換 */
.actions, .card-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.card-actions { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); }
.push { margin-left: auto; }
/* 検索の一列 — 欄・選択・ボタンを1行に。狭ければ折り返す */
.search-form {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin: 0 0 20px;
}
.search-form input[type=text] { flex: 1 1 150px; min-width: 0; max-width: 260px; }
.search-form select { flex: none; }

/* ---------- 6. tables · pager ---------- */
.wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th {
  text-align: left; font-size: 11.5px; font-weight: 600;
  letter-spacing: .07em; text-transform: uppercase; color: var(--muted);
  padding: 8px 12px; border-bottom: 1px solid var(--line-strong);
}
@media (min-width: 900.1px) {
  th { position: sticky; top: 0; z-index: 2; background: #fff; }
}
td {
  padding: 9px 12px; border-bottom: 1px solid var(--line);
  vertical-align: top; font-variant-numeric: tabular-nums;
}
tbody tr:hover { background: var(--faint); }
.cell-danger { color: color-mix(in srgb, var(--danger) 75%, var(--ink)); font-weight: 600; }
.cell-when {
  font-family: var(--mono); font-size: 11.5px; color: var(--muted);
  white-space: nowrap;
}
/* 帳簿の最新行 — 開いた瞬間、着いたばかりの色が静かに引く */
.ledger-events tr:nth-child(2) td { animation: freshrow 2.4s ease-out 1; }
@keyframes freshrow {
  from { background: color-mix(in srgb, var(--beat) 14%, transparent); }
  to   { background: transparent; }
}

/* 済んだ一行 — 承認の軌跡: 緑がひと呼吸で退く(帳簿に積まれた事実の言い切り) */
.banner--acted {
  border: 1px solid color-mix(in srgb, var(--ok) 35%, #fff);
  background: color-mix(in srgb, var(--ok) 8%, #fff);
  color: color-mix(in srgb, var(--ok) 75%, var(--ink));
  padding: 8px 14px; border-radius: var(--r-sm); font-size: 13.5px;
  margin: 0 0 14px; animation: acted-fade 4s ease-out 1;
}
@keyframes acted-fade {
  0% { background: color-mix(in srgb, var(--ok) 22%, #fff); }
  100% { background: color-mix(in srgb, var(--ok) 8%, #fff); }
}
.inbox-knock {
  margin: 0 0 12px; padding: 7px 12px; font-size: 13px;
  border: 1px solid color-mix(in srgb, var(--info) 30%, #fff);
  background: color-mix(in srgb, var(--info) 6%, #fff);
  border-radius: var(--r-sm); animation: row-in 5s ease-out 1;
}

/* ---------- いま(/now) — 環のいまと生の帯。動きは到着(row-in)と灯(is-lit)だけ ---------- */
.loop {
  display: flex; align-items: stretch; gap: 0;
  margin: 18px 0 6px;
}
.loop-stage {
  flex: 1 1 0; min-width: 0; font: inherit; text-align: left; cursor: pointer;
  display: flex; flex-direction: column; gap: 3px;
  padding: 12px 14px; background: #fff; position: relative;
  border: 1px solid var(--line-strong); border-radius: var(--r-sm);
}
.loop-stage:hover { border-color: var(--ink); }
/* 押せる合図——全段の隅に▾。開いている段は濃く、地の色が下の説明(loop-note)と繋がる */
.loop-stage::after {
  content: '▾'; position: absolute; right: 11px; bottom: 8px;
  font-size: 10px; color: var(--muted); opacity: .55;
}
.loop-stage:hover::after, .loop-stage.is-open::after { color: var(--ink); opacity: 1; }
.loop-stage.is-open { border-color: var(--ink); background: var(--tint); }
.loop-stage__name { font-family: var(--serif); font-size: 15px; font-weight: 600; }
.loop-stage__sub { font-size: 11.5px; color: var(--muted); }
.loop-stage__n {
  font-size: 22px; font-weight: 650; line-height: 1.2; margin-top: 2px;
  font-variant-numeric: tabular-nums;
}
.loop-stage--you { border-color: color-mix(in srgb, var(--warn) 55%, #fff); }
.loop-stage--you .loop-stage__n { color: var(--warn); }
/* 中身のある段は生きて見える——AI段は青の忙し色、You段は琥珀の鼓動(数が0なら静か) */
.loop-stage__pip { display: none; width: 7px; height: 7px; border-radius: 50%;
  flex: none; margin-right: 6px; vertical-align: 1px; }
.loop-stage__sub { display: flex; align-items: center; }
.loop-stage.is-busy .loop-stage__pip { display: inline-block;
  animation: working-blink 1.4s ease-in-out infinite; }
.loop-stage--ai.is-busy { border-color: var(--info);
  background: color-mix(in srgb, var(--info) 5%, #fff); }
.loop-stage--ai.is-busy .loop-stage__sub { color: var(--info); }
.loop-stage--ai .loop-stage__pip { background: var(--info); }
.loop-stage[data-stage='clock'] .loop-stage__pip { background: var(--line-hard); }
.loop-stage[data-stage='check'] .loop-stage__pip { background: var(--line-hard); }
.loop-stage--you .loop-stage__pip { background: var(--warn); }
.loop-stage--you.is-busy { animation: you-beat 3.2s ease-out infinite; }
@keyframes you-beat {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--warn) 38%, transparent); }
  55% { box-shadow: 0 0 0 6px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}
/* 数の脈 — 値が変わった瞬間だけ、その数字が一拍うつ(描画と連動しない鳴動は置かない) */
.tick { animation: num-tick .7s ease-out 1; }
@keyframes num-tick {
  0% { transform: scale(1); }
  30% { transform: scale(1.22); color: var(--info); }
  100% { transform: none; }
}
[data-now] { display: inline-block; }

/* つなぎ線を流れる点——前の段に中身があるあいだだけ */
.loop-link { position: relative; }
.loop-link.has-flow::after {
  content: ''; position: absolute; top: -4.5px; left: 3px;
  width: 8px; height: 8px; border-radius: 50%; background: var(--info);
  animation: working-blink 1.2s ease-in-out infinite;
}
.loop-stage.is-lit { animation: stage-lit 1.6s ease-out 1; }
@keyframes stage-lit {
  0% { border-color: var(--beat); box-shadow: 0 0 0 3px color-mix(in srgb, var(--beat) 35%, transparent); }
  100% { border-color: var(--line-strong); box-shadow: 0 0 0 0 transparent; }
}
.loop-link { flex: none; width: 22px; align-self: center; border-top: 1.5px dashed var(--line-hard); }
.loop-note {
  margin: 10px 0 0; padding: 10px 14px; font-size: 13.5px; max-width: 76ch;
  background: var(--tint); border: 1px solid var(--line); border-radius: var(--r-sm);
}
.now-cols { display: grid; grid-template-columns: 1fr 1.3fr 1fr; gap: 26px; margin-top: 18px; }
#now-feed { max-height: 340px; overflow-y: auto; overscroll-behavior: contain; }
#now-working { max-height: 340px; overflow-y: auto; }
.now-col__head {
  font-size: 11px; font-weight: 650; letter-spacing: .14em; text-transform: uppercase;
  color: var(--muted-strong); border-bottom: 1px solid var(--ink);
  padding-bottom: 6px; margin: 0 0 10px;
}
.now-working__item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 0; border-bottom: 1px solid var(--line); font-size: 13.5px;
}
.now-working__item a { text-decoration: none; }
.now-working__dot {
  flex: none; width: 7px; height: 7px; border-radius: 50%; margin-left: auto;
  background: var(--info); animation: working-blink 1.4s ease-in-out infinite;
}
@keyframes working-blink { 0%, 100% { opacity: 1; } 50% { opacity: .25; } }
.now-evt {
  display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;
  padding: 6px 0; border-bottom: 1px solid var(--line); font-size: 13px;
}
.now-evt__at { color: var(--muted); font-size: 12px; }
.now-evt__what { color: var(--muted-strong); }
.now-evt__head { text-decoration: none; font-weight: 550; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
.row-in { animation: row-in 5s ease-out 1; }
@keyframes row-in {
  0% { opacity: 0; transform: translateY(-8px); background: color-mix(in srgb, var(--beat) 14%, #fff); }
  10% { opacity: 1; transform: none; }
  80% { background: color-mix(in srgb, var(--beat) 14%, #fff); }
  100% { background: transparent; }
}
.now-waiting { display: flex; align-items: baseline; gap: 10px; padding: 6px 0 2px; }
.now-waiting__n { font-size: 40px; font-weight: 650; font-variant-numeric: tabular-nums; }
.now-waiting--some .now-waiting__n { color: var(--warn); }
.now-waiting--some { animation: waiting-beat 3.2s ease-out infinite; }
@keyframes waiting-beat {
  0% { text-shadow: none; } 55% { text-shadow: 0 0 14px color-mix(in srgb, var(--warn) 45%, transparent); }
  100% { text-shadow: none; }
}
@media (max-width: 900px) {
  .loop { flex-direction: column; gap: 8px; }
  .loop-link { width: 0; height: 14px; border-top: 0; border-left: 1.5px dashed var(--line-hard); margin-left: 24px; }
  .now-cols { display: block; }
  .now-col { margin-bottom: 22px; }
}

/* 裾の細字(/now) — 旧 /how の残りが静かに住む。読み物であって叫ばない */
.now-fine {
  margin-top: 22px; padding-top: 6px; border-top: 1px solid var(--line);
}
.now-fine summary { font-size: 12.5px; color: var(--muted); cursor: pointer; padding: 6px 0; }
.now-fine summary:hover { color: var(--ink); }
.now-fine p { font-size: 12.5px; line-height: 1.65; color: var(--muted);
  max-width: 88ch; margin: 0 0 8px; }
.now-fine strong { color: var(--muted-strong); }

/* 節の札 — 原稿の署名要素: 小さな大文字+インクの下線(PREFILLED FROM A DRAFT の型) */
.sec-label {
  font-size: 11px; font-weight: 650; letter-spacing: .14em;
  text-transform: uppercase; color: var(--muted-strong);
  border-bottom: 1px solid #10161d; padding-bottom: 6px; margin: 0 0 10px;
}

/* 頁送り — 表の下の一列 */
.pager {
  display: flex; align-items: baseline; gap: 16px;
  margin: 14px 0 0; font-size: 13.5px;
}
.pager-link { text-decoration: none; font-weight: 550; white-space: nowrap; }
.pager-link:hover { text-decoration: underline; }
.pager-page { margin-left: auto; font-size: 12.5px; color: var(--muted); }

/* ---------- 7. My Day (/day) ---------- */
.day-bar { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin: 0 0 12px; }
.day-nav { font-size: 14px; }
.day-nav strong { font-weight: 650; }
.filter-chips { display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 16px; }
.filter-chips.faces {
  display: inline-flex; gap: 0; margin: 2px 0 20px;
  border: 1px solid var(--line-hard); border-radius: 999px; overflow: hidden;
}
.filter-chips.faces .filter-chip {
  border: 0; border-radius: 0; padding: 3px 13px; font-size: 12px;
}
.filter-chips.faces .filter-chip.is-on,
.filter-chips.faces .filter-chip[aria-current="true"] {
  background: var(--ink); color: #fff; font-weight: 600;
}
.filter-chip {
  font-size: 13.5px; padding: 3.5px 14px; border-radius: 999px;
  border: 1px solid var(--line-strong); color: var(--muted); text-decoration: none;
}
.filter-chip:hover { color: var(--ink); background: var(--faint); }
.filter-chip.is-on, .filter-chip[aria-current="true"] {
  background: var(--ink); color: #fff;
  border-color: transparent; font-weight: 600;
}
.progress-band, .brief {
  padding: 10px 16px; margin: 0 0 16px; border-radius: var(--r-md); font-size: 13.5px;
  background: var(--faint); border: 1px solid var(--line);
}
.progress-band a, .brief a { color: inherit; }
.map-slot, #gmap {
  width: 100%; max-width: 680px; height: 440px;
  border: 1px solid var(--line); border-radius: var(--r-md); background: var(--faint);
}
.map-slot--placeholder {
  display: grid; place-items: center; border-style: dashed;
  color: var(--muted); font-size: 13px;
}
.route-note { font-size: 12.5px; color: var(--muted); margin: 10px 0 6px; max-width: 72ch; }
.clinician-day { margin: 28px 0 6px; }
.clinician-day__head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.clinician-day__head h3 { font-size: 15px; font-weight: 650; margin: 0; }
.clinician-day__stats { font-size: 13px; color: var(--muted); }
.stop-list { list-style: none; margin: 10px 0 8px; padding: 0; display: grid; gap: 8px; }
.stop-card {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  border: 1px solid var(--line); border-radius: var(--r-md); padding: 10px 14px;
}
.stop-card__seq {
  flex: none; width: 26px; height: 26px; border-radius: 50%;
  display: grid; place-items: center;
  background: var(--ink); color: #fff;
  font-size: 12.5px; font-weight: 650; font-variant-numeric: tabular-nums;
}
.stop-card__main { flex: 1 1 230px; min-width: 0; }
.stop-card__patient { font-weight: 600; display: block; }
.stop-card__patient a { text-decoration: none; }
.stop-card__patient a:hover { text-decoration: underline; }
.stop-card__place { font-size: 13px; color: var(--muted); display: block; margin-top: 2px; }
.stop-card__status { flex: none; }
.stop-card__leg {
  flex: none; width: 64px; text-align: right;
  font-size: 12.5px; color: var(--muted); font-variant-numeric: tabular-nums;
}
.stop-card__open { flex: none; font-size: 13.5px; }
.stop-card--next {
  border-color: color-mix(in srgb, var(--primary) 50%, transparent);
  background: color-mix(in srgb, var(--primary) 4%, #fff);
}
.stop-card--cancelled { opacity: .62; }
.stop-card--cancelled .stop-card__patient { text-decoration: line-through; }
.stop-return {
  display: flex; align-items: center; gap: 14px;
  border: 1px dashed var(--line-strong); border-radius: var(--r-md);
  padding: 8px 14px; font-size: 13.5px; color: var(--muted);
}
.stop-return .stop-card__seq {
  background: transparent; color: var(--muted);
  border: 1px dashed var(--line-strong);
}
/* 2面 — 左（地図と進み具合・貼り付く）44% / 右（回る先の列）。1100px 未満で1段 */
.day-grid {
  display: grid; grid-template-columns: minmax(0, 44fr) minmax(0, 56fr);
  gap: 28px; align-items: start;
}
.day-map { position: sticky; top: 20px; min-width: 0; }
.day-map .map-slot, .day-map #gmap, .day-map svg { max-width: none !important; }
.day-stops { min-width: 0; }
.day-stops .clinician-day:first-child { margin-top: 0; }
@media (max-width: 1100px) {
  .day-grid { display: block; }
  .day-map { position: static; }
}

/* ---------- 8. Visit (/visit) ---------- */
.visit-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 0 0 18px; }
.visit-head .page-title { margin: 0; }
.visit-head__meta { font-size: 13.5px; color: var(--muted); }
.snapshot {
  border: 1px solid var(--line); border-radius: var(--r-md);
  background: var(--faint); padding: 14px 18px; margin: 0 0 18px;
}
.snapshot__head {
  display: flex; align-items: baseline; gap: 10px;
  justify-content: space-between; flex-wrap: wrap;
}
.snapshot__title {
  font-size: 12px; font-weight: 650; letter-spacing: .07em;
  text-transform: uppercase; color: var(--muted);
}
.checklist { border: 1px solid var(--line); border-radius: var(--r-md); padding: 14px 18px; margin: 0 0 18px; }
.checklist__title { font-size: 14px; font-weight: 650; margin: 0 0 6px; }
.checklist label {
  display: flex; gap: 10px; align-items: baseline;
  padding: 3px 0; font-size: 14px; cursor: pointer;
}
.checklist__note { font-size: 12px; color: var(--muted); margin: 8px 0 0; }
.draft-panel {
  border: 1.5px dashed color-mix(in srgb, var(--warn) 55%, transparent);
  border-radius: var(--r-md); padding: 16px 18px; margin: 0 0 22px;
  background: color-mix(in srgb, var(--warn) 3%, #fff);
}
.draft-panel__head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.draft-panel__kicker {
  font-size: 13px; font-weight: 600;
  color: color-mix(in srgb, var(--warn) 70%, var(--ink));
}
.draft-panel__from { font-size: 13px; color: var(--muted); }
.draft-panel__body { user-select: text; }
.draft-panel__actions { display: flex; gap: 10px; align-items: center; margin-top: 12px; flex-wrap: wrap; }
.draft-panel--used { opacity: .65; border-color: var(--line-strong); background: var(--faint); }
.vitals { display: flex; gap: 14px; flex-wrap: wrap; margin: 0 0 22px; }
.vitals .field input { width: 110px; }
.note-editor { display: grid; gap: 20px; margin: 0 0 8px; }
.note-field > label { display: block; font-size: 14px; font-weight: 650; }
.note-field .hint { display: block; font-size: 12.5px; color: var(--muted); margin: 1px 0 7px; }
.cancel-zone {
  display: flex; justify-content: flex-end; align-items: baseline; gap: 4px;
  border-top: 1px solid var(--line); margin-top: 28px; padding: 12px 0 4px;
  font-size: 13.5px; color: var(--muted);
}
.sign-bar {
  position: sticky; bottom: 0; z-index: 10;
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  background: #fff; border-top: 1px solid var(--line-strong);
  padding: 12px 0; margin-top: 10px;
}
.sign-bar__meta { font-size: 13.5px; color: var(--muted); }
.sign-bar__actions { margin-left: auto; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.sign-bar__actions label { font-size: 13px; color: var(--muted); }

/* ---------- 9. Inbox ---------- */
.patient-chip {
  display: inline-flex; align-items: center; gap: 4px;
  font-family: var(--mono); font-size: 12px; font-weight: 600;
  padding: 1.5px 10px; border-radius: 999px; white-space: nowrap;
  border: 1px solid var(--line-strong); text-decoration: none;
}
.patient-chip:hover { background: var(--faint); }
.draft-preview {
  display: -webkit-box; -webkit-line-clamp: 6; -webkit-box-orient: vertical;
  overflow: hidden; margin: 10px 0 0;
}
.question-body { margin: 10px 0 0; white-space: pre-wrap; }
.effort { font-size: 12.5px; color: var(--muted); }
.ledger-ref { font-family: var(--mono); font-size: 12px; color: var(--muted); user-select: all; }

/* ---------- 10. Patient chart (/patient · /patients) ---------- */
.patient-head .card__title { font-size: 17px; }
.note-card {
  border: 1px solid var(--line); border-radius: var(--r-md);
  padding: 16px 18px; margin-bottom: 14px;
}
.note-card--draft {
  border-style: dashed;
  border-color: color-mix(in srgb, var(--warn) 50%, transparent);
  background: color-mix(in srgb, var(--warn) 3%, #fff);
}
.note-card--signed { border-color: var(--line); } /* 無地=正記録。印(.seal--signed)が語る */
.note-card__meta { font-size: 12.5px; color: var(--muted); }
.note-card__foot { font-size: 12.5px; color: var(--muted); margin: 10px 0 0; }
.soap dt { font-family: var(--mono); font-size: 13px; font-weight: 700; color: var(--muted); }

/* ---------- 11. Agreements · Automations ---------- */
.agreement-row--ended td { color: var(--muted); }
.form-card {
  border: 1px solid var(--line); border-radius: var(--r-md);
  padding: 18px; margin-top: 28px; max-width: 760px;
}
.form-card__title { margin: 0 0 4px; font-size: 15px; font-weight: 650; }
.form-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px; margin-top: 14px;
}
.form-actions { margin-top: 16px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

/* ---------- 12. markdown (.md) — サーバ側最小レンダラの出力 ---------- */
.md { max-width: 72ch; }
.md h4, .md h5, .md h6 { margin: 14px 0 6px; line-height: 1.4; }
.md h4 { font-size: 14.5px; }
.md h5 { font-size: 13.5px; }
.md h6 { font-size: 13px; color: var(--muted); }
.md p { margin: 8px 0; }
.md ul, .md ol { margin: 8px 0; padding-left: 22px; }
.md li { margin: 3px 0; }
.md hr { border: 0; border-top: 1px solid var(--line); margin: 12px 0; }
.md strong { font-weight: 650; }

/* ---------- 12b. guide (/guide) — 案内の会話 ----------
   問いは右寄せの吹き出し、答えは静かな札。読み幅 760px。 */
.guide { max-width: 760px; }
.guide-hint { font-size: 14px; color: var(--muted); margin: 0 0 20px; max-width: 62ch; }
.guide-turn { margin: 0 0 20px; }
.guide-q {
  width: max-content; max-width: 85%; margin: 0 0 10px auto;
  font-size: 14px; font-weight: 600;
  padding: 7px 14px; border-radius: var(--r-lg) var(--r-lg) 3px var(--r-lg);
  background: var(--faint); border: 1px solid var(--line);
}
.guide-a {
  max-width: 92%; padding: 12px 16px;
  font-size: 14px; line-height: 1.65; white-space: pre-wrap;
  border: 1px solid var(--line); border-radius: var(--r-lg) var(--r-lg) var(--r-lg) 3px;
}
.guide-form {
  position: sticky; bottom: 0; z-index: 10;
  display: flex; gap: 8px; align-items: center;
  background: #fff; border-top: 1px solid var(--line);
  padding: 12px 0; margin-top: 24px;
}
.guide-input { flex: 1 1 auto; min-width: 0; padding: 8px 12px; }

/* ---------- 12b2. ask — どの頁にも浮かぶ案内 ----------
   右下の襟(launcher)と、その場で開く札(panel)。往復は sessionStorage
   ——帳簿に書かない。JS が無ければ /guide の頁がそのまま受ける。 */
.ask-launcher {
  position: fixed; right: 22px; bottom: 22px; z-index: 40;
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 13.5px; font-weight: 600; text-decoration: none;
  padding: 9px 16px; border-radius: 999px; cursor: pointer;
  background: var(--ink); color: var(--ink-text);
  border: 1px solid var(--ink-line);
  box-shadow: 0 4px 16px rgba(16,22,29,.25);
}
.ask-launcher:hover { background: #1a232d; }
.ask-panel {
  position: fixed; right: 22px; bottom: 74px; z-index: 41;
  width: 390px; max-width: calc(100vw - 32px); max-height: 72vh;
  display: none; flex-direction: column;
  background: #fff; border: 1px solid var(--line-strong);
  border-radius: var(--r-lg); overflow: hidden;
  box-shadow: 0 8px 40px rgba(16,22,29,.28);
}
.ask-panel.is-open { display: flex; }
.ask-panel__head {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; background: var(--ink); color: var(--ink-text);
  font-size: 13px; font-weight: 600;
}
.ask-panel__head small { font-weight: 400; color: var(--ink-muted); }
.ask-panel__close {
  margin-left: auto; border: 0; background: none; color: var(--ink-muted);
  font-size: 16px; cursor: pointer; padding: 0 2px;
}
.ask-panel__close:hover { color: var(--ink-text); background: none; }
.ask-panel__log { flex: 1 1 auto; overflow-y: auto; padding: 14px 14px 4px; }
.ask-panel__log .guide-q { font-size: 13.5px; }
.ask-panel__log .guide-a { font-size: 13.5px; max-width: 100%; }
.ask-panel__log .guide-turn { margin: 0 0 14px; }
.ask-suggest { display: flex; flex-direction: column; gap: 8px; padding: 2px 0 10px; }
.ask-suggest button {
  text-align: left; font-size: 13px; padding: 7px 12px;
  border: 1px dashed var(--line-strong); border-radius: var(--r-md); background: none;
  color: var(--muted); cursor: pointer;
}
.ask-suggest button:hover { color: var(--ink); background: var(--faint); }
.ask-thinking { font-size: 12.5px; color: var(--muted); padding: 0 2px 10px; }
.ask-panel__form {
  display: flex; gap: 8px; padding: 10px 14px;
  border-top: 1px solid var(--line);
}
.ask-panel__form input { flex: 1 1 auto; min-width: 0; font-size: 13.5px; }
.ask-panel__note {
  font-size: 11px; color: var(--muted); padding: 0 14px 10px; margin: 0;
}

/* ---------- 12c. how (/how) — 説明の読みもの ---------- */
.how { max-width: 760px; }
.how p, .how li { line-height: 1.7; }
.how h2 { font-size: 15.5px; font-weight: 650; margin: 0 0 8px; }
.how-steps { margin: 10px 0; padding-left: 22px; }
.how-steps li { margin: 8px 0; }
.how-who { margin: 8px 0 0; }
.how-who td:first-child { white-space: nowrap; }
.how-who tr:last-child td { border-bottom: 0; }
.how-who tr:hover { background: none; }

/* ---------- 13. banners · refusal · empty ---------- */
.banner {
  display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap;
  border-radius: var(--r-md); padding: 10px 16px; margin: 0 0 18px;
  font-size: 14px; border: 1px solid var(--line);
}
.banner--success {
  border-color: color-mix(in srgb, var(--ok) 35%, transparent);
  background: color-mix(in srgb, var(--ok) 7%, #fff);
  color: color-mix(in srgb, var(--ok) 65%, var(--ink));
}
.refusal {
  border: 1px solid color-mix(in srgb, var(--danger) 40%, transparent);
  background: color-mix(in srgb, var(--danger) 7%, #fff);
  color: color-mix(in srgb, var(--danger) 60%, var(--ink));
  border-radius: var(--r-md);
  padding: 10px 16px; margin: 0 0 18px;
}
.empty { color: var(--muted); padding: 36px 0; font-size: 14px; max-width: 68ch; }

/* ---------- 14. focus & a11y ---------- */
:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--primary) 75%, var(--ink));
  outline-offset: 2px;
}
::selection { background: color-mix(in srgb, var(--primary) 22%, #fff); }

/* ---------- 15. narrow — 上部バーは折り返し、ナビは横に送る(何も消えない) ---------- */
@media (max-width: 900px) {
  .topbar .bar-inner { height: auto; flex-wrap: wrap; gap: 8px 12px; padding: 8px 14px; }
  .topbar__clinic { order: 5; flex: 1 1 100%; }
  .cadence, .topbar__beat { display: none; }   /* 飾りだけ畳む——機能は全部残る */
  .navbar .bar-inner { height: 44px; gap: 14px; padding: 0 14px; }
  .nav { gap: 14px; }
  .nav a { font-size: 13px; }
  .nav-ask { padding: 5px 12px; font-size: 12px; }
  .nav-quiet { display: none; }                 /* How はナビ末尾の項目として残す(下) */
  .notice-bar { padding: 6px 14px; }
  main, .page { padding: 14px 14px 48px; }
  .ask-panel { right: 8px; left: 8px; bottom: 64px; width: auto; max-height: 76vh; }
}

/* ---------- 16. print — day sheet ---------- */
@media print {
  .topbar, .navbar, .notice-bar, .filter-chips, .map-slot, #gmap, .sign-bar,
  .cancel-zone, .pager, .guide-form, .nav-ask, .ask-panel,
  button, .btn, form, .banner, .fold { display: none !important; }
  html, body { background: none; height: auto; min-height: 0; }
  .paper { border: 0; box-shadow: none; padding: 0; min-height: 0; }
  .app-shell { display: block; }
  .day-grid { display: block; }
  .day-map { position: static; }
  main, .page { max-width: none; padding: 0; }
  body { font-size: 12px; }
  a { text-decoration: none; color: #000; }
  .chip, .seal, .badge, .patient-chip, .state {
    background: none !important; color: #000 !important;
    border: 1px solid #000 !important;
  }
  .chip--cancelled, .chip--stopped { text-decoration: line-through !important; }
  .stop-card, .note-card, .card, .row { break-inside: avoid; border-color: #999; }
  .stop-card--next { background: none; }
  .clinician-day { break-after: page; }
  .clinician-day:last-of-type { break-after: auto; }
}

"""

#: CARE（現場）が先、BACK OFFICE（監督）が後——2ペルソナのナビ。
_画面 = ("day", "patients", "inbox", "agreements", "billing", "automations",
        "ledger")  # ledger = activity と search の2面。fees は billing 内・how は棚の最下段・guide は襟

#: 書く欄の見出し。**用語集の語ではない**——押すときの手がかりなので、そのまま英語で置く。
