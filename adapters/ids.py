"""識別子 — 新しい識別子を振る実装。

設計: 設計/どう作るか.md §4。
| **adapters** | **業務の規則** | 帳簿の実装・Port の実装・**腐敗防止層** |

`JobId` は立てた者が振る——振る道具は外のもの（`IdPort`）。
その口に乱数を注ぐのがここ。文字で返し、値に包むのは立てた者。
"""

from __future__ import annotations

from uuid import uuid4


class UuidIds:
    """識別子の実装 — uuid4 の短い形（区切りなしの16進）を振る。"""

    def new_id(self) -> str:
        """新しい識別子を1つ振る。呼ぶたびに違う、空でない文字。"""
        return uuid4().hex
