"""やることの壊しかた。設計/仕事とは何か.md §3。

**版が「やること」を持つのが要。**
持たないと AI は何をすればよいか永久に知れない。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.rule.instruction import Instruction


def test_AI_が読んで何をするか分かる文を持つ() -> None:
    やること = Instruction(text="今月の訪問記録を数え、月次報告の下書きを作る")
    assert やること.text == "今月の訪問記録を数え、月次報告の下書きを作る"


def test_何行にわたってもよい() -> None:
    やること = Instruction(text="1. 源を読む\n2. 件数を数える\n3. 下書きを書く")
    assert "件数を数える" in やること.text


def test_やることの空な指示は作れない() -> None:
    for text in ("", "   ", "\n", "　"):
        with pytest.raises(ValidationError):
            Instruction(text=text)


def test_写したやることは元と等しい() -> None:
    版のやること = Instruction(text="今月の訪問記録を数える")
    仕事へ写したやること = Instruction(text=版のやること.text)
    assert 仕事へ写したやること == 版のやること


def test_写したあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        Instruction(text="今月の訪問記録を数える").text = "何もしない"  # type: ignore[misc]
