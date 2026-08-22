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
from typing import Any, NamedTuple, Protocol

from app.dto.detail_view import DetailView
from app.dto.history_row import HistoryRow
from app.dto.row_filter import RowFilter
from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from app.dto.today_row import TodayRow
from ui.words import 操作, 状態, 語, 読める


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
    close: Callable[[], None]


class 手を開く(Protocol):
    def __call__(self) -> 手:
        """帳簿を開き、手の束を組んで返す。**呼ばれるたびに新しい。**"""
        ...


# --- 見せかた。ここから下は「入っているものを出す」だけ ---

_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.7 -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif;
       background: Canvas; color: CanvasText; }
header { padding: 14px 20px; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent);
         display: flex; gap: 18px; align-items: baseline; flex-wrap: wrap; }
header .name { font-weight: 700; letter-spacing: .02em; }
header .who { opacity: .65; font-size: 13px; }
nav a { margin-right: 14px; text-decoration: none; color: inherit; opacity: .6; }
nav a.on { opacity: 1; font-weight: 600; border-bottom: 2px solid currentColor; }
main { padding: 20px; max-width: 900px; }
.row { border: 1px solid color-mix(in srgb, CanvasText 15%, transparent); border-radius: 10px;
       padding: 14px 16px; margin-bottom: 14px; }
.head { display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; margin-bottom: 6px; }
.head .title { font-weight: 600; }
.state { font-size: 12px; padding: 2px 8px; border-radius: 999px;
         background: color-mix(in srgb, CanvasText 10%, transparent); }
.id { font-size: 12px; opacity: .5; font-family: ui-monospace, monospace; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 14px; margin: 8px 0 0; }
dt { opacity: .6; font-size: 13px; }
dd { margin: 0; white-space: pre-wrap; }
form.act { display: inline-flex; gap: 6px; margin: 10px 8px 0 0; align-items: center; }
button { font: inherit; padding: 5px 14px; border-radius: 8px; cursor: pointer;
         border: 1px solid color-mix(in srgb, CanvasText 30%, transparent); background: transparent;
         color: inherit; }
button:hover { background: color-mix(in srgb, CanvasText 8%, transparent); }
input[type=text] { font: inherit; padding: 5px 8px; border-radius: 8px;
                   border: 1px solid color-mix(in srgb, CanvasText 25%, transparent);
                   background: transparent; color: inherit; }
