"""会計の読み。

設計: 設計/仕事が回る筋道.md §4。
| `BillingReader` | Reader | 月×患者の算定行・旗・請求を**文字とIDのまま**写す |
**app** | adapters | `gather_billing` |
"""

from __future__ import annotations

from typing import Protocol

from app.dto.claim_view import ClaimView


class BillingReader(Protocol):
    def read_month(self, month: str) -> tuple[ClaimView, ...]:
        """その月の請求の写し。読めなければ空。"""
        ...
