"""使った量を積む — 実行中のまま、LLM を呼んだぶんの回数と秒を足す。

設計: 設計/仕事が回る筋道.md §1「AI が始めるもの」・仕事とは何か.md §6・不変条件 I14。
| 使った量を積む | `spend` | LLM を呼んだぶんの回数と秒を足す。**`consult` の中で呼ばれる** | 数えるだけ。**上限で止まる（I14）** |

**状態は変わらない**——遷移表の外で刻める例外のひとつ `SpentIncreased`。
積むと上限を超えるなら **ValueError（I14——積む前に止まる）**。`by` は担当。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import InProgress
from domain.events.job.spent_increased import SpentIncreased


def spend(
    job: Job[InProgress], calls: int, seconds: int, now: datetime
) -> tuple[Job[InProgress], SpentIncreased]:
    """積む。返るのは（実行中のままの仕事, 使った量が増えた）の対。"""
    event = SpentIncreased(at=now, by=job.state.assignee, calls=calls, seconds=seconds)
    next_spent = job.spent.plus(calls, seconds)
    if not next_spent.within(job.budget):
        raise ValueError("積むと使用上限を超えます（I14——積む前に止まる）")
    data = fields_of(job) | {"spent": next_spent}
    return Job[InProgress].model_validate(data), event
