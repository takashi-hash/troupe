"""業務ルールの一覧の読み。

設計: 設計/仕事が回る筋道.md §4・人に見えるもの.md §2。
| `RuleReader` | Reader | 業務ルールの一覧（名・版の番号・有効な版・やること） | **app** |
adapters | 予定の画面 |

**Reader の返す型は渡す先で決まる**——渡る先は画面なので、**文字と ID だけ**。
次の対象期間は `reconcile` が、押せることは仕様が出す——ここでは運ばない。
"""

from __future__ import annotations

from typing import Protocol, Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class RuleLine(Value):
    """業務ルールの1行 — 名・版の番号・有効な版・やること。"""

    #: 業務ルールの名。
    name: str

    #: 版の番号 — いちばん新しい版の番号。
    version_number: int

    #: 有効な版の番号。まだ有効な版が無ければ None。
    active_version: int | None

    #: やること — AI が何をするか。
    instruction: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.name, "業務ルールの名")
        not_blank(self.instruction, "やること")
        return self


class RuleReader(Protocol):
    def read_all(self) -> tuple[RuleLine, ...]:
        """業務ルールの一覧。予定の画面が並べる。"""
        ...
