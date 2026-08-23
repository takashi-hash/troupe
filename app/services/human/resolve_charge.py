"""旗の行を裁く — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1。
| 旗の行を裁く | `resolve_charge` | 機械が旗を立てた算定行を、**理由をつけて通す**
（上限の特例——摘要の写し）か、落とす。**例外の適用こそ判断** |
"""

from __future__ import annotations

from app.ports.emr_claim_port import EmrClaimPort
from app.services.refusal import Refusal


def resolve_charge(
    claims: EmrClaimPort, charge_id: str, action: str, reason: str, *, by: str
) -> Refusal | None:
    """allow は理由必須——理由の無い特例は摘要に書けない。通れば None。"""
    if not by.strip():
        return Refusal(reason="No one is making this judgment — the name is blank")
    if action not in ("allow", "drop"):
        return Refusal(reason=f"Unknown ruling: {action}")
    if action == "allow" and not reason.strip():
        return Refusal(reason="An exception needs its reason — that is what goes on the claim")
    なぜ = claims.resolve(charge_id, action, reason.strip(), by)
    return None if なぜ is None else Refusal(reason=なぜ)
