"""席と役を集めるの壊しかた。読むだけ。"""

from __future__ import annotations

from app.services.screen.gather_staff import gather_staff


class 登記簿読みの偽物:
    def read_all(self):  # noqa: ANN201
        self.asked = True
        return ()


def test_登記簿の写しがそのまま返る() -> None:
    読み = 登記簿読みの偽物()
    assert gather_staff(読み) == ()
    assert 読み.asked
