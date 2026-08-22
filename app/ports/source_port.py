"""源への口 — 腐敗防止層。

設計: 設計/仕事が回る筋道.md §4。
| `SourcePort` | Port | 源から読む。**源の言葉を業務の語へ翻訳**（腐敗防止層＝ACL）。
出口は**引用・読めなかった理由**の2つ——読めた中身は引用が兼ねる（**返す者の居ない出口は
置かない**） | **app** | adapters | `consult`・`submit`・**`confirm`**（根拠の引用を取る） |

**出口は domain の値ではない**——業務の一生に残る前の、読みの結果だから。
だから app のここに置く。引用だけは `Evidence` を運ぶ——**AI の言葉は根拠にならない**ので、
源から読んだ引用がここで根拠の形になってから中へ入る。
読めなければ理由が残る——**読めなければ `fail` へ**（§1 `consult`）の材料。
"""

from __future__ import annotations

from typing import Annotated, Literal, Protocol, Self

from pydantic import Field, model_validator

from domain.obligations import Value, not_blank
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.rule.source import Source


class Quote(Value):
    """引用 — 源から読んだ引用。`Evidence` を運ぶ——義務は `Evidence` が守る。"""

    kind: Literal["quote"] = "quote"
    evidence: Evidence


class Unreadable(Value):
    """読めなかった理由 — 理由なしでは落とせない。"""

    kind: Literal["unreadable"] = "unreadable"
    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.reason, "読めなかった理由")
        return self


#: 出口の2択 — 引用・読めなかった理由。**3つ目は無い**（読めた中身は引用が兼ねる）。
SourceOutcome = Annotated[Quote | Unreadable, Field(discriminator="kind")]


class SourcePort(Protocol):
    def read(self, source: Source) -> SourceOutcome:
        """源から読む。出口は2つだけ——どちらかを名乗って返る。"""
        ...
