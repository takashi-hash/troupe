"""窓の枠（web）— 画面を挟む、もう1つの器。

設計: 設計/人に見えるもの.md §1・どう作るか §5
「器（`shell`＝机の窓・`web`＝web の窓。**どちらも脈を持たない**）」。

**脈を持たない。** 常駐は配線のまま——窓を閉じても一座は回る。
画面は常に導出——開いた瞬間の帳簿を見る（「更新」は開き直しと同じ）。

**手は1回ごとに開いて、閉じる。** 帳簿への接続は器が跨いで持たない
——プロセスが何も覚えないのと同じ理由で、リクエストも何も覚えない。
だから同じ器を何本立てても、どれが死んでも壊れない。

**PySide6 を読み込まない。** 机の窓と web の窓は同じ手を受け取るが、
互いを知らない——クラウドの器に画面の道具を載せないため。

**出すのは用語集の識別子の欄**（人に見えるもの §5）——机の窓が語の欄を出すのに対して、
web の窓は識別子の欄を出す。**訳はここで作らない**——橋に無い語は出せない（`語` が落ちる）。
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape
from urllib.parse import quote
from typing import Any, NamedTuple, Protocol

from app.dto.detail_view import DetailView
from app.dto.history_row import HistoryRow
from app.dto.row_filter import RowFilter
from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from app.dto.patient_row import PatientRow
from app.dto.pattern_row import PatternRow
from app.dto.visit_view import VisitView
from app.services.screen.gather_route import _km
from app.dto.route_stop import RouteStop
from app.dto.patient_view import PatientView
from app.dto.today_row import TodayRow
from ui.words import 出来事, 操作, 状態, 語, 起こす者, 読める


class 読む手(Protocol):
    def __call__(self) -> tuple[TodayRow, ...]: ...


class 押す手(Protocol):
    def __call__(self, what: str, id: str, text: str) -> str | None:
        """通れば None、断られたら理由の文字。"""
        ...


class 詳細の手(Protocol):
    def __call__(self, id: str) -> DetailView | None: ...


class 予定の手(Protocol):
    def __call__(self) -> tuple[ScheduleRow, ...]: ...


class 決まりを押す手(Protocol):
    def __call__(
        self, what: str, name: str, version: int, fields: dict[str, str]
    ) -> str | None: ...


class 履歴の手(Protocol):
    def __call__(self) -> tuple[HistoryRow, ...]: ...


class 検索の手(Protocol):
    def __call__(self, filter: RowFilter) -> tuple[SearchRow, ...]: ...


class 頼む手(Protocol):
    def __call__(self, body: str, fields: dict[str, str]) -> str | None: ...


class 来ている仕事の手(Protocol):
    def __call__(self) -> tuple[SearchRow, ...]: ...


class 患者たちの手(Protocol):
    def __call__(self) -> tuple[PatientRow, ...]: ...


class 患者の手(Protocol):
    def __call__(self, code: str) -> PatientView | None: ...


class 取り決めの手(Protocol):
    def __call__(self) -> tuple[PatternRow, ...]: ...


class 取り決めを押す手(Protocol):
    def __call__(self, what: str, fields: dict[str, str]) -> str | None: ...


class 今日の手(Protocol):
    def __call__(self) -> str: ...


class 訪問の手(Protocol):
    def __call__(self, id: str) -> VisitView | None: ...


class 訪問を押す手(Protocol):
    def __call__(self, what: str, fields: dict[str, str]) -> str | None: ...


class 道順の手(Protocol):
    def __call__(
        self, day: str
    ) -> tuple[tuple[float, float] | None, dict[str, tuple[RouteStop, ...]]]: ...


class 手(NamedTuple):
    """器に注がれる手。**中身は知らない**——読む・押す、それだけ。

    机の窓は同じ手を1つずつ受け取る。web は1回ごとに束で受け取り、
    使い終わったら `close` で閉じる。

    **欄の名は机の窓の口と同じ**——同じ手が、どちらの器にも注げる。
    （形をここに写すのは、web の器が机の道具を読み込まないため。
    ずれたら組み立ての根が型で赤くなる——注ぐのは main.py だけだから。）
    """

    fetch: 読む手
    act: 押す手
    detail: 詳細の手
    schedule_fetch: 予定の手
    schedule_act: 決まりを押す手
    history_fetch: 履歴の手
    search: 検索の手
    request: 頼む手
    upcoming: 来ている仕事の手
    patients: 患者たちの手
    patient: 患者の手
    patterns: 取り決めの手
    pattern_act: 取り決めを押す手
    visit: 訪問の手
    visit_act: 訪問を押す手
    route: 道順の手
    today: 今日の手
    close: Callable[[], None]


class 手を開く(Protocol):
    def __call__(self) -> 手:
        """帳簿を開き、手の束を組んで返す。**呼ばれるたびに新しい。**"""
        ...


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
     0. tokens & reset        8. Visit (/visit)
     1. shell（header/nav/page） 9. Inbox
     2. text & links         10. Patient chart
     3. cards & folds        11. Agreements · Automations
     4. chips·badges·seals   12. markdown (.md)
     5. buttons & forms      13. banners · refusal · empty
     6. tables               14. focus & a11y
     7. My Day (/day)        15. print（day sheet）
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
  font: 15px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, "Hiragino Sans", "Noto Sans JP", sans-serif;
  background: Canvas; color: CanvasText;
  -webkit-text-size-adjust: 100%;
}

/* ---------- 1. shell — header / nav / page ---------- */
.app-header {
  display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
  padding: 12px 28px;
  border-bottom: 1px solid var(--line);
}
.brand { font-size: 16px; font-weight: 700; letter-spacing: .01em; }
.nav { display: flex; align-items: center; gap: 2px; flex-wrap: wrap; }
.nav__label {
  font-size: 10.5px; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--muted);
  margin: 0 6px 0 2px; user-select: none;
}
.nav__sep { width: 1px; height: 18px; background: var(--line-strong); margin: 0 12px; }
.nav a {
  text-decoration: none; color: var(--muted);
  font-size: 14px; padding: 6px 10px; border-radius: 7px;
}
.nav a:hover { color: CanvasText; background: var(--faint); }
.nav a[aria-current="page"], .nav a.is-active {
  color: CanvasText; font-weight: 600;
  box-shadow: inset 0 -2px 0 0 CanvasText;
  border-radius: 7px 7px 0 0; background: none;
}
.whoami { margin-left: auto; font-size: 13px; color: var(--muted); }
.whoami strong { color: CanvasText; font-weight: 600; }

main, .page { max-width: 960px; margin: 0 auto; padding: 26px 28px 48px; }
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

/* ---------- 6. tables ---------- */
.wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th {
  text-align: left; font-size: 11.5px; font-weight: 600;
  letter-spacing: .07em; text-transform: uppercase; color: var(--muted);
  padding: 8px 10px; border-bottom: 1px solid var(--line-strong);
}
td {
  padding: 9px 10px; border-bottom: 1px solid var(--line);
  vertical-align: top; font-variant-numeric: tabular-nums;
}
tbody tr:hover { background: var(--faint); }
.cell-danger { color: color-mix(in srgb, var(--danger) 75%, CanvasText); font-weight: 600; }

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
.stop-card__patient { font-weight: 600; }
.stop-card__patient a { text-decoration: none; }
.stop-card__patient a:hover { text-decoration: underline; }
.stop-card__place { font-size: 13px; color: var(--muted); }
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
.empty { color: var(--muted); padding: 36px 0; }

/* ---------- 14. focus & a11y ---------- */
:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--primary) 75%, CanvasText);
  outline-offset: 2px;
}
::selection { background: color-mix(in srgb, var(--primary) 22%, Canvas); }

/* ---------- 15. print — day sheet ---------- */
@media print {
  .app-header, .filter-chips, .map-slot, #gmap, .sign-bar, .cancel-zone,
  button, .btn, form, .banner, .fold { display: none !important; }
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
_書く欄 = {"answer": "Answer", "send_back": "Reason", "abandon": "Reason"}


def _頁(見出し: str, 中身: str, viewer: str, 断り: str | None = None) -> str:
    """窓の枠。**押しつけは今日だけ**——残りは引き出し（人に見えるもの §1）。"""
    def _tab(識別子: str) -> str:
        現在 = " aria-current='page'" if 識別子 == 見出し else ""
        return f"<a href='/{識別子}'{現在}>{escape(読める(識別子))}</a>"

    tabs = (
        "<span class='nav__label'>Care</span>"
        + "".join(_tab(t) for t in ("day", "patients"))
        + "<span class='nav__sep' role='separator'></span>"
        + "<span class='nav__label'>Back office</span>"
        + "".join(_tab(t) for t in ("inbox", "agreements", "automations", "activity", "search"))
    )
    警告 = f'<div class="refusal">{escape(断り)}</div>' if 断り else ""
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Troupe — {escape(読める(見出し))}</title><style>{_STYLE}</style></head><body>"
        f"<header class='app-header'><span class='brand'>Troupe</span>"
        f"<nav class='nav' aria-label='Primary'>{tabs}</nav>"
        f"<span class='whoami'>Signed in as: <strong>{escape(viewer)}</strong></span></header>"
        f"<main>{警告}{中身}</main></body></html>"
    )


def _欄(組: list[tuple[str, str | None]]) -> str:
    """欄を並べる。**本文はそのまま載せる——縮めない**（人に見えるもの §2）。"""
    行 = "".join(
        f"<dt>{escape(名)}</dt><dd>{escape(値)}</dd>" for 名, 値 in 組 if 値
    )
    return f"<dl>{行}</dl>" if 行 else ""


def _押せること(押せる: tuple[str, ...], job_id: str, 戻り: str) -> str:
    """押せることを並べる。**組むのは domain の仕様**——ここは入っているものを出すだけ。"""
    階層 = {"approve": "btn btn--primary", "answer": "btn btn--primary",
            "abandon": "btn btn--destructive"}
    語感 = {"approve": "Approve", "answer": "Reply", "send_back": "Send back",
            "abandon": "Abandon"}
    out = []
    for what in 押せる:
        名 = 語感.get(what, 操作(what))
        欄 = _書く欄.get(what)
        書く = (
            f"<input type='text' name='text' aria-label='{escape(欄)}'"
            f" placeholder='{escape(欄)}' required>"
            if 欄
            else ""
        )
        確認 = (" onclick=\"return confirm('Abandon this job? This is final.')\""
                if what == "abandon" else "")
        out.append(
            f"<form class='act' method='post' action='/act'>"
            f"<input type='hidden' name='what' value='{escape(what)}'>"
            f"<input type='hidden' name='id' value='{escape(job_id)}'>"
            f"<input type='hidden' name='back' value='{escape(戻り)}'>"
            f"{書く}<button class='{階層.get(what, 'btn')}'{確認}>{escape(名)}</button></form>"
        )
    return "".join(out)


def _状態(名: str) -> str:
    return f"<span class='state'>{escape(状態(名))}</span>"


def _帯(rows: tuple[TodayRow, ...], in_flight: int) -> str:
    """ブリーフィングの帯 — 件数と行き先だけ。**行は足さない。**

    人に見えるもの §4「先の予定は今日に載せない（赤が埋もれる）」——
    だからここに出すのは数と道案内であって、押しつけの行ではない。
    数は下に並んでいる行の集計そのもの（別の判定を持たない）。
    """
    from ui.words import STATE_GLOSS

    def 数える(ident: str) -> int:
        return sum(1 for r in rows if STATE_GLOSS.get(r.state_name) == ident)

    承認 = 数える("AwaitingApproval")
    回答 = 数える("AwaitingAnswer")
    組 = [
        f"<strong>{承認}</strong> awaiting your approval",
        f"<strong>{回答}</strong> awaiting an answer",
        f"<strong>{in_flight}</strong> job{'s' if in_flight != 1 else ''} in flight"
        " — <a href='/automations'>automations</a>",
    ]
    return f"<div class='brief'>{' · '.join(組)}</div>"


def _参照名(r: TodayRow) -> tuple[str, str, str | None]:
    """（種類バッジ, 人間参照名, 患者記号）——UUIDの代わりに人が呼べる名。"""
    if r.rule and r.rule.startswith("Visit Note Draft"):
        code = r.rule.rsplit("— ", 1)[-1].strip()
        return "Visit note", f"{code} · Visit note · {r.period or ''}".strip(), code
    if r.rule:
        return "Report", f"{r.rule} · {r.period or ''}".strip(), None
    return "Request", (r.request_head or "Request"), None


def _今日(rows: tuple[TodayRow, ...]) -> str:
    if not rows:
        return "<p class='empty'>Nothing needs your judgment today.</p>"
    out = []
    for r in rows:
        badge, 参照, code = _参照名(r)
        chip = ("<span class='chip chip--needs-answer'>⚠ Needs your answer</span>"
                if "answer" in r.actions else
                "<span class='chip chip--needs-approval'>Needs your approval</span>"
                if "approve" in r.actions else
                f"<span class='chip'>{escape(状態(r.state_name))}</span>")
        患者 = (f"<a class='patient-chip' href='/patient?code={quote(code)}'>{escape(code)} →</a>"
                if code else "")
        中身 = ""
        if r.question_body:
            中身 = f"<p class='question-body'>{escape(r.question_body)}</p>"
            if r.answer_body:
                中身 += f"<dl><dt>Answer</dt><dd>{escape(r.answer_body)}</dd></dl>"
        elif r.result_body:
            中身 = (f"<div class='draft-preview md'>{_md(r.result_body)}</div>"
                    f"<details class='fold'><summary>Show full draft</summary>"
                    f"<div class='md'>{_md(r.result_body)}</div></details>")
        見立て = "\n".join(f"{本文}（{理由}）" for 本文, 理由 in r.assessments)
        詳細 = (
            "<details class='fold'><summary>Details</summary><dl>"
            f"<dt>Brief</dt><dd>{escape(r.instruction)}</dd>"
            + (f"<dt>Source quoted</dt><dd>{escape(r.evidence_quote)}</dd>" if r.evidence_quote else "")
            + (f"<dt>Assessment</dt><dd>{escape(見立て)}</dd>" if 見立て else "")
            + (f"<dt>Recheck</dt><dd>{escape(r.recheck_at)}</dd>" if r.recheck_at else "")
            + f"<dt>AI effort</dt><dd><span class='effort'>{r.spent_calls} of {r.budget_calls}"
            f" calls · {r.spent_seconds} of {r.budget_seconds} s</span></dd>"
            f"<dt>Ledger ref</dt><dd><span class='ledger-ref'>{escape(r.id)}</span>"
            f" · <a class='link-action' href='/detail?id={quote(r.id)}'>Full history →</a></dd>"
            "</dl></details>"
        )
        操作 = _押せること(r.actions, r.id, "/inbox")
        out.append(
            f"<article class='card'><div class='card__head'>"
            f"<span class='badge'>{badge}</span>"
            f"<span class='ref-name'>{escape(参照)}</span>{chip}"
            f"<span class='push sub'>due {escape(r.due)}</span></div>"
            + 患者 + 中身 + 詳細
            + f"<div class='card-actions'>{操作}</div></article>"
        )
    return "".join(out)


def _詳細(view: DetailView | None) -> str:
    if view is None:
        return "<p class='empty'>No such job.</p>"
    問答 = "\n".join(f"Q: {q}\nA: {a or '(not yet)'}" for q, a in view.questions)
    見立て = "\n".join(f"{本文}（{理由}）" for 本文, 理由 in view.assessments)
    出来事の列 = "".join(
        f"<tr><td>{escape(e.at)}</td><td>{escape(起こす者(e.by))}</td><td>{escape(出来事(e.what))}</td></tr>"
        for e in view.events
    )
    return (
        f"<div class='row'><div class='head'>"
        f"<span class='title'>{escape(view.instruction)}</span>{_状態(view.state_name)}"
        f"<span class='id'>{escape(view.id)}</span></div>"
        + _欄(
            [
                (語("期日"), view.due),
                (語("担当"), view.assignee_name),
                (語("成果"), view.result_body),
                (語("根拠"), view.evidence_quote),
                (語("確かめ期日"), view.recheck_at),
                (f'{語("質問")} / {語("回答")}', 問答),
                (語("見立て"), 見立て),
            ]
        )
        + _押せること(view.actions, view.id, f"/detail?id={view.id}")
        + "</div>"
        + "<div class='wrap'><table><tr><th>When</th><th>Who</th><th>What happened</th></tr>"
        + 出来事の列
        + "</table></div>"
    )


def _予定(rules: tuple[ScheduleRow, ...], jobs: tuple[SearchRow, ...]) -> str:
    決まり = "".join(
        f"<tr><td>{escape(r.rule)}</td><td>{escape(r.instruction)}</td>"
        f"<td>{r.version}</td><td>{r.active_version if r.active_version else '—'}</td>"
        # 次の対象期間だけを出す。**その期間の仕事が在るかは、すぐ下の表が示す**
        # ——同じことを2箇所で言わない（言い換えを画面で作らない）
        f"<td>{escape((r.next_period or '—').split('（')[0])}</td></tr>"
        for r in rules
    )
    仕事 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(j.id)}'>{escape(j.id)}</a></td>"
        f"<td>{escape(j.head)}</td><td>{escape(j.period or '')}</td>"
        f"<td>{_状態(j.state_name)}</td><td>{escape(j.due)}</td></tr>"
        for j in jobs
    )
    return (
        f"<h3>{語('業務ルール')}</h3><div class='wrap'><table>"
        "<tr><th>Rule</th><th>Instruction</th><th>Version</th><th>Active version</th>"
        "<th>Next period</th></tr>" + 決まり + "</table></div>"
        "<h3>Jobs in flight</h3><div class='wrap'><table>"
        "<tr><th>Id</th><th>Title</th><th>Period</th><th>State</th><th>Due date</th></tr>"
        + 仕事
        + "</table></div>"
    )


def _履歴(rows: tuple[HistoryRow, ...]) -> str:
    行 = "".join(
        f"<tr><td>{escape(r.at)}</td><td>{escape(起こす者(r.by))}</td><td>{escape(出来事(r.what))}</td>"
        f"<td><a class='id' href='/detail?id={escape(r.job_id)}'>{escape(r.head)}</a></td></tr>"
        for r in rows
    )
    return (
        "<div class='wrap'><table><tr><th>When</th><th>Who</th><th>What happened</th>"
        "<th>Job</th></tr>" + 行 + "</table></div>"
    )


def _検索(rows: tuple[SearchRow, ...], keyword: str) -> str:
    行 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(r.id)}'>{escape(r.id)}</a></td>"
        f"<td>{escape(r.head)}</td><td>{escape(r.period or '')}</td>"
        f"<td>{_状態(r.state_name)}</td><td>{escape(r.due)}</td>"
        f"<td>{escape(r.assignee_name or '')}</td></tr>"
        for r in rows
    )
    return (
        "<form method='get' action='/search'>"
        f"<input type='text' name='keyword' value='{escape(keyword)}' "
        "placeholder='keyword'> <button>Search</button></form>"
        "<div class='wrap'><table><tr><th>Id</th><th>Title</th><th>Period</th>"
        "<th>State</th><th>Due date</th><th>Assignee</th></tr>" + 行 + "</table></div>"
    )


def _患者たち(rows: tuple[PatientRow, ...], today: str = "") -> str:
    """患者の一覧 — 診療録の写し。**よその語のまま並べる**（翻訳しない）。"""
    if not rows:
        return (
            "<p class='empty'>The agency EMR is not wired (ICHIZA_EMR_DSN), "
            "or holds no patients.</p>"
        )
    def _期限(r: PatientRow) -> str:
        if not r.order_expires:
            return "<td>—</td>"
        if today and r.order_expires < today:
            return (f"<td class='cell-danger'><span class='chip chip--expired'>"
                    f"Expired {escape(r.order_expires)}</span></td>")
        return f"<td>{escape(r.order_expires)}</td>"

    行 = "".join(
        f"<tr><td><a class='patient-chip' href='/patient?code={quote(r.code)}'>{escape(r.code)}</a></td>"
        f"<td>{escape(r.age)}</td><td>{escape(r.diagnosis)}</td>"
        f"<td>{escape(r.living)}</td><td>{escape(r.next_visit or '—')}</td>"
        + _期限(r) + "</tr>"
        for r in rows
    )
    return (
        "<p class='sub'>Read-only mirror of the agency EMR — synthetic data, no real patient exists. "
        "Troupe never writes here.</p>"
        "<div class='wrap'><table><tr><th>Code</th><th>Age</th><th>Diagnosis</th>"
        "<th>Living</th><th>Next visit</th><th>Order expires</th></tr>" + 行 + "</table></div>"
    )


def _患者(view: PatientView | None) -> str:
    if view is None:
        return "<p class='empty'>No such patient.</p>"
    下書き = "".join(
        f"<article class='card note-card note-card--draft{' draft-panel--used' if d.used else ''}'>"
        f"<div class='card__head'>"
        f"<span class='seal {'seal--used' if d.used else 'seal--draft'}'>{'USED' if d.used else 'DRAFT'}</span>"
        f"<span class='note-card__meta'>delivered {escape(d.delivered_at[:16])}"
        f" · <a class='link-action' href='/detail?id={quote(d.job_id)}'>AI history →</a></span></div>"
        f"<div class='md'>{_md(d.body)}</div>"
        "<p class='note-card__foot sub'>A proposal from Troupe. A doctor rewrites and signs —"
        " this never becomes the record by itself.</p></article>"
        for d in view.drafts
    )
    記録 = "".join(
        f"<article class='card note-card note-card--signed'><div class='card__head'>"
        f"<span class='seal seal--signed'>SIGNED</span>"
        f"<span class='card__title'>Note {escape(n.at)}</span>"
        f"<span class='note-card__meta push'>{escape(n.clinician)} · signed {escape(n.signed_at[:16])}</span></div>"
        f"<dl class='soap'><dt>S</dt><dd>{escape(n.s)}</dd><dt>O</dt><dd>{escape(n.o)}</dd>"
        f"<dt>A</dt><dd>{escape(n.a)}</dd><dt>P</dt><dd>{escape(n.p)}</dd></dl></article>"
        for n in view.notes
    )
    return (
        f"<div class='row'><div class='head'>"
        f"<span class='title'>{escape(view.code)}</span>"
        f"<span class='id'>{escape(view.diagnosis)}</span></div>"
        + _欄(
            [
                ("Age", view.age),
                ("Living", view.living),
                ("Next visit", view.next_visit),
                ("Physician order", view.order),
                ("Medications", "\n".join(view.meds) or None),
                ("Condition events", "\n".join(view.events) or None),
            ]
        )
        + f"<p class='sub'><a href='/search?keyword={quote(view.code)}'>"
        f"Jobs for this patient →</a></p></div>"
        + 下書き
        + 記録
    )


_色 = ("#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed")

import re as _re


def _soap分解(body: str) -> dict[str, str] | None:
    """下書きから S/O/A/P を最善努力で切り出す。切れなければ None——発明しない。"""
    見出し = _re.compile(
        r"^\s*(?:#+\s*)?\**\(?(S|O|A|P)\)?\**\s*(?:\(Subjective\)|\(Objective\)|\(Assessment\)|\(Plan\))?\**\s*[:：]?\s*$",
        _re.M,
    )
    切れ目 = [(m.group(1), m.end()) for m in 見出し.finditer(body)]
    if [k for k, _ in 切れ目] != ["S", "O", "A", "P"]:
        return None
    out: dict[str, str] = {}
    for i, (k, start) in enumerate(切れ目):
        end = 切れ目[i + 1][1] - len(body[切れ目[i + 1][1]:]) if False else (
            見出し.finditer(body) and None)
    # 位置で切る
    位置 = [start for _, start in 切れ目] + [len(body)]
    始まりの行 = [m.start() for m in 見出し.finditer(body)] + [len(body)]
    for i, (k, _) in enumerate(切れ目):
        out[k.lower()] = body[位置[i]:始まりの行[i + 1]].strip().strip("-* ").strip()
    return out if all(out.values()) else None


def _md(text: str) -> str:
    """最小の Markdown 描画——見出し・箇条書き・太字だけ。外の道具は使わない。"""
    out: list[str] = []
    in_list = False
    for line in text.splitlines():
        t = line.strip()
        h = _re.match(r"^(#{1,4})\s+(.*)$", t)
        if h:
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p class='md-h'>{escape(h.group(2).strip('* '))}</p>")
            continue
        if _re.match(r"^[-*]\s+", t):
            if not in_list:
                out.append("<ul class='md-ul'>"); in_list = True
            out.append(f"<li>{_md_inline(t[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>"); in_list = False
        if t == "" or set(t) <= {"-", "—"}:
            continue
        out.append(f"<p>{_md_inline(t)}</p>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


def _md_inline(t: str) -> str:
    t = escape(t)
    return _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)


def _地図(道順ごと: dict[str, tuple[RouteStop, ...]], base: tuple[float, float] | None) -> str:
    """簡易の地図 — 座標をそのまま平面に引き伸ばして描く。**外の地図は呼ばない。**"""
    点 = [(s.lat, s.lng) for stops in 道順ごと.values() for s in stops if s.seq]
    if base:
        点.append(base)
    if not 点:
        return ""
    lat0, lat1 = min(p[0] for p in 点), max(p[0] for p in 点)
    lng0, lng1 = min(p[1] for p in 点), max(p[1] for p in 点)
    余白 = 0.004
    lat0, lat1, lng0, lng1 = lat0 - 余白, lat1 + 余白, lng0 - 余白, lng1 + 余白
    W, H = 640, 420

    def xy(lat: float, lng: float) -> tuple[float, float]:
        x = (lng - lng0) / (lng1 - lng0) * W
        y = (lat1 - lat) / (lat1 - lat0) * H
        return round(x, 1), round(y, 1)

    parts = [f"<svg viewBox='0 0 {W} {H}' style='width:100%;max-width:680px;"
             f"border:1px solid color-mix(in srgb, CanvasText 15%, transparent);"
             f"border-radius:10px;background:color-mix(in srgb, CanvasText 3%, transparent)'>"]
    for i, (担当, stops) in enumerate(sorted(道順ごと.items())):
        色 = _色[i % len(_色)]
        前 = xy(*base) if base else None
        for st in stops:
            if not st.seq:
                continue
            今 = xy(st.lat, st.lng)
            if 前:
                parts.append(f"<line x1='{前[0]}' y1='{前[1]}' x2='{今[0]}' y2='{今[1]}'"
                             f" stroke='{色}' stroke-width='2' stroke-dasharray='5 3' opacity='.75'/>")
            前 = 今
        for st in stops:
            if not st.seq:
                continue
            x, y = xy(st.lat, st.lng)
            parts.append(f"<circle cx='{x}' cy='{y}' r='11' fill='{色}'/>"
                         f"<text x='{x}' y='{y + 4}' text-anchor='middle'"
                         f" font-size='11' fill='white'>{st.seq}</text>")
    if base:
        x, y = xy(*base)
        parts.append(f"<rect x='{x - 7}' y='{y - 7}' width='14' height='14' fill='#11161d'/>"
                     f"<text x='{x}' y='{y + 22}' text-anchor='middle' font-size='10'"
                     f" fill='currentColor'>clinic</text>")
    parts.append("</svg>")
    return "".join(parts)


def _本物の地図(道順ごと: dict[str, tuple[RouteStop, ...]], base: tuple[float, float] | None, key: str) -> str:
    """Google Maps JavaScript API の地図。**鍵は窓の出自だけに効く制限つき。**"""
    import json as _json

    経路 = [
        {
            "color": _色[i % len(_色)],
            "stops": [{"lat": s.lat, "lng": s.lng, "n": s.seq, "p": s.patient}
                      for s in stops if s.seq],
        }
        for i, (_, stops) in enumerate(sorted(道順ごと.items()))
    ]
    data = _json.dumps({"base": {"lat": base[0], "lng": base[1]} if base else None, "routes": 経路})
    return (
        "<div id='gmap' style='width:100%;max-width:680px;height:440px;border-radius:10px;"
        "border:1px solid color-mix(in srgb, CanvasText 15%, transparent)'></div>"
        f"<script>const R={data};"
        "window.__troupeMap=function(){const m=new google.maps.Map("
        "document.getElementById('gmap'),{mapTypeControl:false,streetViewControl:false});"
        "const b=new google.maps.LatLngBounds();"
        "if(R.base){b.extend(R.base);new google.maps.Marker({position:R.base,map:m,"
        "label:{text:'C',color:'white'},title:'Clinic'});}"
        "for(const r of R.routes){const path=R.base?[R.base]:[];"
        "for(const s of r.stops){b.extend(s);path.push({lat:s.lat,lng:s.lng});"
        "new google.maps.Marker({position:s,map:m,label:{text:String(s.n),color:'white'},"
        "title:s.p});}"
        "new google.maps.Polyline({path,map:m,strokeColor:r.color,strokeOpacity:.8,"
        "strokeWeight:3});}"
        "m.fitBounds(b,48);};</script>"
        f"<script async src='https://maps.googleapis.com/maps/api/js?key={key}"
        "&callback=__troupeMap&loading=async'></script>"
    )


def _道順(
    day: str,
    道順ごと: dict[str, tuple[RouteStop, ...]],
    base: tuple[float, float] | None,
    maps_key: str | None = None,
    who: str | None = None,
    signed: str | None = None,
) -> str:
    from datetime import date, timedelta

    d = date.fromisoformat(day)
    前日, 翌日 = (d - timedelta(days=1)).isoformat(), (d + timedelta(days=1)).isoformat()
    who_q = f"&who={quote(who)}" if who else ""
    nav = (
        "<div class='day-bar'><span class='day-nav'>"
        f"<a href='/day?day={前日}{who_q}'>← {前日[5:]}</a> · <strong>{escape(day)}</strong>"
        f" · <a href='/day?day={翌日}{who_q}'>{翌日[5:]} →</a></span>"
        "<button class='btn btn--small push' onclick='print()'>Print day sheet</button></div>"
    )
    バナー = (
        f"<div class='banner banner--success'>✓ Signed: {escape(signed)}</div>" if signed else ""
    )
    if not 道順ごと:
        return バナー + nav + "<p class='empty'>No visits scheduled this day.</p>"

    医師たち = sorted(道順ごと)
    絞り = {who: 道順ごと[who]} if who in 道順ごと else 道順ごと
    フィルタ = (
        "<div class='filter-chips'>"
        + f"<a class='filter-chip{' is-on' if not who else ''}' href='/day?day={day}'>All</a>"
        + "".join(
            f"<a class='filter-chip{' is-on' if who == 名 else ''}'"
            f" href='/day?day={day}&who={quote(名)}'>{escape(名)}</a>"
            for 名 in 医師たち
        )
        + "</div>"
    )
    地図 = (
        _本物の地図(絞り, base, maps_key) if maps_key else _地図(絞り, base)
    )
    but = ("<p class='route-note'>Distances are straight-line estimates — not driving"
           " distance. Addresses are public landmarks standing in for homes —"
           " no real residence appears.</p>")

    節たち = []
    for i, (担当, stops) in enumerate(sorted(絞り.items())):
        予定 = [st for st in stops if st.seq]
        済み休み = [st for st in stops if not st.seq]
        署名済 = sum(1 for st in stops if st.prep == "signed")
        中止 = sum(1 for st in stops if st.status == "cancelled")
        次 = next((st for st in 予定 if st.prep != "signed" and st.status == "scheduled"), None)
        合計 = sum(float(st.leg_km) for st in 予定)
        帰路 = 0.0
        if base and 予定:
            末 = 予定[-1]
            帰路 = _km(末.lat, 末.lng, base[0], base[1])
        帯 = (
            f"<div class='progress-band'><strong>{escape(担当)}:</strong>"
            f" {署名済} of {len(stops)} signed"
            + (f" · {中止} cancelled" if 中止 else "")
            + (f" · next: {escape(次.patient)}" if 次 else " · round complete")
            + "</div>"
        )
        地点 = ([f"{base[0]},{base[1]}"] if base else []) + [
            f"{st.lat},{st.lng}" for st in 予定
        ] + ([f"{base[0]},{base[1]}"] if base and 予定 else [])
        gmap = "https://www.google.com/maps/dir/" + "/".join(地点) if 予定 else ""

        def _card(st: RouteStop) -> str:
            打消 = " stop-card--cancelled" if st.status == "cancelled" else ""
            強調 = " stop-card--next" if 次 is not None and st.visit_id == 次.visit_id else ""
            番号 = str(st.seq) if st.seq else ("✓" if st.status == "done" else "—")
            chip = (
                "<span class='chip chip--cancelled'>Cancelled</span>"
                if st.status == "cancelled"
                else f"<span class='{_CHIP[st.prep][0]}'>{_CHIP[st.prep][1]}</span>"
            )
            距離 = f"<span class='stop-card__leg'>{escape(st.leg_km)} km</span>" if st.seq else ""
            return (
                f"<li class='stop-card{打消}{強調}'>"
                f"<span class='stop-card__seq'>{番号}</span>"
                f"<span class='stop-card__main'><span class='stop-card__patient'>"
                f"<a class='patient-chip' href='/patient?code={quote(st.patient)}'>{escape(st.patient)}</a>"
                f" {escape(st.purpose)}</span>"
                f"<span class='stop-card__place sub'>{escape(st.place)}</span></span>"
                f"{chip}{距離}"
                f"<a class='link-action stop-card__open' href='/visit?id={quote(st.visit_id)}'>Open visit →</a>"
                "</li>"
            )

        節たち.append(
            f"<section class='clinician-day'><div class='clinician-day__head'>"
            f"<h3 id='{escape(担当)}' style='color:{_色[i % len(_色)]}'>{escape(担当)}</h3>"
            f"<span class='clinician-day__stats'>{len(予定)} stops · "
            f"{合計 + 帰路:.1f} km incl. return"
            + (f" · <a href='{escape(gmap)}'>open in Google Maps</a>" if gmap else "")
            + "</span></div>"
            + 帯
            + "<ol class='stop-list'>"
            + "".join(_card(st) for st in stops)
            + "</ol>"
            + (f"<div class='stop-return'>⌂ Return to clinic · {帰路:.1f} km</div>" if base and 予定 else "")
            + "</section>"
        )
    return バナー + nav + フィルタ + f"<div class='map-slot'>{地図}</div>" + but + "".join(節たち)


def _取り決めたち(rows: tuple[PatternRow, ...], added: str | None = None) -> str:
    バナー = (f"<div class='banner banner--success'>✓ {escape(added)}</div>" if added else "")
    行 = "".join(
        f"<tr{' class=agreement-row--ended' if r.active_to else ''}>"
        f"<td><a class='patient-chip' href='/patient?code={quote(r.patient)}'>{escape(r.patient)}</a></td>"
        f"<td>{escape(r.weekday)}</td>"
        f"<td>{'every week' if r.every_weeks == '1' else f'every {escape(r.every_weeks)} weeks'}</td>"
        f"<td>{escape(r.clinician)}</td><td>{escape(r.purpose)}</td>"
        f"<td>{escape(r.active_from)}</td>"
        f"<td>{escape(r.active_to) if r.active_to else '—'}</td>"
        f"<td>" + (
            f"<form class='act' method='post' action='/patterns/act'>"
            f"<input type='hidden' name='what' value='end_pattern'>"
            f"<input type='hidden' name='id' value='{escape(r.id)}'>"
            f"<button class='btn btn--destructive btn--small'"
            " onclick=\"return confirm('End this agreement? Its future planned visits will be cancelled.')\">End</button></form>"
            if r.active_to is None else ""
        ) + "</td></tr>"
        for r in rows
    )
    曜日 = "".join(f"<option>{w}</option>" for w in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"))
    form = (
        "<h3>Agree a new recurring visit</h3>"
        "<p class='sub'>The agreement with the patient is the human judgment."
        " Troupe's pulse expands it into the calendar — that part is bookkeeping.</p>"
        "<form class='act' method='post' action='/patterns/act'>"
        "<input type='hidden' name='what' value='add_pattern'>"
        "<input type='text' name='patient' placeholder='P-001' required>"
        f"<select name='weekday'>{曜日}</select>"
        "<input type='text' name='clinician' placeholder='Dr-A' required>"
        "<input type='text' name='purpose' placeholder='weekly home visit' required>"
        "<input type='date' name='start' required>"
        f"<button>{escape(操作('add_pattern'))}</button></form>"
    )
    return (
        "<div class='wrap'><table><tr><th>Patient</th><th>Weekday</th><th>Clinician</th>"
        "<th>Purpose</th><th>From</th><th>To</th><th></th></tr>" + 行 + "</table></div>" + form
    )


_CHIP = {"signed": ("chip chip--signed", "Signed ✓"),
         "draft": ("chip chip--draft-ready", "Draft ready ✓"),
         "none": ("chip chip--no-draft", "No draft yet")}


def _訪問(view: VisitView | None, 断り: str | None = None) -> str:
    if view is None:
        return "<p class='empty'>No such visit.</p>"
    pt = view.patient
    期限 = ""
    if pt.order_expires:
        期限 = (f"<dt>Physician order</dt><dd>expires "
                f"<span class='chip chip--expiring'>{escape(pt.order_expires)}</span></dd>")
    頭 = (
        f"<p class='crumbs'><a href='/day?day={quote(view.visit_date)}'>My Day</a>"
        f" → {escape(pt.code)} · Visit</p>"
        f"<div class='visit-head'><h1 class='page-title'>{escape(pt.code)} · Visit</h1>"
        f"<span class='chip'>{escape(view.status.capitalize())}</span>"
        f"<span class='visit-head__meta'>{escape(view.visit_date)} · {escape(view.clinician)}</span></div>"
        f"<div class='card snapshot'><div class='snapshot__head'>"
        f"<span class='snapshot__title'>Patient snapshot</span>"
        f"<a class='link-action push' href='/patient?code={quote(pt.code)}'>Full chart →</a></div>"
        f"<dl><dt>Diagnosis</dt><dd>{escape(pt.diagnosis)}</dd>"
        f"<dt>Age · Living</dt><dd>{escape(pt.age)} · {escape(pt.living)}</dd>"
        f"<dt>Purpose</dt><dd>{escape(view.purpose)}</dd>{期限}</dl></div>"
    )
    if view.status != "scheduled":
        済み = "".join(
            f"<div class='row'><div class='head'><span class='state state-final'>SIGNED</span>"
            f"<span class='title'>Note {escape(n.at)}</span>"
            f"<span class='id'>{escape(n.clinician)} · signed {escape(n.signed_at[:16])}</span></div>"
            + _欄([("S", n.s), ("O", n.o), ("A", n.a), ("P", n.p)]) + "</div>"
            for n in view.notes[:1]
        )
        return 頭 + f"<p class='sub'>This visit is {escape(view.status)} — read-only.</p>" + 済み
    draft = view.drafts[0] if view.drafts else None
    分解 = _soap分解(draft.body) if draft else None
    下書きパネル = ""
    if draft:
        下書きパネル = (
            "<details class='fold draft-panel' open><summary>"
            f"<span class='seal seal--draft'>DRAFT</span>"
            "<span class='draft-panel__kicker'> A proposal, not the record</span>"
            f"<span class='sub'> · delivered {escape(draft.delivered_at)}</span></summary>"
            f"<div class='draft-panel__body md'>{_md(draft.body)}</div>"
            "<p class='sub'>"
            + ("Prefilled into the editor below"
               if 分解 else "Could not be split into S/O/A/P — copy what you need")
            + ". The doctor rewrites and signs; the draft is never the record.</p></details>"
        )
    説明 = {"s": "What the patient reports.", "o": "What you observe and measure.",
            "a": "Your clinical judgment.", "p": "What happens next — checks first."}

    def 欄(名: str, key: str) -> str:
        中身 = (分解 or {}).get(key, "")
        return (f"<div class='note-field'><label for='f-{key}'>{名}</label>"
                f"<p class='hint'>{説明[key]}</p>"
                f"<textarea id='f-{key}' name='{key}' rows='6' required>{escape(中身)}</textarea></div>")
    署名者 = "".join(
        f"<option{' selected' if c == view.clinician else ''}>{escape(c)}</option>"
        for c in view.clinicians
    )
    編集 = (
        f"<form class='note-editor' method='post' action='/visit/act'>"
        f"<input type='hidden' name='what' value='sign_note'>"
        f"<input type='hidden' name='id' value='{escape(view.id)}'>"
        + (f"<input type='hidden' name='draft_id' value='{escape(draft.id)}'>" if draft else "")
        + 欄("S — Subjective", "s") + 欄("O — Objective", "o")
        + 欄("A — Assessment", "a") + 欄("P — Plan", "p")
        + "<div class='sign-bar'><span class='sign-bar__meta'>"
        f"{escape(pt.code)} · {escape(view.visit_date)} — a signed note is permanent"
        " and cannot be edited</span>"
        "<span class='sign-bar__actions'><label>Signing as <select name='signer'>"
        + 署名者 + "</select></label>"
        "<button class='btn btn--primary' onclick=\"return confirm('Sign this note and complete the visit? A signed record cannot be changed.')\">"
        "Sign and complete visit</button></span></div></form>"
    )
    休み = (
        "<div class='cancel-zone'><details class='fold'>"
        "<summary>This visit didn't happen?</summary>"
        f"<form class='act' method='post' action='/visit/act'>"
        f"<input type='hidden' name='what' value='cancel_visit'>"
        f"<input type='hidden' name='id' value='{escape(view.id)}'>"
        "<label>Reason <input type='text' name='reason' required></label>"
        "<button class='btn btn--destructive' onclick=\"return confirm('Cancel this one visit? The agreement stays.')\">Cancel this visit only</button></form>"
        "<p class='sub'>The agreement stays — only this one visit is cancelled.</p>"
        "</details></div>"
    )
    return 頭 + 下書きパネル + 編集 + 休み


def make_app(開く: 手を開く, viewer: str, maps_key: str | None = None) -> Any:
    """web の器を組む。**手は1回ごとに開いて閉じる。**

    返すのは ASGI のアプリ——立てるのは main.py（**注ぐのはそこだけ**）。
    """
    from fastapi import FastAPI, Form
    from fastapi.responses import HTMLResponse, RedirectResponse

    app = FastAPI(title="Troupe", docs_url=None, redoc_url=None)

    def 見せる(見出し: str, 描く: Callable[[手], str], 断り: str | None = None) -> HTMLResponse:
        手たち = 開く()
        try:
            return HTMLResponse(_頁(見出し, 描く(手たち), viewer, 断り))
        finally:
            手たち.close()

    @app.get("/", response_class=HTMLResponse)
    def _根() -> Any:
        return RedirectResponse("/day")

    # 古い道は新しい道へ——貼られたリンクを死なせない
    @app.get("/today")
    def _旧today() -> Any:
        return RedirectResponse("/inbox", status_code=303)

    @app.get("/route")
    def _旧route(day: str | None = None) -> Any:
        return RedirectResponse(f"/day?day={day}" if day else "/day", status_code=303)

    @app.get("/schedule")
    def _旧schedule() -> Any:
        return RedirectResponse("/automations", status_code=303)

    @app.get("/history")
    def _旧history() -> Any:
        return RedirectResponse("/activity", status_code=303)

    @app.get("/patterns")
    def _旧patterns() -> Any:
        return RedirectResponse("/agreements", status_code=303)

    @app.get("/alive")
    def _生きているか() -> dict[str, str]:
        """器が生きているかだけ。**帳簿は開かない**——脈ではない。

        （`/healthz` は載せる先の入口に取られるので使わない。）
        """
        return {"status": "ok"}

    @app.get("/inbox", response_class=HTMLResponse)
    def _今日の頁(refused: str | None = None) -> HTMLResponse:
        def 描く(h: 手) -> str:
            rows = h.fetch()
            return _帯(rows, len(h.upcoming())) + _今日(rows)

        return 見せる("inbox", 描く, refused)

    @app.get("/detail", response_class=HTMLResponse)
    def _詳細の頁(id: str, refused: str | None = None) -> HTMLResponse:
        return 見せる("inbox", lambda h: _詳細(h.detail(id)), refused)

    @app.get("/automations", response_class=HTMLResponse)
    def _予定の頁() -> HTMLResponse:
        副題 = ("<p class='page-sub'>Troupe's own work schedule — AI routines and their runs."
                " Patient visits live in <a href='/day'>My Day</a>.</p>")
        return 見せる("automations", lambda h: 副題 + _予定(h.schedule_fetch(), h.upcoming()))

    @app.get("/activity", response_class=HTMLResponse)
    def _履歴の頁() -> HTMLResponse:
        return 見せる("activity", lambda h: _履歴(h.history_fetch()))

    @app.get("/day", response_class=HTMLResponse)
    def _道順の頁(
        day: str | None = None, who: str | None = None, signed: str | None = None
    ) -> HTMLResponse:
        from datetime import date

        def 描く(h: 手) -> str:
            対象 = day or h.today()
            try:
                date.fromisoformat(対象)
            except ValueError:
                対象 = h.today()  # 壊れた日付は今日に倒す——500 は出さない
            拠点, 道順ごと = h.route(対象)
            return _道順(対象, 道順ごと, 拠点, maps_key, who, signed)

        return 見せる("day", 描く)

    @app.get("/agreements", response_class=HTMLResponse)
    def _取り決めの頁(refused: str | None = None, added: str | None = None) -> HTMLResponse:
        return 見せる("agreements", lambda h: _取り決めたち(h.patterns(), added), refused)

    @app.post("/patterns/act")
    def _取り決めを押す(
        what: str = Form(...),
        id: str = Form(""),
        patient: str = Form(""),
        weekday: str = Form(""),
        every_weeks: str = Form("1"),
        clinician: str = Form(""),
        purpose: str = Form(""),
        start: str = Form(""),
    ) -> Any:
        手たち = 開く()
        try:
            断り = 手たち.pattern_act(
                what,
                {"id": id, "patient": patient, "weekday": weekday,
                 "every_weeks": every_weeks,
                 "clinician": clinician, "purpose": purpose, "start": start},
            )
        finally:
            手たち.close()
        if 断り is None:
            戻り = ("/agreements?added=" + quote("Agreement added — visits will appear shortly")
                    if what == "add_pattern" else "/agreements")
        else:
            戻り = f"/agreements?refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/visit", response_class=HTMLResponse)
    def _訪問の頁(id: str, refused: str | None = None) -> HTMLResponse:
        return 見せる("day", lambda h: _訪問(h.visit(id), refused), refused)

    @app.post("/visit/act")
    def _訪問を押す(
        what: str = Form(...),
        id: str = Form(...),
        signer: str = Form(""),
        s: str = Form(""),
        o: str = Form(""),
        a: str = Form(""),
        p: str = Form(""),
        draft_id: str = Form(""),
        reason: str = Form(""),
    ) -> Any:
        手たち = 開く()
        try:
            断り = 手たち.visit_act(
                what,
                {"id": id, "signer": signer, "s": s, "o": o, "a": a, "p": p,
                 "draft_id": draft_id, "reason": reason},
            )
        finally:
            手たち.close()
        if 断り is None:
            if what == "sign_note":
                戻り = f"/day?signed={quote('Visit ' + id)}"
            else:
                戻り = "/day"
        else:
            戻り = f"/visit?id={quote(id)}&refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/patients", response_class=HTMLResponse)
    def _患者たちの頁() -> HTMLResponse:
        return 見せる("patients", lambda h: _患者たち(h.patients(), h.today()))

    @app.get("/patient", response_class=HTMLResponse)
    def _患者の頁(code: str) -> HTMLResponse:
        return 見せる("patients", lambda h: _患者(h.patient(code)))

    @app.get("/search", response_class=HTMLResponse)
    def _検索の頁(keyword: str = "") -> HTMLResponse:
        条件 = RowFilter(keyword=keyword or None)
        return 見せる("search", lambda h: _検索(h.search(条件), keyword))

    @app.post("/act")
    def _押す(
        what: str = Form(...),
        id: str = Form(...),
        back: str = Form("/today"),
        text: str = Form(""),
    ) -> Any:
        """押されたら文字で app を呼ぶだけ。**断られたら理由を出す。**

        押して何も起きないのが一番わるい（人に見えるもの §3）。
        操作の失敗はエラーではない——仕事の状態は変わらないので、
        一生に傷をつけず、画面にだけ理由を出す。
        """
        手たち = 開く()
        try:
            断り = 手たち.act(what, id, text)
        finally:
            手たち.close()
        つなぎ = "&" if "?" in back else "?"
        戻り = back if 断り is None else f"{back}{つなぎ}refused={断り}"
        return RedirectResponse(戻り, status_code=303)

    return app
