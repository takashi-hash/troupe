"""差し戻しの壊しかた。設計/仕事とは何か.md §3・§7・I7。

**理由が空でない。** 理由なしで作れたら赤。
**誰がの型が `Human`**——AI の手からこの事実が組めない（I7）。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.job.send_back import SendBack
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.human import Human

座長 = Human(name="座長")


def test_誰がと理由を持つ差し戻しは作れる() -> None:
    差し戻し = SendBack(by=座長, reason="件数が源と合っていません。8月分をもう一度数えてください")
    assert 差し戻し.by == 座長
    assert 差し戻し.reason == "件数が源と合っていません。8月分をもう一度数えてください"


def test_理由の無い差し戻しは作れない() -> None:
    with pytest.raises(ValidationError):
        SendBack(by=座長)  # type: ignore[call-arg]


def test_誰がの無い差し戻しは作れない() -> None:
    with pytest.raises(ValidationError):
        SendBack(reason="件数が合っていません")  # type: ignore[call-arg]


def test_AIからは差し戻しが組めない() -> None:
    """I7——誰がの型が `Human`。"""
    with pytest.raises(ValidationError):
        SendBack(by=Agent(name="一号"), reason="件数が合っていません")  # type: ignore[arg-type]


def test_理由の空な差し戻しは作れない() -> None:
    for text in ("", "   ", "\n\t", "　"):
        with pytest.raises(ValidationError):
            SendBack(by=座長, reason=text)


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        SendBack(by=座長, reason="件数が合っていません", urgent=True)  # type: ignore[call-arg]


def test_決めたあと書き換えられない() -> None:
    差し戻し = SendBack(by=座長, reason="件数が合っていません")
    with pytest.raises(ValidationError):
        差し戻し.reason = "やっぱりよい"  # type: ignore[misc]
