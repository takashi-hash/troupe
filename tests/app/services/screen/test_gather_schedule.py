"""予定を集めるの壊しかた。人に見えるもの §1・§2——未作成のものが見える（F1）。"""

from __future__ import annotations

from datetime import UTC, datetime

from app.ports.rule_reader import RuleLine
from app.services.screen.gather_schedule import gather_schedule
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.origin import Origin
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source
from tests.app.services.clock.conftest import 予定の読みの偽物

いま = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
名 = RuleName(text="週次の依存の棚卸し")
源 = Source(location="deps://prod")


class 一覧の偽物:
    def __init__(self, *lines: RuleLine) -> None:
        self._lines = lines

    def read_all(self) -> tuple[RuleLine, ...]:
        return self._lines


class 有効の偽物:
    def __init__(self, *rows: tuple[RuleName, int, Cycle, Source, int]) -> None:
        self._rows = rows

    def read_all(self) -> tuple[tuple[RuleName, int, Cycle, Source, int], ...]:
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
    (行,) = gather_schedule(
        一覧の偽物(_line()), 有効の偽物((名, 1, Cycle.WEEKLY, 源, 3)), 鍵の偽物(),
        予定の読みの偽物(), 固定時計(),
    )
    assert 行.next_period == "2026-W34（未作成）"
    assert 行.actions == ("add_version", "activate", "deactivate")


def test_作られたものは作られたと出る() -> None:
    鍵 = Origin.from_rule(名, 1, Period.of(いま, Cycle.WEEKLY)).key
    (行,) = gather_schedule(
        一覧の偽物(_line()), 有効の偽物((名, 1, Cycle.WEEKLY, 源, 3)), 鍵の偽物(鍵),
        予定の読みの偽物(), 固定時計(),
    )
    assert 行.next_period == "2026-W34（作られた）"


def test_止まっている業務ルールに次の対象期間は無い() -> None:
    (行,) = gather_schedule(
        一覧の偽物(_line(active=None)), 有効の偽物(), 鍵の偽物(), 予定の読みの偽物(), 固定時計()
    )
    assert 行.next_period is None
    assert 行.actions == ("add_version", "activate")  # 止めるは有効なときだけ


def test_穴あきの版は残りの訪問数が見える() -> None:
    """展開のうち半分だけ作られたリード——「作られた」と嘘をつかない。"""
    カルテ = Source(location="db:chart/{患者}")
    予定 = 予定の読みの偽物((("P-001", "2026-08-18"), ("P-004", "2026-08-19"), ("P-009", "2026-08-20")))
    鍵 = Origin.from_visit(名, "P-001", "2026-08-18").key
    (行,) = gather_schedule(
        一覧の偽物(_line()), 有効の偽物((名, 1, Cycle.WEEKLY, カルテ, 3)), 鍵の偽物(鍵), 予定, 固定時計()
    )
    assert 行.next_period == "2026-W34（未作成 2件）"


def test_来ている仕事の列が語と見出しで出る() -> None:
    """予定の下段——頼んだ直後の行方がここに見える（§1 予定の正本）。"""
    from app.services.screen.gather_schedule import gather_upcoming
    from tests.services.conftest import make_material

    class 今日読みの偽物:
        def read(self, id):  # type: ignore[no-untyped-def]
            return None

        def read_all(self):  # type: ignore[no-untyped-def]
            return (make_material(),)

    rows = gather_upcoming(今日読みの偽物())
    assert rows[0].head == "週次の依存の棚卸し　2026-W34"
    assert rows[0].state_name == "承認待ち"  # 画面に出るのは用語集の語そのまま
    assert rows[0].instruction


def test_穴あきの版が全訪問分作られたら作られたと出る() -> None:
    カルテ = Source(location="db:chart/{患者}")
    予定 = 予定の読みの偽物((("P-001", "2026-08-18"),))
    鍵 = Origin.from_visit(名, "P-001", "2026-08-18").key
    (行,) = gather_schedule(
        一覧の偽物(_line()), 有効の偽物((名, 1, Cycle.WEEKLY, カルテ, 3)), 鍵の偽物(鍵), 予定, 固定時計()
    )
    assert 行.next_period == "2026-W34（作られた）"
