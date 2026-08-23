"""訪問の終わりの口の宣言の壊しかた。筋道 §4——人の操作だけが呼ぶ。"""

from __future__ import annotations

from app.ports.emr_visit_port import EmrVisitPort


class 訪問の終わりの偽物:
    def sign(self, visit_id: str, signer: str, s: str, o: str, a: str, p: str,
             draft_id: str | None) -> str | None:
        return None

    def cancel(self, visit_id: str, reason: str, by: str) -> str | None:
        return None


def test_宣言は名乗りだけで満たせる() -> None:
    口: EmrVisitPort = 訪問の終わりの偽物()
    assert 口.sign("7", "Dr-A", "s", "o", "a", "p", None) is None
    assert 口.cancel("7", "family away", "Director") is None
