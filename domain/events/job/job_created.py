"""仕事が作られた — 頼まれてから終わるまでの1件が生まれた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 仕事が作られた | どの業務ルールの、どの版の、どの対象期間 | `JobCreated` |

業務ルール発なら**三つ揃い**、依頼発なら**三つとも空**——片方だけの形は書けない。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event
from domain.values.calendar.period import Period
from domain.values.rule.rule_name import RuleName


class JobCreated(Event):
    """仕事が作られた。依頼発でも業務ルール発でも、生まれの記録はこの1つ。"""

    #: どの業務ルールの — 業務ルール発のみ。
    rule_name: RuleName | None

    #: どの版の — 業務ルール発のみ。
    version: int | None

    #: どの対象期間 — 業務ルール発のみ。
    period: Period | None

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        trio = (self.rule_name, self.version, self.period)
        if any(x is not None for x in trio) and not all(x is not None for x in trio):
            raise ValueError(
                "どの業務ルールの・どの版の・どの対象期間は、業務ルール発なら三つ揃い、依頼発なら三つとも空です"
            )
        return self
