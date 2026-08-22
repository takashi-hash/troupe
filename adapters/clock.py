"""時計 — いまを出す実装。

設計: 設計/どう作るか.md §4。
| **adapters** | **業務の規則** | 帳簿の実装・Port の実装・**腐敗防止層** |

domain は「いま」を引数で受け取り、取りに行くのは app の口だけ（`ClockPort`）。
その口にいまを注ぐのがここ。**UTC で aware な時刻**を返す——naive な時刻は
比べるたびに嘘をつくので、生まれる場所で潰す。
"""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """時計の実装 — いまを UTC で出す。判断はしない。"""

    def now(self) -> datetime:
        """いまの時刻。UTC で aware。"""
        return datetime.now(UTC)
