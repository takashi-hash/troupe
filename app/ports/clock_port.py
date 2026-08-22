"""時刻への口。

設計: 設計/仕事が回る筋道.md §4。
| `ClockPort` | Port | いまの時刻を出す | **app** | adapters | **人・AI・時計のすべてと、今日の画面** |

domain は「いま」を引数で受け取る——取りに行くのは app のここだけ。
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    def now(self) -> datetime: ...
