"""版を積む（app）の壊しかた。設計/仕事が回る筋道.md §1・§4——題材が初期値、人が上書き。"""

from __future__ import annotations

from app.dto.version_form import VersionForm
from app.services.human.add_version import add_version, add_version_from_fields
from domain.events.rule.rule_version_added import RuleVersionAdded
from tests.aggregates.job.conftest import make_copied
from tests.aggregates.rule.conftest import make_rule, 名, 座長
from tests.app.services.conftest import 固定時計, ルール帳簿の偽物, 題材の偽物


def test_題材を初期値に_1版目として業務ルールごと生まれ_対で書く() -> None:
    帳簿 = ルール帳簿の偽物()
    断り = add_version(帳簿, 題材の偽物(make_copied()), 固定時計(), 名.text, by=座長.name, form=VersionForm())
    assert 断り is None
    ルール = 帳簿.rules[名]
    assert tuple(v.number for v in ルール.versions) == (1,)
    assert ルール.active is None  # 積んだだけでは有効にならない——有効は人の別の判断
    assert [type(e) for e in 帳簿.events] == [RuleVersionAdded]


def test_人が書いた欄が題材を上書きする() -> None:
    帳簿 = ルール帳簿の偽物()
    断り = add_version(帳簿, 題材の偽物(make_copied()), 固定時計(), 名.text, by=座長.name, form=VersionForm(days=5))
    assert 断り is None
    版 = 帳簿.rules[名].versions[-1]
    assert 版.days == 5
    assert 版.instruction == make_copied().instruction  # 上書きしない欄は題材のまま


def test_在る業務ルールには次の番号で積まれる() -> None:
    """版は積むだけ（I2）——番号は最後の版＋1しかありえない。"""
    帳簿 = ルール帳簿の偽物()
    帳簿.rules[名] = make_rule()
    断り = add_version(帳簿, 題材の偽物(make_copied()), 固定時計(), 名.text, by=座長.name, form=VersionForm())
    assert 断り is None
    assert tuple(v.number for v in 帳簿.rules[名].versions) == (1, 2)


def test_題材が無く_書いた欄も足りなければ断りに変わる() -> None:
    """題材にデータが無ければ初期値なし——人がぜんぶ書く。足りなければ義務が拒む。"""
    帳簿 = ルール帳簿の偽物()
    断り = add_version(帳簿, 題材の偽物(None), 固定時計(), 名.text, by=座長.name, form=VersionForm(days=5))
    assert 断り is not None
    assert not 帳簿.rules and not 帳簿.events


def test_義務に触れる上書きは断りに変わる() -> None:
    """エラーは投げない——版の列に傷をつけず、理由だけが返る。"""
    帳簿 = ルール帳簿の偽物()
    断り = add_version(帳簿, 題材の偽物(make_copied()), 固定時計(), 名.text, by=座長.name, form=VersionForm(days=0))
    assert 断り is not None
    assert not 帳簿.rules and not 帳簿.events


def test_欄の文字から組める_周期は用語集の語で書ける() -> None:
    """画面から渡るのは文字だけ——数に読むのも周期の語を写すのも app の仕事。"""
    帳簿 = ルール帳簿の偽物()
    断り = add_version_from_fields(
        帳簿, 題材の偽物(make_copied()), 固定時計(), 名.text, by=座長.name,
        fields={"days": "5", "cycle": "月"},
    )
    assert 断り is None
    版 = 帳簿.rules[名].versions[-1]
    assert 版.days == 5 and 版.cycle.value == "monthly"


def test_数に読めない欄は断りに変わる_窓は落ちない() -> None:
    帳簿 = ルール帳簿の偽物()
    断り = add_version_from_fields(
        帳簿, 題材の偽物(make_copied()), 固定時計(), 名.text, by=座長.name,
        fields={"days": "五日"},
    )
    assert 断り is not None and "終えるまでの日数" in 断り.reason  # 断りも用語集の語で
    assert not 帳簿.rules and not 帳簿.events
