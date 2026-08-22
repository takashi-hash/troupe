"""確かめ期日が先へ送られたの壊しかた。設計/仕事が回る筋道.md §5——時計が主語。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.recheck_date_pushed import RecheckDatePushed
from domain.values.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
次 = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


def test_新しい確かめ期日が残る() -> None:
    出来事 = RecheckDatePushed(at=いま, by=Clock(), recheck_at=次)
    assert set(RecheckDatePushed.model_fields) == {"at", "by", "recheck_at"}
    assert 出来事.recheck_at == 次


def test_新しい確かめ期日が欠けたら作れない() -> None:
    with pytest.raises(ValidationError):
        RecheckDatePushed(at=いま, by=Clock())  # type: ignore[call-arg]
