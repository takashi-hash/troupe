"""仕事が配られた — 作られた仕事が着手できるへ出た、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 仕事が配られた | — | `JobHandedOut` |

足して残るものは無い——誰が・いつは共通が持つ。
"""

from __future__ import annotations

from domain.events.event import Event


class JobHandedOut(Event):
    """仕事が配られた。ここから AI が取りに来られる。"""
