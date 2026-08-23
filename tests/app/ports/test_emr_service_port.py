"""行為の口の宣言の壊しかた。筋道 §4——人の操作だけが呼ぶ。"""

from __future__ import annotations

from app.ports.emr_service_port import EmrServicePort


class 行為の口の偽物:
    def add(self, visit_id: str, code: str, qty: int, by: str) -> str | None:
        return None

    def remove(self, visit_id: str, code: str, by: str) -> str | None:
        return None


def test_宣言は名乗りだけで満たせる() -> None:
    口: EmrServicePort = 行為の口の偽物()
    assert 口.add("31", "NP03", 1, "Dr-A") is None
    assert 口.remove("31", "NP03", "Dr-A") is None
