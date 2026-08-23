"""点数表を集める — マスタの写し。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの §1「点数表」。
| 点数表を集める | `gather_fees` | 点数表マスタの写し | 同上 |
"""

from __future__ import annotations

from app.dto.fee_row import FeeRow
from app.ports.fee_reader import FeeReader


def gather_fees(fees: FeeReader) -> tuple[FeeRow, ...]:
    """マスタの全行。読むだけ。"""
    return fees.read_all()
