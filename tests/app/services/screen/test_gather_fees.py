"""点数表を集めるの壊しかた。読むだけ。"""

from __future__ import annotations

from app.services.screen.gather_fees import gather_fees


class 点数表読みの偽物:
    def read_all(self):  # noqa: ANN201
        self.asked = True
        return ()


def test_マスタの写しがそのまま返る() -> None:
    読み = 点数表読みの偽物()
    assert gather_fees(読み) == ()
    assert 読み.asked
