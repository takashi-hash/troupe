"""席と役を集める — 職員の登記簿の写し。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」。
| 席と役を集める | `gather_staff` | 職員の登記簿（席の名と役）の写し——切り替えの選びと、
押せることの出し分けに使う | 読むだけ |
"""

from __future__ import annotations

from app.dto.staff_row import StaffRow
from app.ports.staff_reader import StaffReader


def gather_staff(staff: StaffReader) -> tuple[StaffRow, ...]:
    """登記簿の全行。読むだけ——どこにも書かない。"""
    return staff.read_all()
