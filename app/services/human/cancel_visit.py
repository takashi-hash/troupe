"""訪問を1回だけ休む — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」。
| 訪問を1回だけ休む | `cancel_visit` | その1回の予定だけを理由つきで中止に倒す。
取り決めは生きたまま——**この回は行かないと患者と決めたのが判断** |

理由なしでは休めない——なぜ行かなかったかは、あとで必ず問われる（F4）。
"""

from __future__ import annotations

from app.ports.emr_visit_port import EmrVisitPort
from app.services.refusal import Refusal


def cancel_visit(
    visits: EmrVisitPort, visit_id: str, reason: str, *, by: str
) -> Refusal | None:
    """通れば None。断られたら理由。"""
    if not by.strip():
        return Refusal(reason="No one is making this judgment — the name is blank")
    if not visit_id.strip():
        return Refusal(reason="Which visit? The id is blank")
    if not reason.strip():
        return Refusal(reason="A reason is required — a skipped visit must say why")
    なぜ = visits.cancel(visit_id.strip(), reason.strip())
    return None if なぜ is None else Refusal(reason=なぜ)
