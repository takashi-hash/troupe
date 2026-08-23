"""道順の行の壊しかた。人に見えるもの §2——場所は公共の代役。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.route_stop import RouteStop


def _行(**over: object) -> RouteStop:
    data: dict[str, object] = {
        "seq": 1, "patient": "P-001", "place": "Setagaya City Hall (public landmark stand-in)",
        "purpose": "weekly visit", "leg_km": "1.4", "lat": 35.64, "lng": 139.65,
    }
    return RouteStop.model_validate(data | over)


def test_並び順と座標を持つ() -> None:
    行 = _行()
    assert 行.seq == 1 and 行.lat == 35.64


def test_書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _行().seq = 2  # type: ignore[misc]
