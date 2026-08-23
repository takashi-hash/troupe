"""月次請求を確定する — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1。
| 月次請求を確定する | `confirm_claim` | 1患者1月の請求を事実とする（月が終わってから）。
**確定した請求と算定行は書き換え不能**（診療録の錠） |
"""

from __future__ import annotations

from app.ports.emr_claim_port import EmrClaimPort
from app.services.refusal import Refusal


def confirm_claim(
    claims: EmrClaimPort, patient: str, month: str, *, by: str
) -> Refusal | None:
    """通れば None。旗が残る月・終わっていない月は口が断る。"""
    if not by.strip():
        return Refusal(reason="No one is making this judgment — the name is blank")
    if not patient.strip() or not month.strip():
        return Refusal(reason="Which patient, which month? Something is blank")
    なぜ = claims.confirm(patient, month, by)
    return None if なぜ is None else Refusal(reason=なぜ)
