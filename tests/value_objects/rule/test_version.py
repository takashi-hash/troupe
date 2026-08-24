"""版と写すものの束の壊しかた。設計/仕事とは何か.md §3・§4・§7。

**版そのものは渡さない。写すのであって、指すのではない。**
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.source import Source
from domain.value_objects.rule.copied import Copied
from domain.value_objects.rule.version import Version


def 版の欄() -> dict[str, Any]:
    """通る版の欄一式。**例が仕様。** ここから1つ抜くのが「どれか欠けて」。"""
    return {
        "number": 1,
        "instruction": Instruction(text="先月分の請求書を源から読み、出ていない先を並べる"),
        "criteria": AcceptanceCriteria(
            required_terms=("{対象期間} の請求書",), description="先月分の請求がすべて出ていること"
        ),
        "cycle": Cycle.MONTHLY,
        "days": 5,
        "budget": Budget(calls=20, seconds=600),
        "owner": Owner(person=Human(name="座長")),
        "source": Source(location="data/請求.csv"),
        "max_retries": 3,
    }


def 版() -> Version:
    return Version(**版の欄())


# ——— 通る例（例が仕様） ———


def test_八つそろえば版は作れる() -> None:
    版1 = 版()
    assert 版1.number == 1
    assert 版1.instruction.text.startswith("先月分の請求書")
    assert 版1.cycle is Cycle.MONTHLY
    assert 版1.days == 5
    assert 版1.budget == Budget(calls=20, seconds=600)
    assert 版1.owner == Owner(person=Human(name="座長"))
    assert 版1.source == Source(location="data/請求.csv")
    assert 版1.max_retries == 3


# ——— 共通の義務（この値に効くもの） ———


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert 版() == 版()
    assert {版(): "有効"}[版()] == "有効"


def test_版は積むだけ_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        版().number = 2  # type: ignore[misc]


# ——— どれか欠けて作れたら赤 ———


@pytest.mark.parametrize("欠ける欄", list(版の欄()))
def test_どれか欠けたら版は作れない(欠ける欄: str) -> None:
    欄 = 版の欄()
    del 欄[欠ける欄]
    with pytest.raises(ValidationError):
        Version(**欄)


def test_やることの空な版は作れない() -> None:
    with pytest.raises(ValidationError):
        Instruction(text="")


# ——— 数の義務 ———


@pytest.mark.parametrize("番号", [0, -1])
def test_版の番号が1未満なら作れない(番号: int) -> None:
    with pytest.raises(ValidationError):
        Version(**{**版の欄(), "number": 番号})


def test_版の番号は1から始められる() -> None:
    assert Version(**{**版の欄(), "number": 1}).number == 1


@pytest.mark.parametrize("日数", [0, -1])
def test_終えるまでの日数が1未満なら作れない(日数: int) -> None:
    with pytest.raises(ValidationError):
        Version(**{**版の欄(), "days": 日数})


def test_終えるまでの日数は1日でよい() -> None:
    assert Version(**{**版の欄(), "days": 1}).days == 1


def test_やり直しの上限が負なら作れない() -> None:
    with pytest.raises(ValidationError):
        Version(**{**版の欄(), "max_retries": -1})


def test_やり直しの上限は0でよい() -> None:
    assert Version(**{**版の欄(), "max_retries": 0}).max_retries == 0


# ——— 写す ———


def test_写すと束が返る_中身は版と同じ() -> None:
    束 = 版().copy_for(Period(text="2026-08"))
    assert isinstance(束, Copied)
    assert 束.instruction == 版().instruction
    assert 束.cycle is Cycle.MONTHLY
    assert 束.owner == Owner(person=Human(name="座長"))
    assert 束.budget == Budget(calls=20, seconds=600)
    assert 束.source == Source(location="data/請求.csv")
    assert 束.max_retries == 3


def test_束は終えるまでの日数を持つ() -> None:
    assert 版().copy_for(Period(text="2026-08")).days == 5


def test_束は版そのものを持たない() -> None:
    束 = 版().copy_for(Period(text="2026-08"))
    assert not hasattr(束, "number")
    assert not hasattr(束, "version")


def test_写すときに対象期間を開く() -> None:
    束 = 版().copy_for(Period(text="2026-08"))
    assert 束.criteria.required_terms == ("2026-08 の請求書",)
    assert 束.criteria.opened


def test_週の対象期間でも開く() -> None:
    束 = Version(**{**版の欄(), "cycle": Cycle.WEEKLY}).copy_for(Period(text="2026-W34"))
    assert 束.criteria.required_terms == ("2026-W34 の請求書",)


def test_対象期間が無ければ開かない() -> None:
    束 = 版().copy_for(None)
    assert 束.criteria.required_terms == ("{対象期間} の請求書",)
    assert not 束.criteria.opened


def test_穴の無い版は対象期間が無くても開いている() -> None:
    欄 = {**版の欄(), "criteria": AcceptanceCriteria(required_terms=("請求書",))}
    assert Version(**欄).copy_for(None).criteria.opened


def test_写しても版は変わらない() -> None:
    版1 = 版()
    版1.copy_for(Period(text="2026-08"))
    assert 版1.criteria.required_terms == ("{対象期間} の請求書",)


def test_同じ対象期間へ写せば同じ束になる() -> None:
    期間 = Period(text="2026-08")
    assert 版().copy_for(期間) == 版().copy_for(期間)


def test_束はどれか欠けたら作れない() -> None:
    with pytest.raises(ValidationError):
        Copied(  # type: ignore[call-arg]
            instruction=Instruction(text="やること"),
            criteria=AcceptanceCriteria(required_terms=("請求書",)),
            cycle=Cycle.MONTHLY,
            owner=Owner(person=Human(name="座長")),
            budget=Budget(calls=20, seconds=600),
            source=Source(location="data/請求.csv"),
            max_retries=3,
        )


def test_穴あきの源は患者で開かれて写る() -> None:
    """筋道 §1 create——写すときに穴を患者記号で開く。"""
    欄 = {**版の欄(), "source": Source(location="db:chart/{患者}")}
    束 = Version(**欄).copy_for(Period(text="2026-08"), "P-004")
    assert 束.source == Source(location="db:chart/P-004")


def test_穴あきの源に患者が無ければ写せない() -> None:
    """穴の開いていない源を持つ仕事が作れたら赤（仕事とは何か §3 Source）。"""
    欄 = {**版の欄(), "source": Source(location="db:chart/{患者}")}
    with pytest.raises(ValueError):
        Version(**欄).copy_for(Period(text="2026-08"))
