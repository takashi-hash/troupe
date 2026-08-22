"""版 — 業務ルールの1つの姿。**積むだけ。**。

設計: 設計/仕事とは何か.md §2「決まり」・§3・§4「仕事が持つもの」・§7「禁止値」。
| `Version` | 番号は1以上。**やること・受け入れ基準・周期・終えるまでの日数・使用上限・
受け持ちの人・源・やり直しの上限**を必ず持つ | どれか欠けて作れたら赤 |
| **やることの空な版** | `Version` |

**版が「やること」を持つのが要。**
持たないと **AI は何をすればよいか永久に知れない。**

**版そのものは渡さない。** Repository が返すのは集約ルートだけなので、
`Rule` 集約が「写すものの束」（**共通の持ちもの ＋ 終えるまでの日数**）を返す。
日数は仕事が持たない——期日になって消える。

**写すのであって、指すのではない。** 版をまたいで読みに行くと、
1回の書き込みで2つの集約を触ることになる。だから写すときに
`AcceptanceCriteria` の `{対象期間}` を `Period` で開く——
開かれていない `{` が検査に届いたら、機械は幻の語を探すことになる。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.obligations import Value
from domain.value_objects.people.owner import Owner
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.copied import Copied
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.source import Source


class Version(Value):
    """版 — 業務ルールの1つの姿。**積むだけ。** 減らせない・書き換えられない。"""

    #: 版の番号 — 1以上。作成元の鍵の一部になる。
    number: int

    #: やること — **これが無いと AI は何をすればよいか永久に知れない。**
    instruction: Instruction

    #: 受け入れ基準 — 検査が何を見るか。`{対象期間}` を書ける。
    criteria: AcceptanceCriteria

    #: 周期 — いつ・どの対象期間の仕事を作るか。
    cycle: Cycle

    #: 終えるまでの日数 — 1以上。起点の時刻に足して期日にする。
    days: int

    #: 使用上限 — 暴走を止める安全弁。
    budget: Budget

    #: 受け持ちの人 — **版が決める。** AI は受け持ちの人になれない。
    owner: Owner

    #: 源 — AI が読みに行く先。
    source: Source

    #: やり直しの上限 — 0以上。0なら一度もやり直さない。
    max_retries: int

    def copy_for(self, period: Period | None) -> Copied:
        """写すものの束を返す。**そのとき受け入れ基準の `{対象期間}` を開く。**

        対象期間が無い（依頼発）なら開かない——開く相手が居ない。
        """
        return Copied(
            instruction=self.instruction,
            criteria=self.criteria.expand(period) if period is not None else self.criteria,
            cycle=self.cycle,
            owner=self.owner,
            budget=self.budget,
            source=self.source,
            max_retries=self.max_retries,
            days=self.days,
        )

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.number < 1:
            raise ValueError("版の番号は1以上です")
        if self.days < 1:
            raise ValueError("終えるまでの日数は1以上です")
        if self.max_retries < 0:
            raise ValueError("やり直しの上限は0以上です")
        return self
