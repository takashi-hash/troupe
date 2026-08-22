"""予定を集めるの壊しかた。人に見えるもの §1・§2——未作成のものが見える（F1）。"""

from __future__ import annotations

from datetime import UTC, datetime

from app.ports.rule_reader import RuleLine
from app.services.screen.gather_schedule import gather_schedule
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.origin import Origin
from domain.value_objects.rule.rule_name import RuleName

いま = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
名 = RuleName(text="週次の依存の棚卸し")


class 一覧の偽物:
    def __init__(self, *lines: RuleLine) -> None:
        self._lines = lines

    def read_all(self) -> tuple[RuleLine, ...]:
        return self._lines


class 有効の偽物:
    def __init__(self, *rows: tuple[RuleName, int, Cycle]) -> None:
        self._rows = rows

    def read_all(self) -> tuple[tuple[RuleName, int, Cycle], ...]:
        return self._rows


class 鍵の偽物:
    def __init__(self, *keys: str) -> None:
        self._keys = frozenset(keys)

    def keys(self) -> frozenset[str]:
        return self._keys


class 固定時計:
    def now(self) -> datetime:
        return いま


def _line(active: int | None = 1) -> RuleLine:
    return RuleLine(name=名.text, version_number=1, active_version=active, instruction="棚卸しする")


def test_未作成のものが見える() -> None:
    (行,) = gather_schedule(一覧の偽物(_line()), 有効の偽物((名, 1, Cycle.WEEKLY)), 鍵の偽物(), 固定時計())
    assert 行.next_period == "2026-W34（未作成）"
    assert 行.actions == ("add_version", "activate", "deactivate")


def test_作られたものは作られたと出る() -> None:
    鍵 = Origin.from_rule(名, 1, Period.of(いま, Cycle.WEEKLY)).key
    (行,) = gather_schedule(一覧の偽物(_line()), 有効の偽物((名, 1, Cycle.WEEKLY)), 鍵の偽物(鍵), 固定時計())
    assert 行.next_period == "2026-W34（作られた）"


def test_止まっている業務ルールに次の対象期間は無い() -> None:
    (行,) = gather_schedule(一覧の偽物(_line(active=None)), 有効の偽物(), 鍵の偽物(), 固定時計())
    assert 行.next_period is None
    assert 行.actions == ("add_version", "activate")  # 止めるは有効なときだけ
