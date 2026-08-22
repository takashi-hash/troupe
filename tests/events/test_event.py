"""出来事の共通の壊しかた。設計/仕事が回る筋道.md §5。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.event import Event
from domain.values.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_すべての出来事がいつと誰がを持つ() -> None:
    出来事 = Event(at=いま, by=Clock())
    assert 出来事.at == いま and 出来事.by == Clock()


def test_いつか誰がが欠けた出来事は作れない() -> None:
    with pytest.raises(ValidationError):
        Event(at=いま)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Event(by=Clock())  # type: ignore[call-arg]


def test_誰がは素の文字列から作れない() -> None:
    with pytest.raises(ValidationError):
        Event(at=いま, by="時計")  # type: ignore[arg-type]
