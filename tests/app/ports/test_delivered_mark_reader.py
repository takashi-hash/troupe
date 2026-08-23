"""配達の印の読みの宣言の壊しかた。筋道 §4——刻んだ事実そのものが照合の材料。"""

from __future__ import annotations

from app.ports.delivered_mark_reader import DeliveredMarkReader
from domain.value_objects.job.job_id import JobId


class 印読みの偽物:
    def marked_ids(self) -> frozenset[JobId]:
        return frozenset({JobId(text="J-1")})


def test_宣言は名乗りだけで満たせる() -> None:
    読み: DeliveredMarkReader = 印読みの偽物()
    assert JobId(text="J-1") in 読み.marked_ids()
