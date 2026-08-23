# --- 見せかた。ここから下は「入っているものを出す」だけ ---

_STYLE = """
/* ================================================================
   Troupe — style.css  ·  design “clinical calm”
   ui/web.py の _STYLE を丸ごと置き換える1枚。
   外部アセットなし・システムフォントのみ・JSはGoogle Maps スロットだけ。
   ライト/ダーク: color-scheme + Canvas/CanvasText + color-mix（現行方式踏襲）。

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
  color-scheme: light dark;

  /* 状態の色相 — UI に存在する有彩色はこの5つだけ */
  --ok:      #15803d;
  --warn:    #b45309;
  --danger:  #b91c1c;
  --info:    #2563eb;
  --primary: #1f5f9e;   /* 唯一の塗りつぶし: Sign / Approve / Reply */

  /* 無彩色はすべて Canvas/CanvasText から導出（両テーマ自動対応） */
  --line:        color-mix(in srgb, CanvasText 14%, transparent);
  --line-strong: color-mix(in srgb, CanvasText 30%, transparent);
  --muted:       color-mix(in srgb, CanvasText 75%, Canvas); /* 二次テキストは75%が下限 */
  --faint:       color-mix(in srgb, CanvasText 4%, Canvas);  /* うっすらした地 */
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font: 14.5px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, "Hiragino Sans", "Noto Sans JP", sans-serif;
  background: Canvas; color: CanvasText;
  -webkit-text-size-adjust: 100%;
}

/* ---------- 1. shell — sidebar / nav / page ----------
   骨組み:  .app-shell > .app-header（左の縦ナビ・幅216px固定）
                       + .app-content（.notice-bar → main）
   900px 未満は §15 で上のバーに畳む。 */
.app-shell { display: flex; align-items: stretch; min-height: 100vh; }
.app-header {
  flex: none; width: 216px;
  display: flex; flex-direction: column;
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  padding: 16px 12px 14px;
  border-right: 1px solid var(--line);
  background: color-mix(in srgb, CanvasText 2.5%, Canvas);
}
.brand {
  display: block; font-size: 15.5px; font-weight: 700; letter-spacing: .01em;
  padding: 2px 10px 13px; margin: 0 0 4px;
  border-bottom: 1px solid var(--line);
}
.nav { display: flex; flex-direction: column; gap: 1px; }
.nav__label {
  display: block; font-size: 10.5px; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--muted);
  margin: 18px 10px 4px; user-select: none;
}
.nav > .nav__label:first-child { margin-top: 8px; }
/* 縦組では見出し前の余白が区切り。横組（§15）で線として復活 */
.nav__sep { display: none; width: 1px; height: 16px; background: var(--line-strong); }
.nav a {
  display: block; text-decoration: none; color: var(--muted);
  font-size: 13.5px; padding: 5.5px 10px; border-radius: 7px;
}
.nav a:hover { color: CanvasText; background: color-mix(in srgb, CanvasText 6%, Canvas); }
.nav a[aria-current="page"], .nav a.is-active {
  color: CanvasText; font-weight: 600;
  background: color-mix(in srgb, CanvasText 8%, Canvas);
  box-shadow: inset 2px 0 0 0 CanvasText;
}
.whoami {
  margin-top: auto; padding: 12px 10px 2px; border-top: 1px solid var(--line);
  font-size: 12px; color: var(--muted); line-height: 1.5;
}
.whoami strong { display: block; color: CanvasText; font-weight: 600; font-size: 12.5px; }

.app-content { flex: 1 1 auto; min-width: 0; }
/* 開示バー — 合成の座長が動いているあいだの、細い琥珀の帯 */
.notice-bar {
  font-size: 12.5px; line-height: 1.5; padding: 6px 36px;
  color: color-mix(in srgb, var(--warn) 72%, CanvasText);
  background: color-mix(in srgb, var(--warn) 8%, Canvas);
  border-bottom: 1px solid color-mix(in srgb, var(--warn) 26%, transparent);
}

main, .page { width: 100%; max-width: 1480px; margin: 0; padding: 26px 36px 56px; }
.page-title { font-size: 20px; font-weight: 650; letter-spacing: -.01em; margin: 0 0 4px; }
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
  border: 1px solid var(--line); border-radius: 10px;
  padding: 16px 18px; margin-bottom: 14px; background: Canvas;
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
.fold > summary:hover { color: CanvasText; }
.fold[open] > summary { margin-bottom: 6px; }

/* ---------- 4. chips · badges · seals ----------
   chip  = 状態。色を持つ唯一の常連。記号は HTML の文字で: “Signed ✓” “⚠ Needs your answer”
   badge = 種類（Visit note / Weekly report / Request / Task）。常に無彩色の枠。
   seal  = 記録の印（DRAFT / SIGNED / USED）。カルテと下書きパネルの見出しに捺す。 */
.chip {
  --c: CanvasText;
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600; line-height: 1.5;
  padding: 1.5px 9px; border-radius: 999px; white-space: nowrap;
  color: color-mix(in srgb, var(--c) 70%, CanvasText);
  background: color-mix(in srgb, var(--c) 9%, Canvas);
  border: 1px solid color-mix(in srgb, var(--c) 32%, transparent);
}
a.chip { text-decoration: none; }
a.chip:hover { border-color: color-mix(in srgb, var(--c) 60%, transparent); }
/* 状態 → 色。この対応が正本 */
.chip--signed, .chip--approved, .chip--done      { --c: var(--ok); }
.chip--draft-ready, .chip--working               { --c: var(--info); }
.chip--needs-approval, .chip--needs-answer,
.chip--expiring                                  { --c: var(--warn); }
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
  color: color-mix(in srgb, var(--warn) 70%, CanvasText);
  background: color-mix(in srgb, var(--warn) 13%, Canvas);
}
.seal--signed, .state-final {
  color: color-mix(in srgb, var(--ok) 70%, CanvasText);
  background: color-mix(in srgb, var(--ok) 12%, Canvas);
}
.seal--used { color: var(--muted); background: var(--faint); }
/* 旧 .state 互換 — 無彩チップとして残す */
.state {
  font-size: 12px; padding: 1.5px 9px; border-radius: 999px;
  background: color-mix(in srgb, CanvasText 9%, Canvas);
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
  background: color-mix(in srgb, CanvasText 35%, Canvas);
}
.who--human .who-dot { background: var(--ok); }
.who--agent .who-dot { background: #7c3aed; }
.who--clock .who-dot { background: color-mix(in srgb, CanvasText 40%, Canvas); }

/* ---------- 5. buttons & forms ----------
   3階層:  primary(塗り) = Sign / Approve / Reply だけ
           secondary(枠) = 既定。それ以外の操作すべて
           destructive(赤テキスト) = 取り消し系。2段階目は .is-confirm を付ける */
button, .btn {
  font: inherit; font-size: 14px; font-weight: 500;
  padding: 6px 16px; border-radius: 8px; cursor: pointer;
  border: 1px solid var(--line-strong); background: Canvas; color: inherit;
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
  color: color-mix(in srgb, var(--danger) 72%, CanvasText);
}
.btn--destructive:hover { background: none; text-decoration: underline; }
.btn--destructive.is-confirm {
  border-color: color-mix(in srgb, var(--danger) 55%, transparent);
  background: color-mix(in srgb, var(--danger) 9%, Canvas);
  padding: 6px 14px; text-decoration: none; font-weight: 600;
}
.btn--destructive.is-confirm:hover {
  background: color-mix(in srgb, var(--danger) 14%, Canvas);
}
.confirm-note { font-size: 12.5px; color: color-mix(in srgb, var(--danger) 70%, CanvasText); }
input[type=text], input[type=date], input[type=number], select, textarea {
  font: inherit; padding: 6px 10px; border-radius: 8px;
  border: 1px solid var(--line-strong); background: Canvas; color: inherit;
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
td {
  padding: 9px 12px; border-bottom: 1px solid var(--line);
  vertical-align: top; font-variant-numeric: tabular-nums;
}
tbody tr:hover { background: var(--faint); }
.cell-danger { color: color-mix(in srgb, var(--danger) 75%, CanvasText); font-weight: 600; }
.cell-when {
  font-family: var(--mono); font-size: 11.5px; color: var(--muted);
  white-space: nowrap;
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
.filter-chip {
  font-size: 13.5px; padding: 3.5px 14px; border-radius: 999px;
  border: 1px solid var(--line-strong); color: var(--muted); text-decoration: none;
}
.filter-chip:hover { color: CanvasText; background: var(--faint); }
.filter-chip.is-on, .filter-chip[aria-current="true"] {
  background: color-mix(in srgb, CanvasText 88%, Canvas); color: Canvas;
  border-color: transparent; font-weight: 600;
}
.progress-band, .brief {
  padding: 10px 16px; margin: 0 0 16px; border-radius: 10px; font-size: 13.5px;
  background: var(--faint); border: 1px solid var(--line);
}
.progress-band a, .brief a { color: inherit; }
.map-slot, #gmap {
  width: 100%; max-width: 680px; height: 440px;
  border: 1px solid var(--line); border-radius: 10px; background: var(--faint);
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
  border: 1px solid var(--line); border-radius: 10px; padding: 10px 14px;
}
.stop-card__seq {
  flex: none; width: 26px; height: 26px; border-radius: 50%;
  display: grid; place-items: center;
  background: color-mix(in srgb, CanvasText 85%, Canvas); color: Canvas;
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
  background: color-mix(in srgb, var(--primary) 4%, Canvas);
}
.stop-card--cancelled { opacity: .62; }
.stop-card--cancelled .stop-card__patient { text-decoration: line-through; }
.stop-return {
  display: flex; align-items: center; gap: 14px;
  border: 1px dashed var(--line-strong); border-radius: 10px;
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
  border: 1px solid var(--line); border-radius: 10px;
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
.checklist { border: 1px solid var(--line); border-radius: 10px; padding: 14px 18px; margin: 0 0 18px; }
.checklist__title { font-size: 14px; font-weight: 650; margin: 0 0 6px; }
.checklist label {
  display: flex; gap: 10px; align-items: baseline;
  padding: 3px 0; font-size: 14px; cursor: pointer;
}
.checklist__note { font-size: 12px; color: var(--muted); margin: 8px 0 0; }
.draft-panel {
  border: 1.5px dashed color-mix(in srgb, var(--warn) 55%, transparent);
  border-radius: 10px; padding: 16px 18px; margin: 0 0 22px;
  background: color-mix(in srgb, var(--warn) 3%, Canvas);
}
.draft-panel__head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.draft-panel__kicker {
  font-size: 13px; font-weight: 600;
  color: color-mix(in srgb, var(--warn) 70%, CanvasText);
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
  background: Canvas; border-top: 1px solid var(--line-strong);
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
  border: 1px solid var(--line); border-radius: 10px;
  padding: 16px 18px; margin-bottom: 14px;
}
.note-card--draft {
  border-style: dashed;
  border-color: color-mix(in srgb, var(--warn) 50%, transparent);
  background: color-mix(in srgb, var(--warn) 3%, Canvas);
}
.note-card--signed { border-color: var(--line); } /* 無地=正記録。印(.seal--signed)が語る */
.note-card__meta { font-size: 12.5px; color: var(--muted); }
.note-card__foot { font-size: 12.5px; color: var(--muted); margin: 10px 0 0; }
.soap dt { font-family: var(--mono); font-size: 13px; font-weight: 700; color: var(--muted); }

/* ---------- 11. Agreements · Automations ---------- */
.agreement-row--ended td { color: var(--muted); }
.form-card {
  border: 1px solid var(--line); border-radius: 10px;
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
  padding: 7px 14px; border-radius: 12px 12px 3px 12px;
  background: var(--faint); border: 1px solid var(--line);
}
.guide-a {
  max-width: 92%; padding: 12px 16px;
  font-size: 14px; line-height: 1.65; white-space: pre-wrap;
  border: 1px solid var(--line); border-radius: 12px 12px 12px 3px;
}
.guide-form {
  position: sticky; bottom: 0; z-index: 10;
  display: flex; gap: 8px; align-items: center;
  background: Canvas; border-top: 1px solid var(--line);
  padding: 12px 0; margin-top: 24px;
}
.guide-input { flex: 1 1 auto; min-width: 0; padding: 8px 12px; }

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
  border-radius: 10px; padding: 10px 16px; margin: 0 0 18px;
  font-size: 14px; border: 1px solid var(--line);
}
.banner--success {
  border-color: color-mix(in srgb, var(--ok) 35%, transparent);
  background: color-mix(in srgb, var(--ok) 7%, Canvas);
  color: color-mix(in srgb, var(--ok) 65%, CanvasText);
}
.refusal {
  border-left: 3px solid var(--danger);
  background: color-mix(in srgb, var(--danger) 7%, Canvas);
  border-radius: 0 10px 10px 0;
  padding: 10px 16px; margin: 0 0 18px;
}
.empty { color: var(--muted); padding: 36px 0; font-size: 14px; max-width: 68ch; }

/* ---------- 14. focus & a11y ---------- */
:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--primary) 75%, CanvasText);
  outline-offset: 2px;
}
::selection { background: color-mix(in srgb, var(--primary) 22%, Canvas); }

/* ---------- 15. narrow — 900px 未満は上の小さなバー ---------- */
@media (max-width: 900px) {
  .app-shell { display: block; }
  .app-header {
    width: auto; height: auto; overflow: visible; z-index: 30;
    flex-direction: row; align-items: center; gap: 12px;
    padding: 8px 14px; border-right: 0; border-bottom: 1px solid var(--line);
  }
  .brand { padding: 0; margin: 0; border-bottom: 0; font-size: 15px; }
  .nav {
    flex-direction: row; align-items: center; gap: 2px;
    flex: 1 1 auto; min-width: 0;
    overflow-x: auto; -webkit-overflow-scrolling: touch;
  }
  .nav__label { margin: 0 4px 0 8px; }
  .nav > .nav__label:first-child { margin: 0 4px 0 0; }
  .nav__sep { display: block; flex: none; margin: 0 6px; align-self: center; }
  .nav a { white-space: nowrap; font-size: 13px; padding: 5px 9px; }
  .nav a[aria-current="page"], .nav a.is-active {
    background: none; box-shadow: inset 0 -2px 0 0 CanvasText; border-radius: 0;
  }
  .whoami { display: none; }
  .notice-bar { padding: 6px 16px; }
  main, .page { padding: 18px 16px 48px; }
}

/* ---------- 16. print — day sheet ---------- */
@media print {
  .app-header, .notice-bar, .filter-chips, .map-slot, #gmap, .sign-bar,
  .cancel-zone, .pager, .guide-form,
  button, .btn, form, .banner, .fold { display: none !important; }
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
_画面 = ("day", "patients", "inbox", "agreements", "automations", "activity", "search")

#: 書く欄の見出し。**用語集の語ではない**——押すときの手がかりなので、そのまま英語で置く。
