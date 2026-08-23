"""定期訪問を集める — 取り決めの一覧を写す。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」。
| 定期訪問を集める | `gather_patterns` | 取り決めの一覧を写す | 読むだけ。書かない |
"""

from __future__ import annotations

from app.dto.pattern_row import PatternRow
from app.ports.emr_pattern_port import EmrPatternPort


def gather_patterns(patterns: EmrPatternPort) -> tuple[PatternRow, ...]:
    """取り決めの行の一覧。読むだけ——どこにも書かない。"""
    return patterns.read_all()
