"""突き合わせるの壊しかた。I8——有効なら、その対象期間の仕事が必ず存在する。"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.clock.audit import audit
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.job.origin import Origin
from domain.value_objects.calendar.period import Period
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source
from tests.app.services.clock.conftest import 予定の読みの偽物

いま = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
名 = RuleName(text="週次の依存の棚卸し")
源 = Source(location="deps://prod")


class 有効の偽物:
    def __init__(self, *rows: tuple[RuleName, int, Cycle, Source, int]) -> None:
        self.rows = rows

    def read_all(self) -> tuple[tuple[RuleName, int, Cycle, Source, int], ...]:
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
    欠け = audit(有効の偽物((名, 1, Cycle.WEEKLY, 源, 3)), 鍵の偽物(), 予定の読みの偽物(), 固定時計())
    assert 欠け == ((名, 1, Period.of(いま, Cycle.WEEKLY), None, None),)


def test_仕事が在れば空() -> None:
    期間 = Period.of(いま, Cycle.WEEKLY)
    鍵 = Origin.from_rule(名, 1, 期間).key
    assert audit(
        有効の偽物((名, 1, Cycle.WEEKLY, 源, 3)), 鍵の偽物(鍵), 予定の読みの偽物(), 固定時計()
    ) == ()


def test_有効が無ければ空() -> None:
    """守るものが無いところに欠けは無い。"""
    assert audit(有効の偽物(), 鍵の偽物(), 予定の読みの偽物(), 固定時計()) == ()


def test_穴あきの版は訪問ごとに欠けが数え上がる() -> None:
    """I8 は展開後の1つ1つを守る——半分だけ作られたリードが緑にならない。"""
    カルテ = Source(location="db:chart/{患者}")
    期間 = Period.of(いま, Cycle.WEEKLY)
    予定 = 予定の読みの偽物((("P-001", "2026-08-18"), ("P-004", "2026-08-19")))
    鍵 = Origin.from_visit(名, "P-001", "2026-08-18").key
    欠け = audit(有効の偽物((名, 1, Cycle.WEEKLY, カルテ, 3)), 鍵の偽物(鍵), 予定, 固定時計())
    assert 欠け == ((名, 1, 期間, "P-004", "2026-08-19"),)
