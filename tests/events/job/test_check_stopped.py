"""検査で止まったの壊しかた。設計/仕事が回る筋道.md §5——理由の無い止まりは残せない。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.check_stopped import CheckStopped
from domain.values.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_検査で止まったは止めた理由を残す() -> None:
    出来事 = CheckStopped(at=いま, by=Clock(), reason="必ず含む語がありません: 2026-W34")
    assert set(CheckStopped.model_fields) == {"at", "by", "reason"}
    assert 出来事.reason == "必ず含む語がありません: 2026-W34"


def test_理由が空では止まった形が書けない() -> None:
    with pytest.raises(ValidationError, match="止めた理由"):
        CheckStopped(at=いま, by=Clock(), reason="")
    with pytest.raises(ValidationError, match="止めた理由"):
        CheckStopped(at=いま, by=Clock(), reason="   ")
