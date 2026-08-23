"""会計の読みの宣言の壊しかた。筋道 §4。"""

from __future__ import annotations

from app.dto.claim_view import ClaimView
from app.ports.billing_reader import BillingReader


class 会計読みの偽物:
    def read_month(self, month: str) -> tuple[ClaimView, ...]:
        return ()

    def count_flagged(self) -> int:
        return 0


def test_宣言は名乗りだけで満たせる() -> None:
    読み: BillingReader = 会計読みの偽物()
    assert 読み.read_month("2026-08") == ()
    assert 読み.count_flagged() == 0
