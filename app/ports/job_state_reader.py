"""ある状態の仕事の読み。

設計: 設計/仕事が回る筋道.md §4。
| `JobStateReader` | Reader | ある状態の仕事の識別子。**担当でも絞れる** | **app** | adapters |
`start`・`ask`・`submit`・`fail`・`assess`・`spend`・`hand_out`・`return_timed_out`・
`run_check`・`sort_failures`・`confirm`・`mark_overdue` |

**Repository は鍵で1件。一覧と絞り込みは Reader**——中心の interface に都合が入り込まない。
返すのは識別子だけ——中身が要る者は `JobRepository` で読み戻す。
"""

from __future__ import annotations

from typing import Protocol

from domain.values.job.job_id import JobId


class JobStateReader(Protocol):
    def ids_in(self, state_name: str, assignee_name: str | None = None) -> tuple[JobId, ...]:
        """その状態の仕事の識別子。担当の名を渡せばその担当のぶんだけ。"""
        ...
