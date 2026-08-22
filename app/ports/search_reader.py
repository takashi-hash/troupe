"""検索の読み。

設計: 設計/仕事が回る筋道.md §4・人に見えるもの.md §1「検索」・§2「検索の行」。
| `SearchReader` | Reader | 絞り込みの条件（**状態は識別子に写してから**）で仕事の行を引く
——**終わったものも含めて**（F1） | **app** | adapters | `gather_search` |

**Reader の返す型は渡す先で決まる**——渡る先は画面なので、**文字と ID だけ**。
状態の語→識別子の橋は app（`gather_search`）——ここに届くのは識別子。
空の欄は絞らない。
"""

from __future__ import annotations

from typing import Protocol

from domain.obligations import Value


class SearchHit(Value):
    """検索の材料 — 仕事1件ぶん。文字と ID だけ。"""

    #: 仕事の識別子。
    id: str

    #: 見出しの材料 — 業務ルールと対象期間（依頼発は空）、やること。
    rule: str | None
    period: str | None
    instruction: str

    #: 状態の識別子（語に写すのは app）・期日・担当の名。
    state_name: str
    due: str
    assignee_name: str | None


class SearchReader(Protocol):
    def read(
        self,
        keyword: str | None,
        state_name: str | None,
        rule: str | None,
        assignee: str | None,
    ) -> tuple[SearchHit, ...]:
        """条件に合う仕事をぜんぶ——終わったものも含めて。空の条件は絞らない。"""
        ...
