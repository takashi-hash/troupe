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
from app.dto.route_stop import RouteStop
from app.dto.patient_view import PatientView
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
    route: 道順の手
    today: 今日の手
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
.sub { opacity: .6; font-size: 13px; }
.row.draft { border-style: dashed; border-color: color-mix(in srgb, #b45309 55%, transparent); }
.state-draft { background: color-mix(in srgb, #b45309 18%, transparent); font-weight: 600; }
.state-final { background: color-mix(in srgb, #15803d 15%, transparent); font-weight: 600; }
.brief { padding: 10px 16px; margin-bottom: 18px; border-radius: 10px; font-size: 13.5px;
         background: color-mix(in srgb, CanvasText 5%, transparent);
         border: 1px solid color-mix(in srgb, CanvasText 10%, transparent); }
.brief a { color: inherit; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid
         color-mix(in srgb, CanvasText 12%, transparent); vertical-align: top; }
th { font-size: 13px; opacity: .6; font-weight: 500; }
.wrap { overflow-x: auto; }
"""

_画面 = ("today", "route", "schedule", "history", "search", "patients", "patterns")

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
        " — <a href='/schedule'>schedule</a>",
    ]
    return f"<div class='brief'>{' · '.join(組)}</div>"


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


def _患者たち(rows: tuple[PatientRow, ...]) -> str:
    """患者の一覧 — 診療録の写し。**よその語のまま並べる**（翻訳しない）。"""
    if not rows:
        return (
            "<p class='empty'>The agency EMR is not wired (ICHIZA_EMR_DSN), "
            "or holds no patients.</p>"
        )
    行 = "".join(
        f"<tr><td><a class='id' href='/patient?code={quote(r.code)}'>{escape(r.code)}</a></td>"
        f"<td>{escape(r.age)}</td><td>{escape(r.diagnosis)}</td>"
        f"<td>{escape(r.living)}</td><td>{escape(r.next_visit or '—')}</td>"
        f"<td>{escape(r.order_expires or '—')}</td></tr>"
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
        f"<div class='row draft'><div class='head'>"
        f"<span class='state state-draft'>DRAFT</span>"
        f"<span class='title'>delivered {escape(d.delivered_at[:16])}</span>"
        f"<a class='id' href='/detail?id={escape(d.job_id)}'>from job {escape(d.job_id[:8])}…</a></div>"
        f"<div style='white-space:pre-wrap'>{escape(d.body)}</div>"
        "<p class='sub'>A proposal from Troupe. A doctor rewrites and signs it in the EMR — "
        "this never becomes the record by itself.</p></div>"
        for d in view.drafts
    )
    記録 = "".join(
        f"<div class='row'><div class='head'>"
        f"<span class='state state-final'>SIGNED</span>"
        f"<span class='title'>Note {escape(n.at)}</span>"
        f"<span class='id'>{escape(n.clinician)} · signed {escape(n.signed_at[:16])}</span></div>"
        + _欄([("S", n.s), ("O", n.o), ("A", n.a), ("P", n.p)])
        + "</div>"
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


def _地図(道順ごと: dict[str, tuple[RouteStop, ...]], base: tuple[float, float] | None) -> str:
    """簡易の地図 — 座標をそのまま平面に引き伸ばして描く。**外の地図は呼ばない。**"""
    点 = [(s.lat, s.lng) for stops in 道順ごと.values() for s in stops]
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
            今 = xy(st.lat, st.lng)
            if 前:
                parts.append(f"<line x1='{前[0]}' y1='{前[1]}' x2='{今[0]}' y2='{今[1]}'"
                             f" stroke='{色}' stroke-width='2' stroke-dasharray='5 3' opacity='.75'/>")
            前 = 今
        for st in stops:
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
            "stops": [{"lat": s.lat, "lng": s.lng, "n": s.seq, "p": s.patient} for s in stops],
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
) -> str:
    from datetime import date, timedelta

    d = date.fromisoformat(day)
    前日, 翌日 = (d - timedelta(days=1)).isoformat(), (d + timedelta(days=1)).isoformat()
    nav = (f"<p><a href='/route?day={前日}'>← {前日}</a> · <strong>{escape(day)}</strong>"
           f" · <a href='/route?day={翌日}'>{翌日} →</a></p>")
    if not 道順ごと:
        return nav + "<p class='empty'>No visits scheduled this day.</p>"
    地図 = (
        _本物の地図(道順ごと, base, maps_key) if maps_key else _地図(道順ごと, base)
    )
    とび = " · ".join(
        f"<a href='#{escape(担当)}'>{escape(担当)}</a>" for 担当 in sorted(道順ごと)
    )
    表たち = [f"<p class='sub'>Jump to: {とび}</p>"] if len(道順ごと) > 1 else []
    for i, (担当, stops) in enumerate(sorted(道順ごと.items())):
        色 = _色[i % len(_色)]
        行 = "".join(
            f"<tr><td>{s.seq}</td>"
            f"<td><a class='id' href='/patient?code={quote(s.patient)}'>{escape(s.patient)}</a></td>"
            f"<td>{escape(s.place)}</td><td>{escape(s.purpose)}</td><td>{escape(s.leg_km)} km</td></tr>"
            for s in stops
        )
        地点 = ([f"{base[0]},{base[1]}"] if base else []) + [f"{s.lat},{s.lng}" for s in stops]
        gmap = "https://www.google.com/maps/dir/" + "/".join(地点) if 地点 else ""
        合計 = sum(float(s.leg_km) for s in stops)
        表たち.append(
            f"<h3 id='{escape(担当)}' style='color:{色}'>{escape(担当)}"
            f" <span class='sub'>{len(stops)} visits · {合計:.1f} km"
            + (f" · <a href='{escape(gmap)}'>open in Google Maps</a>" if gmap else "")
            + "</span></h3>"
            "<div class='wrap'><table><tr><th>#</th><th>Patient</th><th>Place (public stand-in)"
            "</th><th>Purpose</th><th>Leg</th></tr>" + 行 + "</table></div>"
        )
    return (nav + 地図
            + "<p class='sub'>Stops are greedy nearest-neighbour from the clinic."
              " Addresses are public landmarks standing in for homes — no real residence appears.</p>"
            + "".join(表たち))


def _取り決めたち(rows: tuple[PatternRow, ...]) -> str:
    行 = "".join(
        f"<tr><td>{escape(r.patient)}</td><td>{escape(r.weekday)}</td>"
        f"<td>{escape(r.clinician)}</td><td>{escape(r.purpose)}</td>"
        f"<td>{escape(r.active_from)}</td>"
        f"<td>{escape(r.active_to) if r.active_to else '—'}</td>"
        f"<td>" + (
            f"<form class='act' method='post' action='/patterns/act'>"
            f"<input type='hidden' name='what' value='end_pattern'>"
            f"<input type='hidden' name='id' value='{escape(r.id)}'>"
            f"<button>{escape(操作('end_pattern'))}</button></form>" if r.active_to is None else ""
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
        return RedirectResponse("/today")

    @app.get("/alive")
    def _生きているか() -> dict[str, str]:
        """器が生きているかだけ。**帳簿は開かない**——脈ではない。

        （`/healthz` は載せる先の入口に取られるので使わない。）
        """
        return {"status": "ok"}

    @app.get("/today", response_class=HTMLResponse)
    def _今日の頁(refused: str | None = None) -> HTMLResponse:
        def 描く(h: 手) -> str:
            rows = h.fetch()
            return _帯(rows, len(h.upcoming())) + _今日(rows)

        return 見せる("today", 描く, refused)

    @app.get("/detail", response_class=HTMLResponse)
    def _詳細の頁(id: str, refused: str | None = None) -> HTMLResponse:
        return 見せる("today", lambda h: _詳細(h.detail(id)), refused)

    @app.get("/schedule", response_class=HTMLResponse)
    def _予定の頁() -> HTMLResponse:
        return 見せる("schedule", lambda h: _予定(h.schedule_fetch(), h.upcoming()))

    @app.get("/history", response_class=HTMLResponse)
    def _履歴の頁() -> HTMLResponse:
        return 見せる("history", lambda h: _履歴(h.history_fetch()))

    @app.get("/route", response_class=HTMLResponse)
    def _道順の頁(day: str | None = None) -> HTMLResponse:
        from datetime import date

        def 描く(h: 手) -> str:
            対象 = day or h.today()
            try:
                date.fromisoformat(対象)
            except ValueError:
                対象 = h.today()  # 壊れた日付は今日に倒す——500 は出さない
            拠点, 道順ごと = h.route(対象)
            return _道順(対象, 道順ごと, 拠点, maps_key)

        return 見せる("route", 描く)

    @app.get("/patterns", response_class=HTMLResponse)
    def _取り決めの頁(refused: str | None = None) -> HTMLResponse:
        return 見せる("patterns", lambda h: _取り決めたち(h.patterns()), refused)

    @app.post("/patterns/act")
    def _取り決めを押す(
        what: str = Form(...),
        id: str = Form(""),
        patient: str = Form(""),
        weekday: str = Form(""),
        clinician: str = Form(""),
        purpose: str = Form(""),
        start: str = Form(""),
    ) -> Any:
        手たち = 開く()
        try:
            断り = 手たち.pattern_act(
                what,
                {"id": id, "patient": patient, "weekday": weekday,
                 "clinician": clinician, "purpose": purpose, "start": start},
            )
        finally:
            手たち.close()
        戻り = "/patterns" if 断り is None else f"/patterns?refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/patients", response_class=HTMLResponse)
    def _患者たちの頁() -> HTMLResponse:
        return 見せる("patients", lambda h: _患者たち(h.patients()))

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
