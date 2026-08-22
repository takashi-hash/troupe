"""突き合わせるの壊しかた。I8——有効なら、その対象期間の仕事が必ず存在する。"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.clock.audit import audit
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.job.origin import Origin
from domain.value_objects.calendar.period import Period
from domain.value_objects.rule.rule_name import RuleName

いま = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
名 = RuleName(text="週次の依存の棚卸し")


class 有効の偽物:
    def __init__(self, *rows: tuple[RuleName, int, Cycle]) -> None:
        self.rows = rows

    def read_all(self) -> tuple[tuple[RuleName, int, Cycle], ...]:
        return self.rows


class 鍵の偽物:
    def __init__(self, *keys: str) -> None:
        self._keys = frozenset(keys)

    def keys(self) -> frozenset[str]:
        return self._keys


class 固定時計:
    def now(self) -> datetime:
        return いま


def test_仕事が無ければ赤く数え上がる() -> None:
    欠け = audit(有効の偽物((名, 1, Cycle.WEEKLY)), 鍵の偽物(), 固定時計())
    assert 欠け == ((名, 1, Period.of(いま, Cycle.WEEKLY)),)


def test_仕事が在れば空() -> None:
    期間 = Period.of(いま, Cycle.WEEKLY)
    鍵 = Origin.from_rule(名, 1, 期間).key
    assert audit(有効の偽物((名, 1, Cycle.WEEKLY)), 鍵の偽物(鍵), 固定時計()) == ()


def test_有効が無ければ空() -> None:
    """守るものが無いところに欠けは無い。"""
    assert audit(有効の偽物(), 鍵の偽物(), 固定時計()) == ()
