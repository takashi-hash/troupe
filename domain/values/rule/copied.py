"""写すものの束 — 版から仕事へ写す中身 ＋ 終えるまでの日数。

設計: 設計/仕事とは何か.md §4「仕事が持つもの」。

**版そのものは渡さない。** Repository が返すのは集約ルートだけなので、
`Rule` 集約が束を返し、仕事はそれを**写して**持つ——指すのではない。
版をまたいで読みに行くと、1回の書き込みで2つの集約を触ることになる。

**集約の境界を渡るのは、この束だけ。** だから版とは別の概念。
"""

from __future__ import annotations

from domain.values.calendar.cycle import Cycle
from domain.obligations import Value
from domain.values.people.owner import Owner
from domain.values.rule.budget import Budget
from domain.values.rule.criteria import AcceptanceCriteria
from domain.values.rule.instruction import Instruction
from domain.values.rule.source import Source


class Copied(Value):
    """写すものの束。日数だけは仕事に残らない——期日になって消える。"""

    #: やること — AI が読む指示。
    instruction: Instruction

    #: 受け入れ基準 — **写した時点で `{対象期間}` は開かれている。**
    criteria: AcceptanceCriteria

    #: 周期 — 確かめ期日を先へ送る幅になる。
    cycle: Cycle

    #: 受け持ちの人 — 誰が承認し、誰が質問を受けるか。
    owner: Owner

    #: 使用上限 — どこで止まるか。
    budget: Budget

    #: 源 — AI がどこを読みに行くか。
    source: Source

    #: やり直しの上限 — 何回までやり直してよいか。
    max_retries: int

    #: 終えるまでの日数 — **仕事は持たない。** 期日になって消える。
    days: int
