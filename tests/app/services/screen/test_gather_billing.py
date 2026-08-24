"""会計を集めるの壊しかた。読むだけ・写しをそのまま。"""

from __future__ import annotations

from app.dto.claim_view import ClaimView
from app.services.screen.gather_billing import gather_billing


class 会計読みの偽物:
    def __init__(self, views: tuple[ClaimView, ...]) -> None:
        self._views = views

    def read_month(self, month: str) -> tuple[ClaimView, ...]:
        self.asked = month
        return self._views

    def count_flagged(self) -> int:
        return 0


def test_月を渡して写しがそのまま返る() -> None:
    読み = 会計読みの偽物(())
    assert gather_billing(読み, "2026-08") == ()
    assert 読み.asked == "2026-08"
