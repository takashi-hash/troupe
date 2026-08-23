"""定期訪問の取り決めへの口。**人の操作だけが呼ぶ。**

設計: 設計/仕事が回る筋道.md §4。
| `EmrPatternPort` | Port | 定期訪問の取り決めを診療録に載せる・終える・読む。
**人の操作だけが呼ぶ** | **app** | adapters | `add_pattern`・`end_pattern`・`gather_patterns` |

**取り決めこそが判断**（患者と調整済みの約束）。だから載せる・終えるは人の操作からしか
呼ばれない。ここから先の展開（予定づくり）は脈の帳簿づけ。
"""

from __future__ import annotations

from typing import Protocol

from app.dto.pattern_row import PatternRow


class EmrPatternPort(Protocol):
    def read_all(self) -> tuple[PatternRow, ...]:
        """取り決めの一覧。繋がっていなければ空。"""
        ...

    def add(
        self, patient: str, weekday: str, clinician: str, purpose: str, start: str,
        every_weeks: str = "1", *, by: str = "",
    ) -> str | None:
        """取り決めを載せる。通れば None、載せられなければ理由の文字。"""
        ...

    def end(self, pattern_id: str, on: str, by: str) -> str | None:
        """取り決めに終わりの日を入れる。列は消さない。通れば None。"""
        ...
