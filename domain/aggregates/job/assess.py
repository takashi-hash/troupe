"""見立てを書く — 読んだ結果と理由を積む。**状態は変わらない。**

設計: 設計/仕事が回る筋道.md §1「AI が始めるもの」・仕事とは何か.md §6・不変条件 I13。
| 見立てを書く | `assess` | 読んだ結果と理由を積む。**担当でなくても書ける**（I13 の例外）——落ちた仕事・終わった仕事こそ見立てが要る。**状態を変えない** | **事実の報告と案。決めるのは人** |

遷移表の外で刻める3つの例外のひとつ（`AssessmentWritten`）——
**同じ状態の型を返す関数**として書く。返すのは（同じ状態, 出来事）の対。
**AI が起こす**——`by` の型が `Agent`。主語だが判断ではない。
見立ての本体は Store に積む——仕事は在りかも持たない。
"""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import StateUnion
from domain.events.job.assessment_written import AssessmentWritten
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.people.agent import Agent

S = TypeVar("S", bound=StateUnion)


def assess(
    job: Job[S], assessment: Assessment, by: Agent, now: datetime
) -> tuple[Job[S], AssessmentWritten]:
    """（同じ状態の仕事, 見立てが書かれた）の対。

    どの状態でも、担当でなくても書ける（I13 の例外）——
    落ちた仕事・終わった仕事こそ見立てが要る。
    """
    return job, AssessmentWritten(at=now, by=by, assessment=assessment)
