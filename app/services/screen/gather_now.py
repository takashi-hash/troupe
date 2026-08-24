"""いまを集める — この座はいま動いているのか？

設計: 設計/仕事が回る筋道.md §1・人に見えるもの.md §1「いま」・§2「いまの眺め」。

**読むだけ。数えて写すだけ。予告しない——最後の脈の事実だけ。**
生の帯（SSE）は器がこの読みを繰り返すだけ——開きっぱなしの導出。
"""

from __future__ import annotations

from app.dto.now_view import NowView
from app.ports.history_reader import HistoryReader
from app.ports.today_reader import TodayReader
from app.services.screen.gather_history import heading

#: 環の段への割り当て——状態の識別子はここでだけ段になる。
_待ち = ("Created", "Ready")
_作業中 = ("InProgress",)
_検査中 = ("Submitted", "FinishedPendingRecheck", "Failed")
_人待ち = ("AwaitingApproval", "AwaitingAnswer")


def gather_now(today: TodayReader, history: HistoryReader) -> NowView:
    """帳簿のいまを写す。段ごとの数・作業中の仕事・最後の脈の時刻。"""
    queued = checking = waiting = 0
    working: list[tuple[str, str]] = []
    for m in today.read_all():
        if m.state_name in _待ち:
            queued += 1
        elif m.state_name in _作業中:
            working.append(
                (
                    m.id.text,
                    heading(
                        m.rule.text if m.rule is not None else None,
                        m.period.text if m.period is not None else None,
                        m.request_head or m.instruction.text,
                    ),
                )
            )
        elif m.state_name in _検査中:
            checking += 1
        elif m.state_name in _人待ち:
            waiting += 1

    beat_at: str | None = None
    for e in history.read_latest(50):
        if e.by_kind == "clock":
            beat_at = e.at
            break

    return NowView(
        queued=queued,
        working=tuple(working),
        checking=checking,
        waiting=waiting,
        beat_at=beat_at,
    )
