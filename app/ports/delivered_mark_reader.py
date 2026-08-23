"""配達の印の読み。

設計: 設計/仕事が回る筋道.md §4。
| `DeliveredMarkReader` | Reader | 既に「下書きが配達された」の印のある仕事の識別子——
二度目を運ばない照合 | **app** | adapters | `deliver_drafts` |

印は出来事（`DraftDelivered`）にしか残らず、仕事の欄には無い——
設計に無い欄を足さず、刻んだ事実そのものを照合の材料にする（`OverdueMarkReader` と同じ構え）。
**帳簿が配達を覚えている**から、診療録の種を入れ直しても二度目は運ばれない。
"""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.job.job_id import JobId


class DeliveredMarkReader(Protocol):
    """既に「下書きが配達された」の印が刻まれた仕事の読み。二度目を運ばない照合の材料。"""

    def marked_ids(self) -> frozenset[JobId]:
        """既に印のある仕事の識別子をぜんぶ。"""
        ...
