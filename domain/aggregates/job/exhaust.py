"""使い切る — 実行中 → 失敗した（使用上限に達した）。

設計: 設計/仕事とは何か.md §6 遷移表・仕事が回る筋道.md §1「AI が始めるもの」。
| 実行中 | 失敗した | **使い切る** `exhaust` | `JobFailed`（使用上限に達した） | AI（`spend` が I14 で止めたとき） |

**数が上限に触れただけ**——判断を含まない。`by` は担当。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import Failed, InProgress
from domain.events.job.job_failed import JobFailed

#: 落ちた中身 — 使い切りは、いつもこの言葉で残る。
EXHAUSTED = "使用上限に達した"


def exhaust(job: Job[InProgress], now: datetime) -> tuple[Job[Failed], JobFailed]:
    """使用上限に達したことを残して失敗したへ。返るのは対——I1 が型になる。"""
    data = fields_of(job) | {"state": Failed(fallen=EXHAUSTED)}
    return Job[Failed].model_validate(data), JobFailed(
        at=now, by=job.state.assignee, fallen=EXHAUSTED
    )
