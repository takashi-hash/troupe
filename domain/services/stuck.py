"""行き詰まり — もう自力では進めないか。

設計: 設計/仕事が回る筋道.md §2「仕様」。
| **もう自力では進めないか** | 前に出した成果の中身 ＋ 止まった理由の列 ＋ やり直した回数 | 真なら `hand_over`（実行中から） |

**白黒の線（実装で決めた）**:
①**直近2回の止まった理由が同じ**なら真——やり直しても同じ壁に当たっている。
②**前に出した成果が無いまま、3回以上やり直した**なら真——成果の形すら出せていない。
それ以外は偽——材料が足りないうちは、人を呼ぶよりもう1回やらせるほうが安い。
事実の照合だけ——だから何度でも同じ結果になる。判断ではない。
"""

from __future__ import annotations

from collections.abc import Sequence


def is_stuck(previous_result: str | None, stop_reasons: Sequence[str], retried: int) -> bool:
    """真なら `hand_over`（実行中から）。"""
    if len(stop_reasons) >= 2 and stop_reasons[-1] == stop_reasons[-2]:
        return True
    return previous_result is None and retried >= 3
