"""仕事の識別子の壊しかた。設計/仕事とは何か.md §3・§7。

**前後の空白を許すと、目には同じ識別子が二つになる。**
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.job.job_id import JobId


def test_識別子は作れる() -> None:
    assert JobId(text="J-0001").text == "J-0001"


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert JobId(text="J-0001") == JobId(text="J-0001")
    assert {JobId(text="J-0001"): "一件目"}[JobId(text="J-0001")] == "一件目"


def test_あとから変えられない() -> None:
    with pytest.raises(ValidationError):
        JobId(text="J-0001").text = "J-0002"  # type: ignore[misc]


def test_空の識別子は作れない() -> None:
    for text in ("", "   ", "\t\n"):
        with pytest.raises(ValidationError):
            JobId(text=text)


def test_前に空白のある識別子は作れない() -> None:
    with pytest.raises(ValidationError):
        JobId(text=" J-0001")


def test_後ろに空白のある識別子は作れない() -> None:
    with pytest.raises(ValidationError):
        JobId(text="J-0001 ")


def test_改行やタブが前後にある識別子は作れない() -> None:
    for text in ("\tJ-0001", "J-0001\n"):
        with pytest.raises(ValidationError):
            JobId(text=text)


def test_中の空白は識別子の一部として残る() -> None:
    assert JobId(text="J 0001").text == "J 0001"
