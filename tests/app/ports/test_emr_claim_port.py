"""請求の裁きと確定の口の宣言の壊しかた。筋道 §4。"""

from __future__ import annotations

from app.ports.emr_claim_port import EmrClaimPort


class 請求の口の偽物:
    def resolve(self, charge_id: str, action: str, reason: str, by: str) -> str | None:
        return None

    def confirm(self, patient: str, month: str, by: str) -> str | None:
        return None


def test_宣言は名乗りだけで満たせる() -> None:
    口: EmrClaimPort = 請求の口の偽物()
    assert 口.resolve("17", "allow", "acute exacerbation", "Director") is None
    assert 口.confirm("P-001", "2026-07", "Director") is None
