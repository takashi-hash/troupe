"""いまの眺めの壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.now_view import NowView


def test_欄は設計のいまの眺めそのまま() -> None:
    assert set(NowView.model_fields) == {
        "queued", "working", "checking", "waiting", "beat_at",
    }


def test_作ったあと書き換えられない() -> None:
    v = NowView(queued=0, working=(), checking=0, waiting=0, beat_at=None)
    with pytest.raises(ValidationError):
        v.waiting = 9  # type: ignore[misc]


def test_予告の欄は無い() -> None:
    """予告しない——最後の脈の事実だけ（設計 §1「いま」）。next の名の欄を持たない。"""
    assert not [f for f in NowView.model_fields if "next" in f]
