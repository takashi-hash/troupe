"""使った量が増えたの壊しかた。設計/仕事が回る筋道.md §5。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.spent_increased import SpentIncreased
from domain.values.people.agent import Agent

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_増えた回数と秒が残る() -> None:
    出来事 = SpentIncreased(at=いま, by=Agent(name="出納係"), calls=1, seconds=12)
    assert set(SpentIncreased.model_fields) == {"at", "by", "calls", "seconds"}
    assert 出来事.calls == 1 and 出来事.seconds == 12


def test_片方だけが増えたのでもよい() -> None:
    出来事 = SpentIncreased(at=いま, by=Agent(name="出納係"), calls=1, seconds=0)
    assert 出来事.calls == 1 and 出来事.seconds == 0


def test_両方0は増えていないので作れない() -> None:
    with pytest.raises(ValidationError, match="増えていません"):
        SpentIncreased(at=いま, by=Agent(name="出納係"), calls=0, seconds=0)


def test_負の値では作れない() -> None:
    with pytest.raises(ValidationError, match="0以上"):
        SpentIncreased(at=いま, by=Agent(name="出納係"), calls=-1, seconds=10)
    with pytest.raises(ValidationError, match="0以上"):
        SpentIncreased(at=いま, by=Agent(name="出納係"), calls=1, seconds=-1)
