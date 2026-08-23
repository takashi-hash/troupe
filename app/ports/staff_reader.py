"""職員の登記簿の読み。

設計: 設計/仕事が回る筋道.md §4。
| `StaffReader` | Reader | 職員の登記簿（席の名・役=座長/医師）を写す。**役の正本はデータ**
——診療録の staff と clinicians（医師の名簿）。**席は名乗りであって認証ではない**
（力の源はすべて登記簿の門） | **app** | adapters | `gather_staff` |
"""

from __future__ import annotations

from typing import Protocol

from app.dto.staff_row import StaffRow


class StaffReader(Protocol):
    def read_all(self) -> tuple[StaffRow, ...]:
        """登記簿の全行。読めなければ空。"""
        ...
