"""期日を過ぎた — 期日を越えたことに一度だけ印が残った、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 期日を過ぎた | — | `DueDatePassed` |

**時計が主語。** 足して残るものは無い——誰が・いつは共通が持つ。
状態は変えない——遷移表の外で刻める例外のひとつ。
"""

from __future__ import annotations

from domain.events.event import Event


class DueDatePassed(Event):
    """期日を過ぎた。日付の比べだけ——判断を含まない。"""