.refusal { border-left: 3px solid #c0392b; padding: 10px 14px; margin-bottom: 16px;
           background: color-mix(in srgb, #c0392b 8%, transparent); border-radius: 0 8px 8px 0; }
.empty { opacity: .55; padding: 30px 0; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid
         color-mix(in srgb, CanvasText 12%, transparent); vertical-align: top; }
th { font-size: 13px; opacity: .6; font-weight: 500; }
.wrap { overflow-x: auto; }
"""

_画面 = ("today", "schedule", "history", "search")

#: 書く欄の見出し。**用語集の語ではない**——押すときの手がかりなので、そのまま英語で置く。
_書く欄 = {"answer": "Answer", "send_back": "Reason", "abandon": "Reason"}


def _頁(見出し: str, 中身: str, viewer: str, 断り: str | None = None) -> str:
    """窓の枠。**押しつけは今日だけ**——残りは引き出し（人に見えるもの §1）。"""
    tabs = "".join(
        f'<a class="{"on" if 識別子 == 見出し else ""}" href="/{識別子}">'
        f"{escape(読める(識別子))}</a>"
        for 識別子 in _画面
    )
    警告 = f'<div class="refusal">{escape(断り)}</div>' if 断り else ""
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Troupe — {escape(読める(見出し))}</title><style>{_STYLE}</style></head><body>"
        f"<header><span class='name'>Troupe</span><nav>{tabs}</nav>"
        f"<span class='who'>Viewer: {escape(viewer)}</span></header>"
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
    out = []
    for what in 押せる:
        名 = 操作(what)
        欄 = _書く欄.get(what)
        書く = (
            f"<input type='text' name='text' placeholder='{escape(欄)}' required>"
            if 欄
            else ""
        )
        out.append(
            f"<form class='act' method='post' action='/act'>"
            f"<input type='hidden' name='what' value='{escape(what)}'>"
            f"<input type='hidden' name='id' value='{escape(job_id)}'>"
            f"<input type='hidden' name='back' value='{escape(戻り)}'>"
            f"{書く}<button>{escape(名)}</button></form>"
        )
    return "".join(out)


def _状態(名: str) -> str:
    return f"<span class='state'>{escape(状態(名))}</span>"


def _今日(rows: tuple[TodayRow, ...]) -> str:
    if not rows:
        return "<p class='empty'>Nothing needs your judgment today.</p>"
    out = []
    for r in rows:
        見出し = r.rule or r.request_head or ""
        使った = f"{r.spent_calls}/{r.budget_calls} calls, {r.spent_seconds}/{r.budget_seconds} s"
        見立て = "\n".join(f"{本文}（{理由}）" for 本文, 理由 in r.assessments)
        out.append(
            f"<div class='row'><div class='head'>"
            f"<span class='title'>{escape(見出し)} {escape(r.period or '')}</span>"
            f"{_状態(r.state_name)}<a class='id' href='/detail?id={escape(r.id)}'>{escape(r.id)}</a>"
            f"</div>"
            + _欄(
                [
                    (語("やること"), r.instruction),
                    (語("期日"), r.due),
                    (語("担当"), r.assignee_name),
                    (語("質問"), r.question_body),
                    (語("回答"), r.answer_body),
                    (語("成果"), r.result_body),
                    (語("根拠"), r.evidence_quote),
                    (語("見立て"), 見立て),
                    (語("確かめ期日"), r.recheck_at),
                    ("Retries", "exhausted" if r.retries_exhausted else None),
                    (語("使った量"), 使った),
                ]
            )
            + _押せること(r.actions, r.id, "/today")
            + "</div>"
        )
    return "".join(out)


def _詳細(view: DetailView | None) -> str:
    if view is None:
        return "<p class='empty'>No such job.</p>"
    問答 = "\n".join(f"Q: {q}\nA: {a or '(not yet)'}" for q, a in view.questions)
    見立て = "\n".join(f"{本文}（{理由}）" for 本文, 理由 in view.assessments)
    出来事 = "".join(
        f"<tr><td>{escape(e.at)}</td><td>{escape(e.by)}</td><td>{escape(e.what)}</td></tr>"
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
        + 出来事
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
        f"<tr><td>{escape(r.at)}</td><td>{escape(r.by)}</td><td>{escape(r.what)}</td>"
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


def make_app(開く: 手を開く, viewer: str) -> Any:
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
        return RedirectResponse("/today")

    @app.get("/alive")
    def _生きているか() -> dict[str, str]:
        """器が生きているかだけ。**帳簿は開かない**——脈ではない。

        （`/healthz` は載せる先の入口に取られるので使わない。）
        """
        return {"status": "ok"}

    @app.get("/today", response_class=HTMLResponse)
    def _今日の頁(refused: str | None = None) -> HTMLResponse:
        return 見せる("today", lambda h: _今日(h.fetch()), refused)

    @app.get("/detail", response_class=HTMLResponse)
    def _詳細の頁(id: str, refused: str | None = None) -> HTMLResponse:
        return 見せる("today", lambda h: _詳細(h.detail(id)), refused)

    @app.get("/schedule", response_class=HTMLResponse)
    def _予定の頁() -> HTMLResponse:
        return 見せる("schedule", lambda h: _予定(h.schedule_fetch(), h.upcoming()))

    @app.get("/history", response_class=HTMLResponse)
    def _履歴の頁() -> HTMLResponse:
        return 見せる("history", lambda h: _履歴(h.history_fetch()))

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
