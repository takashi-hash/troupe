"""突合の壊しかた。設計/仕事が回る筋道.md §2「ドメインサービス」・§1 `create`・I3・I8。

**既にある鍵は二度作らない**——鍵は `Origin` が出すものと同じ形。
**源に穴を持つ版は、リード（版の日数）以内に迫った予定の定期訪問ごとに1つ**——
比べる「今日」は診療所の暦（JST）。版と期間は鍵に入れない。
"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.services.reconcile import reconcile
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.origin import Origin
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source

#: JST では 8/17(月) 18:00——訪問の水平線は 8/17〜8/19（日数2）。
いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
週次 = RuleName(text="週次の依存の棚卸し")
月次 = RuleName(text="月次の請求の突合")
下書き = RuleName(text="Visit Note Draft")
書類 = Source(location="file:pyproject.toml")
カルテ = Source(location="db:chart/{患者}")


def test_まだ無い仕事が作るべきに出る_週はISO週の形() -> None:
    作るべき = reconcile([(週次, 1, Cycle.WEEKLY, 書類, 2)], (), (), now=いま)
    assert 作るべき == ((週次, 1, Period(text="2026-W34"), None, None),)


def test_週と月で対象期間の形が違う() -> None:
    作るべき = reconcile(
        [(週次, 1, Cycle.WEEKLY, 書類, 2), (月次, 2, Cycle.MONTHLY, 書類, 3)], (), (), いま
    )
    assert 作るべき == (
        (週次, 1, Period(text="2026-W34"), None, None),
        (月次, 2, Period(text="2026-08"), None, None),
    )


def test_既にある鍵は二度作らない() -> None:
    """I3——同じ作成元から仕事は二度作られない。"""
    既にある = {Origin.from_rule(週次, 1, Period(text="2026-W34")).key}
    assert reconcile([(週次, 1, Cycle.WEEKLY, 書類, 2)], 既にある, (), いま) == ()


def test_版が違えば別の鍵で作る() -> None:
    既にある = {Origin.from_rule(週次, 1, Period(text="2026-W34")).key}
    作るべき = reconcile([(週次, 2, Cycle.WEEKLY, 書類, 2)], 既にある, (), いま)
    assert 作るべき == ((週次, 2, Period(text="2026-W34"), None, None),)


def test_作った鍵を積んだあとに回すと_もう出ない() -> None:
    """時計の掟——何度回しても同じ結果になる。"""
    有効 = [(週次, 1, Cycle.WEEKLY, 書類, 2), (月次, 1, Cycle.MONTHLY, 書類, 3)]
    一度目 = reconcile(有効, (), (), いま)
    鍵 = {Origin.from_rule(名, 番, 期間).key for 名, 番, 期間, _患者, _日 in 一度目}
    assert reconcile(有効, 鍵, (), いま) == ()


def test_穴あきの版はリード内に迫った訪問ごとに1つ() -> None:
    """筋道 §1 `create`——展開の正体。今日より前と、日数の先の予定は数えない。"""
    予定 = (
        ("P-001", "2026-08-17"),  # 今日(JST)——出る
        ("P-004", "2026-08-19"),  # 今日+2——出る
        ("P-004", "2026-08-18"),  # 同じ患者の別の日——別の訪問として出る
        ("P-002", "2026-08-16"),  # 昨日——出ない(過去の訪問に下書きは要らない)
        ("P-009", "2026-08-20"),  # 今日+3——まだ出ない(次の脈が拾う)
    )
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), 予定, いま)
    assert 作るべき == (
        (下書き, 1, Period(text="2026-W34"), "P-001", "2026-08-17"),
        (下書き, 1, Period(text="2026-W34"), "P-004", "2026-08-18"),
        (下書き, 1, Period(text="2026-W34"), "P-004", "2026-08-19"),
    )


def test_同じ患者の同じ日の重複は1つに畳む() -> None:
    予定 = (("P-001", "2026-08-18"), ("P-001", "2026-08-18"))
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), 予定, いま)
    assert 作るべき == ((下書き, 1, Period(text="2026-W34"), "P-001", "2026-08-18"),)


def test_穴あきの版でも既にある訪問の鍵は二度作らない() -> None:
    既にある = {Origin.from_visit(下書き, "P-001", "2026-08-18").key}
    予定 = (("P-001", "2026-08-18"), ("P-004", "2026-08-19"))
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], 既にある, 予定, いま)
    assert 作るべき == ((下書き, 1, Period(text="2026-W34"), "P-004", "2026-08-19"),)


def test_訪問の鍵に版と期間は入らない_版を上げても二度作らない() -> None:
    """業務の同一性は（規則・患者・訪問日）——版の改訂で同じ訪問の下書きは増えない。"""
    既にある = {Origin.from_visit(下書き, "P-001", "2026-08-18").key}
    予定 = (("P-001", "2026-08-18"),)
    assert reconcile([(下書き, 9, Cycle.WEEKLY, カルテ, 2)], 既にある, 予定, いま) == ()


def test_穴あきの版で予定が無ければ1つも出ない() -> None:
    """下書きの相手が居ない——0件は正しい姿。"""
    assert reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), (), いま) == ()


def test_読めない日付の予定は数えない() -> None:
    予定 = (("P-001", "いつか"),)
    assert reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), 予定, いま) == ()


def test_今日はJSTで判じる_UTCの日付ではない() -> None:
    """UTC 20:00 = JST 翌 05:00——診療所の朝には明日の訪問がもう水平線の中。"""
    夜 = datetime(2026, 8, 17, 20, 0, tzinfo=UTC)  # JST 8/18 05:00
    予定 = (("P-001", "2026-08-17"), ("P-004", "2026-08-20"))
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), 予定, 夜)
    assert 作るべき == ((下書き, 1, Period(text="2026-W34"), "P-004", "2026-08-20"),)


def test_訪問仕事の対象期間は訪問日から導く() -> None:
    """来週の訪問がリード内に入ったら、対象期間も来週——読みのための札は訪問の週。"""
    土曜 = datetime(2026, 8, 22, 9, 0, tzinfo=UTC)  # JST 8/22(土)
    予定 = (("P-001", "2026-08-24"),)  # 翌週(W35)の月曜
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), 予定, 土曜)
    assert 作るべき == ((下書き, 1, Period(text="2026-W35"), "P-001", "2026-08-24"),)


def test_穴あきと穴なしの版が同じ回で混ざっても互いに乱さない() -> None:
    予定 = (("P-001", "2026-08-18"),)
    作るべき = reconcile(
        [(週次, 1, Cycle.WEEKLY, 書類, 2), (下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), 予定, いま
    )
    assert 作るべき == (
        (週次, 1, Period(text="2026-W34"), None, None),
        (下書き, 1, Period(text="2026-W34"), "P-001", "2026-08-18"),
    )


def test_患者記号の空な予定は数えない_脈は落ちない() -> None:
    """読めない行は読めない日付と同じ——1行の汚れで展開が止まらない。"""
    予定 = (("", "2026-08-18"), ("   ", "2026-08-19"), ("P-001", "2026-08-18"))
    作るべき = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), 予定, いま)
    assert 作るべき == ((下書き, 1, Period(text="2026-W34"), "P-001", "2026-08-18"),)


def test_予定が後から見えても追いつく() -> None:
    """EMR の読めない朝——復帰した次の回で、同じ鍵の照合のまま作るべきに出る。"""
    落ちた朝 = reconcile([(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), (), いま)
    assert 落ちた朝 == ()
    復帰後 = reconcile(
        [(下書き, 1, Cycle.WEEKLY, カルテ, 2)], (), (("P-001", "2026-08-18"),), いま
    )
    assert 復帰後 == ((下書き, 1, Period(text="2026-W34"), "P-001", "2026-08-18"),)
