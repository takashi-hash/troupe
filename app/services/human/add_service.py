"""行為を足す — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1。
| 行為を足す | `add_service` | 署名前の訪問へ、その日行った行為・薬剤（点数表の行）と
数量を載せる。**署名で凍る**——事実の門はひとつ |
"""

from __future__ import annotations

from app.ports.emr_service_port import EmrServicePort
from app.services.refusal import Refusal


def add_service(
    services: EmrServicePort, visit_id: str, code: str, qty_text: str, *, by: str
) -> Refusal | None:
    """通れば None。数に読めない数量は断りに変える——エラーは投げない。"""
    if not by.strip():
        return Refusal(reason="No one is making this entry — the name is blank")
    if not visit_id.strip() or not code.strip():
        return Refusal(reason="Which visit, which item? Something is blank")
    try:
        qty = int(qty_text.strip() or "1")
    except ValueError:
        return Refusal(reason=f"Quantity is not a number: {qty_text}")
    if qty < 1:
        return Refusal(reason="Quantity must be at least 1")
    なぜ = services.add(visit_id, code, qty, by)
    return None if なぜ is None else Refusal(reason=なぜ)
