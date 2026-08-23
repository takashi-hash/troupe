"""案内の口の宣言の壊しかた。筋道 §4。"""

from __future__ import annotations

from app.ports.guide_port import GuidePort


class 案内の偽物:
    def answer(
        self,
        question: str,
        digest: str,
        history: tuple[tuple[str, str], ...],
    ) -> str:
        return ""


def test_宣言は名乗りだけで満たせる() -> None:
    口: GuidePort = 案内の偽物()
    assert 口.answer("q", "", ()) == ""
