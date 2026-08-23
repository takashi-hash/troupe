"""下書きを配達する — 配達の事実を一度だけ刻む。**状態は変わらない。**

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」・仕事とは何か.md §6。
| 下書きを配達する | `deliver_drafts` | 承認の済んだカルテの下書きを診療録へ
**draft としてだけ**置く。置けたら **`DraftDelivered` を刻む** | 承認は済んでいる。
運ぶだけ——**印の無いものだけ運ぶ** |

遷移表の外で刻める例外のひとつ（`DraftDelivered`）——
**同じ状態の型を返す関数**として書く。返すのは（同じ状態, 出来事）の対。
**時計が起こす**——`by=Clock()`。承認を経ていない状態と、成果の無い仕事には何も刻まない
——承認前の提案が診療録に渡る道を、ここで塞ぐ。
「一度だけ」は呼び手が既に印のある仕事を呼ばないことで守る（`mark_overdue` と同じ構え）。
"""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import Cleared, Finished, FinishedPendingRecheck, StateUnion
from domain.events.job.draft_delivered import DraftDelivered
from domain.value_objects.people.clock import Clock

S = TypeVar("S", bound=StateUnion)


def deliver_drafts(job: Job[S], now: datetime) -> tuple[Job[S], DraftDelivered] | None:
    """承認を経た成果つきの仕事なら（同じ状態の仕事, 下書きが配達された）の対。

    それ以外は None——承認前・成果なしの下書きは配達の事実になれない。
    """
    if not isinstance(job.state, (Cleared, FinishedPendingRecheck, Finished)):
        return None
    if job.result_at is None:
        return None
    return job, DraftDelivered(at=now, by=Clock())
