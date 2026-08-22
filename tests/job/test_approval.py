"""承認の壊しかた。設計/仕事とは何か.md §3・§7・I4・I7。

**誰がといつを両方持つ。** 片方空で作れたら赤。
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from domain.job.approval import Approval
from domain.people.agent import Agent
from domain.people.human import Human

承認した人 = Human(name="座長")
時刻 = datetime(2026, 8, 22, 17, 30)


def test_誰がといつを両方持つ承認は作れる() -> None:
    承認 = Approval(by=承認した人, at=時刻)
    assert 承認.by == 承認した人
    assert 承認.at == 時刻


def test_誰がの欠けた承認は作れない() -> None:
    with pytest.raises(ValidationError):
        Approval(at=時刻)  # type: ignore[call-arg]


def test_いつの欠けた承認は作れない() -> None:
    with pytest.raises(ValidationError):
        Approval(by=承認した人)  # type: ignore[call-arg]


def test_名の空な人は承認できない() -> None:
    with pytest.raises(ValidationError):
        Approval(by=Human(name=""), at=時刻)


def test_AI_は承認できない() -> None:
    with pytest.raises(ValidationError):
        Approval(by=Agent(name="一号"), at=時刻)  # type: ignore[arg-type]


def test_素の文字列は承認した人にならない() -> None:
    with pytest.raises(ValidationError):
        Approval(by="座長", at=時刻)  # type: ignore[arg-type]


def test_決めたあと書き換えられない() -> None:
    承認 = Approval(by=承認した人, at=時刻)
    with pytest.raises(ValidationError):
        承認.at = datetime(2026, 8, 23, 9, 0)  # type: ignore[misc]
