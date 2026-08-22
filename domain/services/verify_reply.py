"""検める — `Reply` をどれに振り分けるか。

設計: 設計/仕事が回る筋道.md §2「仕様」・仕事とは何か.md 不変条件 I16。
| **`Reply` をどれに振り分けるか** | **`Reply`（印と本文）** ＋ 受け入れ基準の**必ず含む語** |
印が質問なら**質問**へ。印が成果で、本文が必ず含む語を**すべて含めば成果**へ。
**含まなければ見立て**へ——**名乗りを検めるのがここ**。印がどちらでもないなら**見立て**へ |

**印は自己申告——仕様が検める（I16 の後半）。** LLM の名乗りは鵜呑みにしない。
返るのは**検めたあとの印**——成果と名乗っても語が欠ければ見立てへ落ちる。
文字の照合だけ——だから何度でも同じ結果になる。
"""

from __future__ import annotations

from domain.values.job.reply import Mark, Reply
from domain.values.rule.criteria import AcceptanceCriteria


def verify(reply: Reply, criteria: AcceptanceCriteria) -> Mark:
    """検めたあとの印。質問はそのまま、成果は語が揃ってこそ、残りは見立てへ。"""
    if not criteria.opened:
        raise ValueError("開かれていない差し込みが仕様に届きました（写すときに開く）")
    if reply.mark is Mark.QUESTION:
        return Mark.QUESTION
    if reply.mark is Mark.RESULT and all(term in reply.body for term in criteria.required_terms):
        return Mark.RESULT
    return Mark.NEITHER
