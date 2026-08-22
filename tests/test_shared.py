"""どちらの集約も使う語の壊しかた。

設計: 設計/仕事とは何か.md §3 の「壊しかた」の欄。
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.job.values import JobId
from domain.shared import Actor, Agent, Assignee, Clock, Cycle, Human, Owner, Period

ALICE = Human(name="座長")

def test_同じ中身なら等しい() -> None:
    assert JobId(text="j1") == JobId(text="j1")
    # frozen が基底クラスにあると pyright が __hash__ を見ない（実物は下で確かめる）
    assert {JobId(text="j1"): 1}[JobId(text="j1")] == 1  # pyright: ignore[reportUnhashable]
    assert hash(JobId(text="j1")) == hash(JobId(text="j1"))


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        JobId(text="j1").text = "j2"  # type: ignore[misc]


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        JobId(text="j1", extra="x")  # type: ignore[call-arg]


def test_空の識別子と空の名前() -> None:
    for make in (lambda: JobId(text=""), lambda: Human(name=""), lambda: Agent(name=" ")):
        with pytest.raises(ValidationError):
            make()


def test_AI_を受け持ちの人にできない() -> None:
    with pytest.raises(ValidationError):
        Owner(person=Agent(name="一号"))  # type: ignore[arg-type]


def test_時計は担当になれない() -> None:
    """`Assignee` は人か AI のどちらか。3つ目は無い。"""
    ta = TypeAdapter(Assignee)
    assert ta.validate_python(ALICE) == ALICE
    with pytest.raises(ValidationError):
        ta.validate_python(Clock())


def test_起こす者は素の文字列から作れない() -> None:
    ta = TypeAdapter(Actor)
    assert ta.validate_python(Clock()) == Clock()
    with pytest.raises(ValidationError):
        ta.validate_python("時計")


def test_形の違う対象期間() -> None:
    for text in ("来月", "2026-13", "2026-W54", "2026/08", ""):
        with pytest.raises(ValidationError):
            Period(text=text)


def test_対象期間の形が周期を言う() -> None:
    assert Period(text="2026-08").cycle is Cycle.MONTHLY
    assert Period(text="2026-W34").cycle is Cycle.WEEKLY
