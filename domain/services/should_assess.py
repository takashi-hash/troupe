"""見立てを書くべきか — いまこの仕事に見立てを書くべきか。

設計: 設計/仕事が回る筋道.md §2「仕様」・仕事とは何か.md 不変条件 I15。
| **いまこの仕事に見立てを書くべきか** | これまでの見立て ＋ 落ちた中身と止まった理由の列 ＋ **使った量と使用上限** ＋ **やり直した回数とやり直しの上限** | 真偽（F6——**同じ見立てを二度書かない**）。**上限に触れた・やり直しが尽きたときは必ず真**（I15） |

読む材料（落ちた中身と止まった理由）が無く、上限にも触れていなければ偽——
数字しか無いところに見立ては書けない。
材料があっても、見立てが既に在れば偽（F6——同じ見立てを二度書かない）。
上限に触れた・やり直しが尽きて、まだ見立てが無ければ**必ず真**（I15）——
書かれてはじめて I15 が満ち、それからは偽になる。
"""

from __future__ import annotations

from collections.abc import Sequence

from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.spent import Spent
from domain.value_objects.rule.budget import Budget


def should_assess(
    assessments: Sequence[Assessment],
    stop_reasons: Sequence[str],
    spent: Spent,
    budget: Budget,
    retried: int,
    max_retries: int,
) -> bool:
    """書くべきなら真。**上限に触れた・やり直しが尽きたときだけ**。書いたら偽（F6）。

    止まった理由が在るだけでは書かない——**時計がまだ仕分ける仕事は拾わない**
    （早く書くと、やり直し0回時点の古い見立てが残る。実機で起きた）。
    根拠なしで終わった仕事は状態そのものが引き金なので、巡回が状態で拾う
    （この仕様の材料に状態は無い）。
    """
    touched = spent.calls >= budget.calls or spent.seconds >= budget.seconds
    exhausted = retried >= max_retries
    if not (touched or exhausted):
        return False
    return len(assessments) == 0
