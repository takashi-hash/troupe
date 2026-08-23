"""訪問の読みの宣言の壊しかた。筋道 §4。"""

from __future__ import annotations

from app.dto.visit_view import VisitView
from app.ports.visit_reader import VisitReader


class 訪問読みの偽物:
    def read_one(self, visit_id: str) -> VisitView | None:
        return None


def test_宣言は名乗りだけで満たせる() -> None:
    読み: VisitReader = 訪問読みの偽物()
    assert 読み.read_one("7") is None
