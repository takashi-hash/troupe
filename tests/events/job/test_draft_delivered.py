"""下書きが配達されたの壊しかた。設計/仕事が回る筋道.md §5——時計が主語・足す欄なし。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.draft_delivered import DraftDelivered
from domain.value_objects.people.clock import Clock

いま = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


def test_下書きが配達されたはいつと誰がだけを残す() -> None:
    """どこへ置いたかは源が知っている——二重の正本を作らない。"""
    出来事 = DraftDelivered(at=いま, by=Clock())
    assert set(DraftDelivered.model_fields) == {"at", "by"}
    assert 出来事.at == いま and 出来事.by == Clock()


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        DraftDelivered(at=いま, by=Clock(), 置き先="P-001")  # type: ignore[call-arg]
