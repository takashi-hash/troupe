"""差し戻す — 承認待ち・実行中・失敗した・終わった（確かめ待ち） → 着手できる。

設計: 設計/仕事とは何か.md §4「仕事が持つもの」・§6 遷移表・不変条件 I1・I7。
| 承認待ち | 着手できる | 差し戻す `send_back` | `SentBack` | **人** |
| 実行中 | 着手できる | 差し戻す `send_back` | `SentBack` | **人**（見立てを読んで） |
| 失敗した | 着手できる | 差し戻す `send_back` | `SentBack` | **人** |
| 終わった（確かめ待ち） | 着手できる | 差し戻す `send_back` | `SentBack` | **人** |

**人しか起こせない**（I7 公理の執行者）——`SendBack` の `by` の型が `Human` なので、
AI がこの手を呼ぶ行は型検査が赤にする。
**使った量とやり直した回数が 0 に戻る**——どの状態からでも（§4 持ちものの表が正本）。
行き先はどれも「着手できる」なので引数を union にする（overload は行き先が違うときだけ）。
着手できるは承認の欄を持たないので、承認を持ったまま戻る形は書けない。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import (
    AwaitingApproval,
    Failed,
    FinishedPendingRecheck,
    InProgress,
    Ready,
)
from domain.events.job.sent_back import SentBack
from domain.value_objects.job.send_back import SendBack
from domain.value_objects.job.spent import Spent


def send_back(
    job: Job[AwaitingApproval]
    | Job[InProgress]
    | Job[Failed]
    | Job[FinishedPendingRecheck],
    sb: SendBack,
    now: datetime,
) -> tuple[Job[Ready], SentBack]:
    """理由をつけて着手できるへ戻す。返るのは（着手できる仕事, 差し戻された）の対——I1 が型になる。"""
    data = fields_of(job) | {
        "state": Ready(),
        "spent": Spent(calls=0, seconds=0),
        "retried": 0,
    }
    return Job[Ready].model_validate(data), SentBack(at=now, by=sb.by, reason=sb.reason)
