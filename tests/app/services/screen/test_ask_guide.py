"""案内に答えるの壊しかた。律速はここ・空の問いは押していないのと同じ。"""

from __future__ import annotations

from app.services.screen.ask_guide import (
    FALLBACK,
    HISTORY_LIMIT,
    QUESTION_LIMIT,
    ask_guide,
)


class 案内の偽物:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    def answer(
        self,
        question: str,
        digest: str,
        history: tuple[tuple[str, str], ...],
    ) -> str:
        self.asked = question
        self.digest = digest
        self.history = history
        return self._reply


def test_問いと写しがそのまま口へ渡る() -> None:
    口 = 案内の偽物("Open /day and sign the P-003 visit.")
    答え = ask_guide(口, "What needs me today?", "digest here", ())
    assert 答え == "Open /day and sign the P-003 visit."
    assert 口.asked == "What needs me today?"
    assert 口.digest == "digest here"


def test_空の問いは何も返さない() -> None:
    口 = 案内の偽物("should not be called")
    assert ask_guide(口, "   ", "digest", ()) == ""
    assert not hasattr(口, "asked")


def test_長すぎる問いは律速で切られる() -> None:
    口 = 案内の偽物("ok")
    ask_guide(口, "a" * (QUESTION_LIMIT + 100), "", ())
    assert len(口.asked) == QUESTION_LIMIT


def test_往復は直近だけが渡る() -> None:
    口 = 案内の偽物("ok")
    往復 = tuple((f"q{i}", f"a{i}") for i in range(HISTORY_LIMIT + 2))
    ask_guide(口, "q", "", 往復)
    assert 口.history == 往復[-HISTORY_LIMIT:]


def test_口が黙ったら断りの文言になる() -> None:
    口 = 案内の偽物("")
    assert ask_guide(口, "q", "", ()) == FALLBACK
