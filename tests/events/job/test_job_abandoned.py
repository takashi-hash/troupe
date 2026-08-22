"""打ち切られたの壊しかた。設計/仕事が回る筋道.md §5——人が主語。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_abandoned import JobAbandoned
from domain.values.people.human import Human

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
座長 = Human(name="座長")


def test_誰がと理由が残る() -> None:
    出来事 = JobAbandoned(at=いま, by=座長, reason="源が消えて追えない")
    assert set(JobAbandoned.model_fields) == {"at", "by", "reason"}
    assert 出来事.by == 座長 and 出来事.reason == "源が消えて追えない"


def test_理由が空なら作れない() -> None:
    with pytest.raises(ValidationError, match="理由"):
        JobAbandoned(at=いま, by=座長, reason=" ")
