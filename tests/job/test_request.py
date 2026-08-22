"""依頼の壊しかた。設計/仕事とは何か.md §3。

**頼んだ人・時刻・中身の3つで、起きた事実を固定する。**
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from domain.job.request import Request
from domain.people.human import Human

頼んだ人 = Human(name="座長")
時刻 = datetime(2026, 8, 22, 9, 0)


def test_依頼は作れる() -> None:
    依頼 = Request(by=頼んだ人, at=時刻, body="八月分の突合をやって")
    assert 依頼.by == 頼んだ人
    assert 依頼.at == 時刻
    assert 依頼.body == "八月分の突合をやって"


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    一つ目 = Request(by=頼んだ人, at=時刻, body="突合をやって")
    二つ目 = Request(by=頼んだ人, at=時刻, body="突合をやって")
    assert 一つ目 == 二つ目
    assert {一つ目: "依頼発"}[二つ目] == "依頼発"


def test_作ったあと書き換えられない() -> None:
    依頼 = Request(by=頼んだ人, at=時刻, body="突合をやって")
    with pytest.raises(ValidationError):
        依頼.body = "別のこと"  # type: ignore[misc]


def test_頼んだ人が欠けたら作れない() -> None:
    with pytest.raises(ValidationError):
        Request(at=時刻, body="突合をやって")  # type: ignore[call-arg]


def test_時刻が欠けたら作れない() -> None:
    with pytest.raises(ValidationError):
        Request(by=頼んだ人, body="突合をやって")  # type: ignore[call-arg]


def test_中身が欠けたら作れない() -> None:
    with pytest.raises(ValidationError):
        Request(by=頼んだ人, at=時刻)  # type: ignore[call-arg]


def test_中身が空なら作れない() -> None:
    for text in ("", "   ", "\n"):
        with pytest.raises(ValidationError):
            Request(by=頼んだ人, at=時刻, body=text)


def test_名の空な人は依頼できない() -> None:
    with pytest.raises(ValidationError):
        Request(by=Human(name=""), at=時刻, body="突合をやって")
