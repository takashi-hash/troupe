"""期日切れの印の読み。

設計: 設計/仕事が回る筋道.md §4。
| `OverdueMarkReader` | Reader | 既に「期日を過ぎた」の印のある仕事の識別子——二度目を刻まない照合 | **app** | adapters | `mark_overdue` |

印は出来事（`DueDatePassed`）にしか残らず、仕事の欄には無い——
設計に無い欄を足さず、刻んだ事実そのものを照合の材料にする。
"""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.job.job_id import JobId


class OverdueMarkReader(Protocol):
    """既に「期日を過ぎた」の印が刻まれた仕事の読み。二度目を刻まないための照合の材料。"""

    def marked_ids(self) -> frozenset[JobId]:
        """既に印のある仕事の識別子をぜんぶ。"""
        ...
