"""道順の材料の読みの宣言の壊しかた。筋道 §4。"""

from __future__ import annotations

from app.ports.route_reader import RouteBase, RouteReader, RouteVisit


class 道順読みの偽物:
    def read_day(self, day: str) -> tuple[RouteBase | None, tuple[RouteVisit, ...]]:
        return None, ()


def test_宣言は名乗りだけで満たせる() -> None:
    読み: RouteReader = 道順読みの偽物()
    assert 読み.read_day("2026-08-24") == (None, ())
