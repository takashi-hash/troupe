"""成果が出された — 担当が成果を積んだ、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 成果が出された | 成果の在りか ＋ **根拠の在りか** | `ResultSubmitted` |

**源をもう一度読んで引用が取れれば**根拠も積む。取れなければ根拠なしで出す
——だから根拠の在りかだけが空でありうる。
"""

from __future__ import annotations

from domain.events.event import Event


class ResultSubmitted(Event):
    """成果が出された。出したら書き換えない。"""

    #: 成果の在りか — 積んだ Store が返したもの。
    result_at: str

    #: 根拠の在りか — 引用が取れたときだけ。
    evidence_at: str | None
