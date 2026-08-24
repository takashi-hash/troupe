"""突合の壊しかた。設計/仕事が回る筋道.md §2「ドメインサービス」・§1 `create`・I3・I8。

**既にある鍵は二度作らない**——鍵は `Origin` が出すものと同じ形。
**源に `{患者}` の穴を持つ版は、対象期間に予定の訪問がある患者ごとに1つ。**
"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.services.reconcile import reconcile
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.origin import Origin
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
週次 = RuleName(text="週次の依存の棚卸し")
月次 = RuleName(text="月次の請求の突合")
下書き = RuleName(text="Visit Note Draft")
書類 = Source(location="file:pyproject.toml")
カルテ = Source(location="db:chart/{患者}")


def test_まだ無い仕事が作るべきに出る_週はISO週の形() -> None:
    作るべき = reconcile([(週次, 1, Cycle.WEEKLY, 書類)], (), (), now=いま)
    assert 作るべき == ((週次, 1, Period(text="2026-W34"), None),)


def test_週と月で対象期間の形が違う() -> None:
    作るべき = reconcile(
        [(週次, 1, Cycle.WEEKLY, 書類), (月次, 2, Cycle.MONTHLY, 書類)], (), (), いま
    )
    assert 作るべき == (
        (週次, 1, Period(text="2026-W34"), None),
        (月次, 2, Period(text="2026-08"), None),
    )


def test_既にある鍵は二度作らない() -> None:
    """I3——同じ作成元から仕事は二度作られない。"""
    既にある = {Origin.from_rule(週次, 1, Period(text="2026-W34")).key}
    assert reconcile([(週次, 1, Cycle.WEEKLY, 書類)], 既にある, (), いま) == ()


def test_版が違えば別の鍵で作る() -> None:
    既にある = {Origin.from_rule(週次, 1, Period(text="2026-W34")).key}
    作るべき = reconcile([(週次, 2, Cycle.WEEKLY, 書類)], 既にある, (), いま)
    assert 作るべき == ((週次, 2, Period(text="2026-W34"), None),)


def test_作った鍵を積んだあとに回すと_もう出ない() -> None:
    """時計の掟——何度回しても同じ結果になる。"""
    有効 = [(週次, 1, Cycle.WEEKLY, 書類), (月次, 1, Cycle.MONTHLY, 書類)]
    一度目 = reconcile(有効, (), (), いま)
    鍵 = {Origin.from_rule(名, 番, 期間, 患者).key for 名, 番, 期間, 患者 in 一度目}
    assert reconcile(有効, 鍵, (), いま) == ()


def test_穴あきの版は期間内に予定のある患者ごとに1つ() -> None:
    """筋道 §1 `create`——展開の正体。期間外の予定と重複の患者は数えない。"""
    予定 = (
        ("P-001", "2026-08-18"),  # 週内
        ("P-004", "2026-08-21"),  # 週内
        ("P-004", "2026-08-19"),  # 週内・同じ患者——1つに畳む
        ("P-009", "2026-08-24"),  # 翌週——出ない
    )
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ)], (), 予定, いま)
    assert 作るべき == (
        (下書き, 1, Period(text="2026-W34"), "P-001"),
        (下書き, 1, Period(text="2026-W34"), "P-004"),
    )


def test_穴あきの版でも既にある患者の鍵は二度作らない() -> None:
    既にある = {Origin.from_rule(下書き, 1, Period(text="2026-W34"), "P-001").key}
    予定 = (("P-001", "2026-08-18"), ("P-004", "2026-08-21"))
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ)], 既にある, 予定, いま)
    assert 作るべき == ((下書き, 1, Period(text="2026-W34"), "P-004"),)


def test_穴あきの版で予定が無ければ1つも出ない() -> None:
    """下書きの相手が居ない——0件は正しい姿。"""
    assert reconcile([(下書き, 1, Cycle.WEEKLY, カルテ)], (), (), いま) == ()


def test_読めない日付の予定は数えない() -> None:
    予定 = (("P-001", "いつか"),)
    assert reconcile([(下書き, 1, Cycle.WEEKLY, カルテ)], (), 予定, いま) == ()


def test_月次の穴あき版は月の予定で展開される() -> None:
    予定 = (("P-001", "2026-08-03"), ("P-002", "2026-09-01"))  # 9月は出ない
    作るべき = reconcile([(下書き, 1, Cycle.MONTHLY, カルテ)], (), 予定, いま)
    assert 作るべき == ((下書き, 1, Period(text="2026-08"), "P-001"),)


def test_穴あきと穴なしの版が同じ回で混ざっても互いに乱さない() -> None:
    予定 = (("P-001", "2026-08-18"),)
    作るべき = reconcile(
        [(週次, 1, Cycle.WEEKLY, 書類), (下書き, 1, Cycle.WEEKLY, カルテ)], (), 予定, いま
    )
    assert 作るべき == (
        (週次, 1, Period(text="2026-W34"), None),
        (下書き, 1, Period(text="2026-W34"), "P-001"),
    )


def test_患者記号の空な予定は数えない_脈は落ちない() -> None:
    """読めない行は読めない日付と同じ——1行の汚れで週全体の展開が止まらない。"""
    予定 = (("", "2026-08-18"), ("   ", "2026-08-19"), ("P-001", "2026-08-18"))
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ)], (), 予定, いま)
    assert 作るべき == ((下書き, 1, Period(text="2026-W34"), "P-001"),)


def test_予定が後から見えても追いつく() -> None:
    """EMR の読めない朝——復帰した次の回で、同じ鍵の照合のまま作るべきに出る。"""
    落ちた朝 = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ)], (), (), いま)
    assert 落ちた朝 == ()
    復帰後 = reconcile(
        [(下書き, 1, Cycle.WEEKLY, カルテ)], (), (("P-001", "2026-08-18"),), いま
    )
    assert 復帰後 == ((下書き, 1, Period(text="2026-W34"), "P-001"),)
