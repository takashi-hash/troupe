"""成果の壊しかた。設計/仕事とは何か.md §3。

**在りかは持たない。** 積んだ Store が返し、仕事が持つ。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.job.result import Result


def test_中身を持つ成果は作れる() -> None:
    assert Result(body="8月分の請求書を3件作りました").body == "8月分の請求書を3件作りました"


def test_中身の空な成果は作れない() -> None:
    for text in ("", "   ", "\n\t"):
        with pytest.raises(ValidationError):
            Result(body=text)


def test_成果は在りかの欄を持たない() -> None:
    with pytest.raises(ValidationError):
        Result(body="8月分の請求書", location="results/2026-08")  # type: ignore[call-arg]


def test_出したあと差し替えられない() -> None:
    with pytest.raises(ValidationError):
        Result(body="8月分の請求書").body = "9月分の請求書"  # type: ignore[misc]


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert Result(body="8月分の請求書") == Result(body="8月分の請求書")
    assert {Result(body="8月分の請求書"): "提出済み"}[Result(body="8月分の請求書")] == "提出済み"
