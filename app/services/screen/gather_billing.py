"""会計を集める — 月×患者の算定行・旗・請求の写し。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの §1「会計」。
| 会計を集める | `gather_billing` | 月×患者の算定行・旗・請求の写しを集める | 読むだけ |
"""

from __future__ import annotations

from app.dto.claim_view import ClaimView
from app.ports.billing_reader import BillingReader


def gather_billing(billing: BillingReader, month: str) -> tuple[ClaimView, ...]:
    """その月の請求の写し。読むだけ——どこにも書かない。"""
    return billing.read_month(month)
