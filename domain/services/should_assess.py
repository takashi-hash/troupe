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

from domain.values.job.assessment import Assessment
from domain.values.job.spent import Spent
from domain.values.rule.budget import Budget


def should_assess(
    assessments: Sequence[Assessment],
    stop_reasons: Sequence[str],
    spent: Spent,
    budget: Budget,
    retried: int,
    max_retries: int,
) -> bool:
    """書くべきなら真。材料が無ければ偽。書いたら偽（F6）。"""
    touched = spent.calls >= budget.calls or spent.seconds >= budget.seconds
    exhausted = retried >= max_retries
    if not (touched or exhausted or stop_reasons):
        return False
    return len(assessments) == 0
