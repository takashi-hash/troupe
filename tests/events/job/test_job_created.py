"""仕事が作られたの壊しかた。設計/仕事が回る筋道.md §5——三つ揃いか三つ空。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_created import JobCreated
from domain.value_objects.calendar.period import Period
from domain.value_objects.people.clock import Clock
from domain.value_objects.rule.rule_name import RuleName

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
規則 = RuleName(text="週次の依存の棚卸し")
期間 = Period(text="2026-W34")


def test_業務ルール発は三つ揃いで残る() -> None:
    出来事 = JobCreated(at=いま, by=Clock(), rule_name=規則, version=1, period=期間)
    assert set(JobCreated.model_fields) == {"at", "by", "rule_name", "version", "period"}
    assert 出来事.rule_name == 規則 and 出来事.version == 1 and 出来事.period == 期間


def test_依頼発は三つとも空で残る() -> None:
    出来事 = JobCreated(at=いま, by=Clock(), rule_name=None, version=None, period=None)
    assert 出来事.rule_name is None and 出来事.version is None and 出来事.period is None


def test_三つのうち一部だけの形は書けない() -> None:
    with pytest.raises(ValidationError, match="三つ"):
        JobCreated(at=いま, by=Clock(), rule_name=規則, version=None, period=None)
    with pytest.raises(ValidationError, match="三つ"):
        JobCreated(at=いま, by=Clock(), rule_name=None, version=1, period=期間)


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        JobCreated(
            at=いま, by=Clock(), rule_name=None, version=None, period=None, 中身="x"  # type: ignore[call-arg]
        )
