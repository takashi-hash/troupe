"""取り決めの部品 — 単独頁は退役し、Patients の頁がここから組む。

/agreements は /patients へ 303。表・結ぶフォーム・数・バナーを部品として輸出する。
"""
from __future__ import annotations
from app.dto.pattern_row import PatternRow
from html import escape
from ui.words import 操作
from urllib.parse import quote

#: 一覧の空文 — 取り決めが1件も無いとき、この製品で本当のことを1行言う（"No data" は言わない）
_空文 = ("No agreement is on record. Planned visits derive from"
         " agreements — record one and Troupe's pulse expands it into the calendar.")


def _取り決め数(rows: tuple[PatternRow, ...]) -> tuple[int, int]:
    """(有効, 終了) — 有効＝active_to が無いもの。"""
    有効 = sum(1 for r in rows if r.active_to is None)
    return 有効, len(rows) - 有効


def _追加バナー(added: str | None) -> str:
    """結べたことの報せ — 節の頭に置く緑のバナー。"""
    return f"<div class='banner banner--success'>✓ {escape(added)}</div>" if added else ""


def _取り決め表(
    rows: tuple[PatternRow, ...],
    back: str = "",
    患者列: bool = True,
    空文: str = _空文,
) -> str:
    """取り決めの表 — 一覧と患者詳細で共用。

    back を渡すと End がその頁へ戻る（渡さなければ routes の既定 /patients）。
    患者詳細では 患者列=False で Patient 列を落とす。
    """
    if not rows:
        return f"<p class='empty'>{空文}</p>"
    隠し戻り = (f"<input type='hidden' name='back' value='{escape(back)}'>" if back else "")
    行 = "".join(
        f"<tr{' class=agreement-row--ended' if r.active_to else ''}>"
        + (
            f"<td><a class='patient-chip' href='/patient?code={quote(r.patient)}'>{escape(r.patient)}</a></td>"
            if 患者列 else ""
        )
        + f"<td>{escape(r.weekday)}</td>"
        f"<td>{'every week' if r.every_weeks == '1' else f'every {escape(r.every_weeks)} weeks'}</td>"
        f"<td>{escape(r.clinician)}</td><td>{escape(r.purpose)}</td>"
        f"<td class='cell-when'>{escape(r.active_from)}</td>"
        f"<td class='cell-when'>{escape(r.active_to) if r.active_to else '—'}</td>"
        f"<td>" + (
            f"<form class='act' method='post' action='/patterns/act'>"
            f"<input type='hidden' name='what' value='end_pattern'>"
            f"<input type='hidden' name='id' value='{escape(r.id)}'>"
            + 隠し戻り
            + "<button class='btn btn--destructive btn--small'"
            " onclick=\"return confirm('End this agreement? Its future planned visits will be cancelled.')\">End</button></form>"
            if r.active_to is None else ""
        ) + "</td></tr>"
        for r in rows
    )
    return (
        "<div class='wrap'><table><tr>"
        + ("<th>Patient</th>" if 患者列 else "")
        + "<th>Weekday</th><th>Cadence</th>"
        "<th>Clinician</th><th>Purpose</th><th>From</th><th>To</th><th></th></tr>"
        + 行 + "</table></div>"
    )


def _取り決めフォーム(back: str) -> str:
    """取り決めを結ぶ form-card — 一覧頁の右レール用。入力は退役前の頁と同じ。"""
    曜日 = "".join(f"<option>{w}</option>" for w in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"))
    return (
        "<aside class='form-card'>"
        "<h3 class='form-card__title'>Agree a new recurring visit</h3>"
        "<p class='sub'>The agreement with the patient is the human judgment."
        " Troupe's pulse expands it into the calendar — that part is bookkeeping.</p>"
        "<form method='post' action='/patterns/act'>"
        "<input type='hidden' name='what' value='add_pattern'>"
        f"<input type='hidden' name='back' value='{escape(back)}'>"
        "<div class='form-grid'>"
        "<div class='field'><label for='agr-patient'>Patient</label>"
        "<input type='text' id='agr-patient' name='patient' placeholder='P-001' required></div>"
        "<div class='field'><label for='agr-weekday'>Weekday</label>"
        f"<select id='agr-weekday' name='weekday'>{曜日}</select></div>"
        "<div class='field'><label for='agr-clinician'>Clinician</label>"
        "<input type='text' id='agr-clinician' name='clinician' placeholder='Dr-A' required></div>"
        "<div class='field'><label for='agr-purpose'>Purpose</label>"
        "<input type='text' id='agr-purpose' name='purpose' placeholder='weekly home visit' required></div>"
        "<div class='field'><label for='agr-start'>Start</label>"
        "<input type='date' id='agr-start' name='start' required></div>"
        "</div>"
        f"<div class='form-actions'><button class='btn'>{escape(操作('add_pattern'))}</button></div>"
        "</form></aside>"
    )


def _患者の取り決めフォーム(patient: str, back: str) -> str:
    """患者詳細の小さい結びフォーム — 患者は隠し入力で決め打ち。名前は routes と同じ。"""
    曜日 = "".join(f"<option>{w}</option>" for w in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"))
    間隔 = "".join(
        f"<option value='{n}'>{'every week' if n == '1' else f'every {n} weeks'}</option>"
        for n in ("1", "2", "3", "4")
    )
    return (
        "<aside class='form-card'>"
        "<h3 class='form-card__title'>Agree a recurring visit</h3>"
        "<form method='post' action='/patterns/act'>"
        "<input type='hidden' name='what' value='add_pattern'>"
        f"<input type='hidden' name='patient' value='{escape(patient)}'>"
        f"<input type='hidden' name='back' value='{escape(back)}'>"
        "<div class='form-grid'>"
        "<div class='field'><label for='pd-agr-weekday'>Weekday</label>"
        f"<select id='pd-agr-weekday' name='weekday'>{曜日}</select></div>"
        "<div class='field'><label for='pd-agr-cadence'>Cadence</label>"
        f"<select id='pd-agr-cadence' name='every_weeks'>{間隔}</select></div>"
        "<div class='field'><label for='pd-agr-clinician'>Clinician</label>"
        "<input type='text' id='pd-agr-clinician' name='clinician' placeholder='Dr-A' required></div>"
        "<div class='field'><label for='pd-agr-purpose'>Purpose</label>"
        "<input type='text' id='pd-agr-purpose' name='purpose' placeholder='weekly home visit' required></div>"
        "<div class='field'><label for='pd-agr-start'>Start</label>"
        "<input type='date' id='pd-agr-start' name='start' required></div>"
        "</div>"
        f"<div class='form-actions'><button class='btn'>{escape(操作('add_pattern'))}</button></div>"
        "</form></aside>"
    )
