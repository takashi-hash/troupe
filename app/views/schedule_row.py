"""予定の行 — 先に何が来るかの画面が見る、文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 予定の行 | 業務ルールの名・やること・版の番号・有効な版・次の対象期間・押せること |

**画面に届くのは文字と ID だけ。振る舞いを持たない。** ただの入れ物。
押せることは 版を積む・有効にする（人なら誰でも。仕事の操作ではないので今日には出ない）。
"""

from __future__ import annotations

from domain.obligations import Value


class ScheduleRow(Value):
    """予定の行 — 1業務ルール1行。"""

    rule: str
    instruction: str
    version: int
    #: 有効な版 — まだ有効にしていなければ空。
    active_version: int | None
    #: 次の対象期間 — 有効な版が無ければ空（作られる仕事が無い）。
    next_period: str | None
    actions: tuple[str, ...]
