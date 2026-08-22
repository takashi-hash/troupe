"""業務ルールの集約の値の壊しかた。

設計: 設計/仕事とは何か.md §3。**版が決めるもの。**
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.rule.values import (
    AcceptanceCriteria,
    Budget,
    Instruction,
    RuleName,
    Source,
    Version,
)
from domain.shared import Cycle, Human, Owner, Period

ALICE = Human(name="座長")
OWNER = Owner(person=ALICE)
SRC = Source(locator="deps://prod")


def _version(**over: object) -> Version:
    base: dict[str, object] = dict(
        number=1,
        instruction=Instruction(text="依存の一覧を取り更新が来ているものを挙げる"),
        criteria=AcceptanceCriteria(must_contain=("{対象期間}",)),
        cycle=Cycle.WEEKLY,
        days=3,
        budget=Budget(calls=20, seconds=600),
        owner=OWNER,
        source=SRC,
        max_retries=20,
    )
    return Version(**(base | over))  # type: ignore[arg-type]


def test_版が写すものの束を渡す() -> None:
    """版そのものは渡さない。写すとき受け入れ基準の差し込みを開く。"""
    copied = _version().copy_for(Period(text="2026-W34"))
    assert copied.criteria.must_contain == ("2026-W34",)
    assert copied.criteria.opened
    assert copied.days == 3  # 日数は束に入る。仕事は持たない

def test_空の業務ルールの識別子() -> None:
    with pytest.raises(ValidationError):
        RuleName(text="")


def test_ゼロや負の使用上限() -> None:
    for calls, seconds in ((0, 600), (20, 0), (-1, 600)):
        with pytest.raises(ValidationError):
            Budget(calls=calls, seconds=seconds)


def test_やることの空な版() -> None:
    with pytest.raises(ValidationError):
        Instruction(text="")
    with pytest.raises(ValidationError):
        _version(number=0)
    with pytest.raises(ValidationError):
        _version(days=0)


def test_空の源() -> None:
    with pytest.raises(ValidationError):
        Source(locator="")


def test_必ず含む語が空では作れない() -> None:
    with pytest.raises(ValidationError):
        AcceptanceCriteria(must_contain=())
    with pytest.raises(ValidationError):
        AcceptanceCriteria(must_contain=("",))


def test_対象期間の差し込みが写すときに開く() -> None:
    c = AcceptanceCriteria(must_contain=("{対象期間}", "更新"), explanation="今週の日付であること")
    assert not c.opened
    opened = c.expand(Period(text="2026-W34"))
    assert opened.must_contain == ("2026-W34", "更新")
    assert opened.opened
    assert opened.explanation == c.explanation


def test_開かれていない差し込みは検査に届いてはいけない() -> None:
    assert not AcceptanceCriteria(must_contain=("{対象期間}",)).opened
