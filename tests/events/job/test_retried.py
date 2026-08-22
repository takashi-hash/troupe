"""もう一度やったの壊しかた。設計/仕事が回る筋道.md §5。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.retried import Retried
from domain.value_objects.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_何度目かが残る() -> None:
    出来事 = Retried(at=いま, by=Clock(), times=1)
    assert set(Retried.model_fields) == {"at", "by", "times"}
    assert 出来事.times == 1


def test_0度目のやり直しは作れない() -> None:
    with pytest.raises(ValidationError, match="1以上"):
        Retried(at=いま, by=Clock(), times=0)


def test_負の何度目かは作れない() -> None:
    with pytest.raises(ValidationError, match="1以上"):
        Retried(at=いま, by=Clock(), times=-1)
