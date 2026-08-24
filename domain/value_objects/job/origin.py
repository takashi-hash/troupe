"""作成元 — どこから生まれたか。**二度作らない鍵。**

設計: 設計/仕事とは何か.md §2「仕事」・§3・§4「仕事が持つもの」・不変条件 I3。
| `Origin` | 依頼発なら依頼の識別子、業務ルール発なら `RuleName`＋版の番号＋`Period` |
  空で作れたら赤／同じ中身が違う鍵を出したら赤 |

**同じ作成元から仕事は二度作られない（I3）。**
それを帳簿の一意の鍵で守るので、**同じ中身なら必ず同じ鍵の文字列**になる。
**版の番号も鍵の一部**——版が変われば、同じ対象期間でも別の仕事が生まれてよい。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.value_objects.calendar.period import Period
from domain.obligations import Value, not_blank
from domain.value_objects.rule.rule_name import RuleName


class Origin(Value):
    """作成元 — 立てた者が決める、二度作らないための鍵。"""

    key: str

    @classmethod
    def from_request(cls, request_id: str) -> Self:
        """依頼発 — 依頼の識別子から。"""
        not_blank(request_id, "依頼の識別子")
        return cls(key=f"request:{request_id}")

    @classmethod
    def from_rule(
        cls, rule_name: RuleName, version_number: int, period: Period,
        patient: str | None = None,
    ) -> Self:
        """業務ルール発 — 業務ルールの識別子＋版の番号＋対象期間から。

        患者ごとに展開する版（源に穴を持つ）は患者記号も鍵に入る——
        同じ週に患者が増えれば、その患者の分だけ追って作られる。
        """
        key = f"rule:{rule_name.text}/v{version_number}/{period.text}"
        if patient is None:
            return cls(key=key)
        not_blank(patient, "患者記号")
        return cls(key=f"{key}/{patient}")

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.key, "作成元の鍵")
        return self
