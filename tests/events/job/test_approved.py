"""承認されたの壊しかた。設計/仕事が回る筋道.md §5——人が主語。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.approved import Approved
from domain.value_objects.people.human import Human

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_承認されたは誰がといつだけを残す() -> None:
    出来事 = Approved(at=いま, by=Human(name="座長"))
    assert set(Approved.model_fields) == {"at", "by"}
    assert 出来事.by == Human(name="座長")


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        Approved(at=いま, by=Human(name="座長"), 中身="x")  # type: ignore[call-arg]
