"""見立てが書かれた — AI が読んだ結果と、そう読んだ理由が残った、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| **見立てが書かれた** | 読んだ中身と、そう読んだ理由 | `AssessmentWritten` |

**AI が主語だが判断ではない**——事実の報告と案で、受けて決めるのは人。
状態は変えない——遷移表の外で刻める3つの例外のひとつ。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.value_objects.job.assessment import Assessment


class AssessmentWritten(Event):
    """見立てが書かれた。AI から人への道の1つ。"""

    #: 見立て — 読んだ結果と、そう読んだ理由。
    assessment: Assessment
