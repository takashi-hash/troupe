"""既にある作成元の鍵の読み。

設計: 設計/仕事が回る筋道.md §4。
| `OriginReader` | Reader | 既にある仕事の作成元の鍵を読む | **app** | adapters | `create` |

`reconcile` の「既にある作成元の鍵の列」へそのまま渡る——
鍵は `Origin` が出すものと同じ形なので、同じ中身なら必ず同じ鍵に当たる（I3）。
"""

from __future__ import annotations

from typing import Protocol


class OriginReader(Protocol):
    def keys(self) -> frozenset[str]:
        """既にある仕事の作成元の鍵をぜんぶ。二度作らないための照合の材料。"""
        ...
