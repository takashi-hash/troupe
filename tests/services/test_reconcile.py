"""突合の壊しかた。設計/仕事が回る筋道.md §2「ドメインサービス」・I3・I8。

**既にある鍵は二度作らない**——鍵は `Origin` が出すものと同じ形。
"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.services.reconcile import reconcile
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.origin import Origin
from domain.value_objects.rule.rule_name import RuleName

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
週次 = RuleName(text="週次の依存の棚卸し")
月次 = RuleName(text="月次の請求の突合")


def test_まだ無い仕事が作るべきに出る_週はISO週の形() -> None:
    作るべき = reconcile([(週次, 1, Cycle.WEEKLY)], existing_origin_keys=(), now=いま)
    assert 作るべき == ((週次, 1, Period(text="2026-W34")),)


def test_週と月で対象期間の形が違う() -> None:
    作るべき = reconcile([(週次, 1, Cycle.WEEKLY), (月次, 2, Cycle.MONTHLY)], (), いま)
    assert 作るべき == (
        (週次, 1, Period(text="2026-W34")),
        (月次, 2, Period(text="2026-08")),
    )


def test_既にある鍵は二度作らない() -> None:
    """I3——同じ作成元から仕事は二度作られない。"""
    既にある = {Origin.from_rule(週次, 1, Period(text="2026-W34")).key}
    assert reconcile([(週次, 1, Cycle.WEEKLY)], 既にある, いま) == ()


def test_版が違えば別の鍵で作る() -> None:
    既にある = {Origin.from_rule(週次, 1, Period(text="2026-W34")).key}
    作るべき = reconcile([(週次, 2, Cycle.WEEKLY)], 既にある, いま)
    assert 作るべき == ((週次, 2, Period(text="2026-W34")),)


def test_作った鍵を積んだあとに回すと_もう出ない() -> None:
    """時計の掟——何度回しても同じ結果になる。"""
    有効 = [(週次, 1, Cycle.WEEKLY), (月次, 1, Cycle.MONTHLY)]
    一度目 = reconcile(有効, (), いま)
    鍵 = {Origin.from_rule(名, 番, 期間).key for 名, 番, 期間 in 一度目}
    assert reconcile(有効, 鍵, いま) == ()
