"""見立て — AI が状況を読んだ結果と理由。

設計: 設計/仕事とは何か.md §2「仕事」・§3・公理「判断は人間」。
| `Assessment` | 読んだ結果と、**そう読んだ理由**を両方持つ | 理由なしで作れたら赤 |

**判断ではない。** 事実の報告と案であって、受けて決めるのは人。
**見立てが無いと AI は数字しか出せない**——「20回使い切りました」ではなく
「20回とも同じ理由で落ちました。源の在りかが変わった可能性が高い」と言えること。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class Assessment(Value):
    """見立て — 読んだ結果と、そう読んだ理由。**AI が主語だが、判断ではない。**"""

    finding: str
    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.finding, "見立ての読んだ結果")
        not_blank(self.reason, "見立ての理由")
        return self
