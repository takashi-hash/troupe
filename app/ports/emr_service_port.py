"""行為の口。

設計: 設計/仕事が回る筋道.md §4。
| `EmrServicePort` | Port | 署名前の訪問に行為を載せる・外す。**人の操作だけが呼ぶ** |
**app** | adapters | `add_service`・`remove_service` |

署名済み・中止済みの訪問には断り——事実の門はひとつ（署名）。
"""

from __future__ import annotations

from typing import Protocol


class EmrServicePort(Protocol):
    def add(self, visit_id: str, code: str, qty: int, by: str) -> str | None:
        """載せる。通れば None、断られたら理由の文字。"""
        ...

    def remove(self, visit_id: str, code: str) -> str | None:
        """外す。通れば None、断られたら理由の文字。"""
        ...
