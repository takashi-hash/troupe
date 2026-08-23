"""訪問を集めるの壊しかた。読むだけ・写しをそのまま。"""

from __future__ import annotations

from app.dto.visit_view import VisitView
from app.services.screen.gather_visit import gather_visit


class 訪問読みの偽物:
    def __init__(self, view: VisitView | None) -> None:
        self._view = view

    def read_one(self, visit_id: str) -> VisitView | None:
        self.asked = visit_id
        return self._view


def test_居ない訪問はNone() -> None:
    読み = 訪問読みの偽物(None)
    assert gather_visit(読み, "999") is None
    assert 読み.asked == "999"
