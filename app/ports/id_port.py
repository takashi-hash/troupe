"""識別子への口。

設計: 設計/仕事が回る筋道.md §4。
| `IdPort` | Port | 新しい識別子を振る | **app** | adapters | `request`・`create` |

`JobId` は**立てた者が振る**——採番はファクトリの外（§3）。
振る道具は外のもの——だから Port。実装は adapters、**注ぐのは main.py だけ。**
"""

from __future__ import annotations

from typing import Protocol


class IdPort(Protocol):
    def new_id(self) -> str:
        """新しい識別子を1つ振る。文字で返す——値に包むのは立てた者。"""
        ...
