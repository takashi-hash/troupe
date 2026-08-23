"""下書き受けの口の宣言の壊しかた。筋道 §4——draft としてだけ置く。"""

from __future__ import annotations

from app.ports.emr_draft_port import EmrDraftPort


class 下書き受けの偽物:
    def deposit(self, job_id: str, patient_code: str, body: str) -> bool:
        return True


def test_宣言は名乗りだけで満たせる() -> None:
    口: EmrDraftPort = 下書き受けの偽物()
    assert 口.deposit("J-1", "P-001", "draft") is True
