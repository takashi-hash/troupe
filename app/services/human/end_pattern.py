"""定期訪問を終える — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」。
| 定期訪問を終える | `end_pattern` | 取り決めに終わりの日を入れる。**列は消さない** |
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.emr_pattern_port import EmrPatternPort
from app.services.refusal import Refusal


def end_pattern(
    patterns: EmrPatternPort, clock: ClockPort, pattern_id: str, by: str
) -> Refusal | None:
    """今日づけで終える。通れば None。"""
    if not by.strip():
        return Refusal(reason="誰の判断かが空です")
    if not pattern_id.strip():
        return Refusal(reason="どの取り決めかが空です")
    なぜ = patterns.end(pattern_id.strip(), clock.now().date().isoformat())
    return None if なぜ is None else Refusal(reason=なぜ)
