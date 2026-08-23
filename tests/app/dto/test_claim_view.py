"""請求の写しの壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.claim_view import ClaimView


def make_view(**over: object) -> ClaimView:
    data: dict[str, object] = {
        "patient": "P-001", "month": "2026-08", "status": "draft",
        "total_points": 3200, "copay_rate": 1, "copay_yen": 3200,
        "confirmed_by": None, "confirmed_at": None, "charges": (),
    }
    return ClaimView.model_validate(data | over)


def test_欄は設計の請求の写しそのまま() -> None:
    assert set(ClaimView.model_fields) == {
        "patient", "month", "status", "total_points", "copay_rate", "copay_yen",
        "confirmed_by", "confirmed_at", "charges",
    }


def test_確定の写しは誰がいつを運ぶ() -> None:
    v = make_view(status="confirmed", confirmed_by="Director", confirmed_at="2026-09-01 09:00")
    assert (v.confirmed_by, v.status) == ("Director", "confirmed")


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_view().total_points = 0  # type: ignore[misc]
