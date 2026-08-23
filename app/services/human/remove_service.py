"""行為を外す — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1。
| 行為を外す | `remove_service` | 署名前の訪問から行為を1行外す |
"""

from __future__ import annotations

from app.ports.emr_service_port import EmrServicePort
from app.services.refusal import Refusal


def remove_service(
    services: EmrServicePort, visit_id: str, code: str, *, by: str
) -> Refusal | None:
    """通れば None。署名済みからは外せない——断りは口が言う。"""
    if not by.strip():
        return Refusal(reason="No one is making this entry — the name is blank")
    if not visit_id.strip() or not code.strip():
        return Refusal(reason="Which visit, which item? Something is blank")
    なぜ = services.remove(visit_id, code, by)
    return None if なぜ is None else Refusal(reason=なぜ)
