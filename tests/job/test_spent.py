"""使った量の壊しかた。設計/仕事とは何か.md §3・§4・I14。

**上限とは別の値。** 使った量は0から積むだけで、収まっているかを言えるだけ。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.job.spent import Spent
from domain.rule.budget import Budget


def test_仕事は使った量0で生まれる() -> None:
    生まれたて = Spent(calls=0, seconds=0)
    assert (生まれたて.calls, 生まれたて.seconds) == (0, 0)


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert Spent(calls=3, seconds=12) == Spent(calls=3, seconds=12)
    assert {Spent(calls=3, seconds=12): "実行中"}[Spent(calls=3, seconds=12)] == "実行中"


def test_使った量と使用上限は別の値() -> None:
    assert Spent(calls=1, seconds=1) != Budget(calls=1, seconds=1)


def test_負の回数では作れない() -> None:
    with pytest.raises(ValidationError):
        Spent(calls=-1, seconds=0)


def test_負の秒では作れない() -> None:
    with pytest.raises(ValidationError):
        Spent(calls=0, seconds=-1)


def test_積むと新しい値が返り_もとは変わらない() -> None:
    もと = Spent(calls=3, seconds=12)
    積んだ = もと.plus(1, 4)
    assert 積んだ == Spent(calls=4, seconds=16)
    assert もと == Spent(calls=3, seconds=12)


def test_負になる積みかたはできない() -> None:
    with pytest.raises(ValidationError):
        Spent(calls=0, seconds=0).plus(-1, 0)


def test_上限に収まっていれば収まっていると言える() -> None:
    assert Spent(calls=3, seconds=12).within(Budget(calls=20, seconds=600))


def test_上限と同じならまだ収まっている() -> None:
    assert Spent(calls=20, seconds=600).within(Budget(calls=20, seconds=600))


def test_回数が上限を超えたら収まっていない() -> None:
    assert not Spent(calls=21, seconds=12).within(Budget(calls=20, seconds=600))


def test_秒が上限を超えたら収まっていない() -> None:
    assert not Spent(calls=3, seconds=601).within(Budget(calls=20, seconds=600))
