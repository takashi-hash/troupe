"""整えた応答の壊しかた。設計/仕事とは何か.md §3・不変条件 I16。

**生の応答が帳簿へ入らない。** 印は自己申告——仕様が検める。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.job.reply import Mark, Reply


def test_印と本文を持つ応答は作れる() -> None:
    応答 = Reply(mark=Mark.RESULT, body="8月分の請求は42件でした")
    assert 応答.mark is Mark.RESULT
    assert 応答.body == "8月分の請求は42件でした"


def test_印は成果と質問とどちらでもないの3つだけ() -> None:
    assert set(Mark) == {Mark.RESULT, Mark.QUESTION, Mark.NEITHER}


def test_4つ目の印は作れない() -> None:
    for text in ("assessment", "evidence", "成果", ""):
        with pytest.raises(ValueError):
            Mark(text)


def test_4つ目の印を名乗った応答は作れない() -> None:
    with pytest.raises(ValidationError):
        Reply(mark="assessment", body="源が見つかりません")  # type: ignore[arg-type]


def test_印の無い応答は作れない() -> None:
    with pytest.raises(ValidationError):
        Reply(body="8月分の請求は42件でした")  # type: ignore[call-arg]


def test_本文の無い応答は作れない() -> None:
    with pytest.raises(ValidationError):
        Reply(mark=Mark.QUESTION)  # type: ignore[call-arg]


def test_本文が空な応答は作れない() -> None:
    for text in ("", "   ", "\n\t"):
        with pytest.raises(ValidationError):
            Reply(mark=Mark.QUESTION, body=text)


def test_質問の印も本文が空なら作れない() -> None:
    with pytest.raises(ValidationError):
        Reply(mark=Mark.NEITHER, body="")


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    応答 = Reply(mark=Mark.QUESTION, body="どの源を読めばよいですか")
    assert 応答 == Reply(mark=Mark.QUESTION, body="どの源を読めばよいですか")
    assert {応答: "尋ねる"}[Reply(mark=Mark.QUESTION, body="どの源を読めばよいですか")] == "尋ねる"


def test_作ったあと書き換えられない() -> None:
    応答 = Reply(mark=Mark.QUESTION, body="どの源を読めばよいですか")
    with pytest.raises(ValidationError):
        応答.mark = Mark.RESULT  # type: ignore[misc]
