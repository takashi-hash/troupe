"""仕事の一生の壊しかた。設計/仕事とは何か.md §6・§7「禁止状態」。"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.aggregates.job.life import (
    STATE_WORDS,
    TERMINAL,
    Abandoned,
    AwaitingAnswer,
    AwaitingApproval,
    Cleared,
    Failed,
    InProgress,
    Ready,
    State,
)
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner


def test_担当の無い実行中が書けない() -> None:
    with pytest.raises(ValidationError):
        InProgress()  # type: ignore[call-arg]


def test_担当の無い答え待ちが書けない() -> None:
    with pytest.raises(ValidationError):
        AwaitingAnswer()  # type: ignore[call-arg]


def test_承認なしの承認済みが書けない() -> None:
    with pytest.raises(ValidationError):
        Cleared()  # type: ignore[call-arg]


def test_承認を持ったまま着手できるへ戻れない() -> None:
    """承認の欄そのものが無い。"""
    assert "approval" not in Ready.model_fields
    with pytest.raises(ValidationError):
        Ready(approval="x")  # type: ignore[call-arg]


def test_受け持ちの人以外は承認待ちを持てない() -> None:
    AwaitingApproval(assignee=Owner(person=Human(name="座長")))
    with pytest.raises(ValidationError):
        AwaitingApproval(assignee=Agent(name="一号"))  # type: ignore[arg-type]


def test_落ちた中身の無い失敗が書けない() -> None:
    with pytest.raises(ValidationError):
        Failed(fallen="")


def test_理由の無い打ち切りが書けない() -> None:
    with pytest.raises(ValidationError):
        Abandoned(by=Human(name="座長"), reason="")


def test_打ち切れるのは人だけ() -> None:
    with pytest.raises(ValidationError):
        Abandoned(by=Agent(name="一号"), reason="源が直らない")  # type: ignore[arg-type]


def test_状態は素の文字列から作れない() -> None:
    ta = TypeAdapter(State)
    assert ta.validate_python(Ready()) == Ready()
    with pytest.raises(ValidationError):
        ta.validate_python("実行中")


def test_急ぎの印がどの状態にも無い() -> None:
    """設計 §7 — そういう欄が無い。急ぎは「期日が今日」で表す。"""
    for word, ident in STATE_WORDS.items():
        state = TypeAdapter(State).core_schema  # ただ列挙の確認
    from domain.aggregates.job import life

    for ident in STATE_WORDS.values():
        cls = getattr(life, ident)
        assert not {"urgent", "priority", "急ぎ"} & set(cls.model_fields), ident


def test_終点は2つ() -> None:
    assert TERMINAL == {"Finished", "Abandoned"}
