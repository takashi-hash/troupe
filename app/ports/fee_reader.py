"""点数表の読み。

設計: 設計/仕事が回る筋道.md §4。
| `FeeReader` | Reader | 点数表マスタの行を**文字とIDのまま**写す | **app** | adapters | `gather_fees` |
"""

from __future__ import annotations

from typing import Protocol

from app.dto.fee_row import FeeRow


class FeeReader(Protocol):
    def read_all(self) -> tuple[FeeRow, ...]:
        """マスタの全行。読めなければ空。"""
        ...
