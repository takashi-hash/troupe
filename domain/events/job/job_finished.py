"""終わった — 仕事が終点か確かめ待ちへ入った、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 終わった | 根拠の在りか、または確かめ期日 | `JobFinished` |

**終わったと言うには、根拠か確かめ期日が要る**（I5）——どちらか一方だけ。
両方持つ形も、両方欠く形も書けない。
"""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import model_validator

from domain.events.event import Event


class JobFinished(Event):
    """終わった。根拠があれば終点、無ければ確かめ期日つきの確かめ待ち。"""

    #: 根拠の在りか — 引用が取れたとき。
    evidence_at: str | None

    #: 確かめ期日 — 根拠が無いまま終えたとき。
    recheck_at: datetime | None

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if (self.evidence_at is None) == (self.recheck_at is None):
            raise ValueError(
                "終わったは根拠の在りかか確かめ期日の、どちらか一方だけを残します（I5）"
            )
        return self
