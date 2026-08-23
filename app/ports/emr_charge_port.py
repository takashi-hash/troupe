"""算定の導出の口。

設計: 設計/仕事が回る筋道.md §4。
| `EmrChargePort` | Port | 署名済みの訪問と行為から、算定行と請求の下書きを導出して置く。
**旗を裁く・確定する口は無い**——確定済みの月に書く道も無い | **app** | adapters | `derive_charges` |
"""

from __future__ import annotations

from typing import Protocol


class EmrChargePort(Protocol):
    def derive(self) -> tuple[str, ...]:
        """まだ無い算定行と請求の下書きを作り、作った行の名を返す。何度回しても同じ。"""
        ...
