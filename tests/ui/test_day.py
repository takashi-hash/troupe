"""今日の器の壊しかた。人に見えるもの §1「今日」——中止の札は支度の札を覆い隠す。

代役（cloud/pilot.py）は頁の文字 'Draft ready' を見て署名の相手を選ぶ——
中止済みの訪問に下書きが在っても、この頁が 'Cancelled' しか出さないことが、
中止済みへの署名を代役に試みさせない前提。ここで固定する。
"""

from __future__ import annotations

from app.dto.route_stop import RouteStop
from ui.web.day import _道順


def _stop(**over: object) -> RouteStop:
    data: dict[str, object] = {
        "seq": 1, "visit_id": "88", "prep": "draft", "status": "scheduled",
        "patient": "P-006", "place": "landmark", "purpose": "weekly visit",
        "leg_km": "1.2", "lat": 35.6, "lng": 139.6,
    }
    return RouteStop.model_validate(data | over)


def test_予定のままの下書きは札が出る() -> None:
    頁 = _道順("2026-08-25", {"Dr-C": (_stop(),)}, None)
    assert "Draft ready" in 頁


def test_中止の訪問は支度の札でなく中止の札_代役の文字合わせが偽陽性にならない() -> None:
    頁 = _道順(
        "2026-08-25",
        {"Dr-C": (_stop(status="cancelled", prep="draft", seq=0),)},
        None,
    )
    assert "Cancelled" in 頁
    assert "Draft ready" not in 頁
