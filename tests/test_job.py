"""仕事の集約の値と、禁止状態の壊しかた。

設計: 設計/仕事とは何か.md §3・§6・§7。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.job.lifecycle import (
    Abandoned,
    AwaitingAnswer,
    AwaitingApproval,
    Cleared,
    Created,
    Failed,
    Finished,
    FinishedPendingRecheck,
    InProgress,
    Ready,
    State,
    Submitted,
)
from domain.job.values import (
    Answer,
    Approval,
    Assessment,
    DueDate,
    Evidence,
    JobId,
    Mark,
    Origin,
    Question,
    RecheckDate,
    Reply,
    Request,
    Result,
    SendBack,
    Spent,
)
from domain.rule.values import Budget, RuleName, Source
from domain.shared import Agent, Cycle, Human, Owner, Period

T0 = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
ALICE = Human(name="座長")
OWNER = Owner(person=ALICE)
SRC = Source(locator="deps://prod")

def test_仕事の識別子は前後に空白を持てない() -> None:
    with pytest.raises(ValidationError):
        JobId(text=" j1 ")


def test_負の使った量() -> None:
    with pytest.raises(ValidationError):
        Spent(calls=-1, seconds=0)


def test_起点より前の期日() -> None:
    with pytest.raises(ValidationError):
        DueDate(start=T0, at=T0 - timedelta(days=1))
    with pytest.raises(ValidationError):
        DueDate(start=T0, at=T0)


def test_期日は起点の時刻と日数から組む() -> None:
    assert DueDate.from_start(T0, 3).at == T0 + timedelta(days=3)


def test_引用の空な根拠() -> None:
    with pytest.raises(ValidationError):
        Evidence(quote="", read_from=SRC)


def test_誰かいつが欠けた承認() -> None:
    with pytest.raises(ValidationError):
        Approval(by=ALICE)  # type: ignore[call-arg]


def test_理由の無い差し戻しと理由の無い見立て() -> None:
    with pytest.raises(ValidationError):
        SendBack(by=ALICE, at=T0, reason="")
    with pytest.raises(ValidationError):
        Assessment(finding="20回とも同じ理由", reason="", at=T0)


def test_中身の空な成果と質問と回答と依頼と応答() -> None:
    with pytest.raises(ValidationError):
        Result(body="")
    with pytest.raises(ValidationError):
        Question(body="", to=OWNER)
    with pytest.raises(ValidationError):
        Answer(by=ALICE, at=T0, body="")
    with pytest.raises(ValidationError):
        Request(by=ALICE, at=T0, body="")
    with pytest.raises(ValidationError):
        Reply(mark=Mark.RESULT, body="")


def test_同じ中身なら同じ鍵の文字列() -> None:
    a = Origin.from_rule(RuleName(text="週次の依存の棚卸し"), 1, Period(text="2026-W34"))
    b = Origin.from_rule(RuleName(text="週次の依存の棚卸し"), 1, Period(text="2026-W34"))
    assert a == b and a.key == b.key


def test_版が違えば作成元も違う() -> None:
    rule, period = RuleName(text="週次の依存の棚卸し"), Period(text="2026-W34")
    assert Origin.from_rule(rule, 1, period) != Origin.from_rule(rule, 2, period)


def test_空の作成元は作れない() -> None:
    with pytest.raises(ValidationError):
        Origin(key="")
    with pytest.raises(ValueError):  # 鍵を組む前に弾く（ValidationError より手前）
        Origin.from_request("")


def test_確かめ期日は期日より後() -> None:
    due = DueDate.from_start(T0, 3)
    with pytest.raises(ValidationError):
        RecheckDate(after=due.at, at=due.at - timedelta(days=1))


def test_確かめ期日は送るたびに先へ進む() -> None:
    due = DueDate.from_start(T0, 3)
    first = RecheckDate.first(due, Cycle.WEEKLY)
    assert first.at == due.at + timedelta(days=7)
    pushed = first.push(Cycle.WEEKLY)
    assert pushed.at > first.at


def test_使った量は上限を超えたと言える() -> None:
    budget = Budget(calls=20, seconds=600)
    assert Spent(calls=20, seconds=600).within(budget)
    assert not Spent(calls=21, seconds=600).within(budget)
    assert not Spent(calls=20, seconds=601).within(budget)


def test_使った量は積める() -> None:
    assert Spent().plus(1, 12) == Spent(calls=1, seconds=12)



# ── 型 — 禁止状態が書けない（設計 §7）─────────────────────


def _approval() -> Approval:
    return Approval(by=ALICE, at=T0)


def test_承認なしの承認済みが書けない() -> None:
    with pytest.raises(ValidationError):
        Cleared()  # type: ignore[call-arg]


def test_担当の無い実行中が書けない() -> None:
    with pytest.raises(ValidationError):
        InProgress()  # type: ignore[call-arg]


def test_質問の無い答え待ちが書けない() -> None:
    with pytest.raises(ValidationError):
        AwaitingAnswer(assignee=Agent(name="一号"))  # type: ignore[call-arg]


def test_承認を持ったまま着手できるへ戻れない() -> None:
    with pytest.raises(ValidationError):
        Ready(approval=_approval())  # type: ignore[call-arg]


def test_受け持ちの人以外は承認待ちを持てない() -> None:
    """I6 — 承認できるのは受け持ちの人だけ。担当の型が `Owner`。"""
    AwaitingApproval(assignee=Owner(person=ALICE))
    with pytest.raises(ValidationError):
        AwaitingApproval(assignee=Agent(name="一号"))  # type: ignore[arg-type]


def test_確かめ待ちは根拠の在りかの欄を持たない() -> None:
    """設計 §6 — 終わった（確かめ待ち）は根拠の在りかを持ってはいけない。"""
    assert "evidence_at" not in FinishedPendingRecheck.model_fields
    assert "recheck" in FinishedPendingRecheck.model_fields


def test_急ぎの印がどの状態にも無い() -> None:
    """設計 §7 — そういう欄が無い。急ぎは「期日が今日」で表す。"""
    for state in (Created, Ready, InProgress, AwaitingAnswer, Submitted,
                  AwaitingApproval, Cleared, Failed, FinishedPendingRecheck,
                  Finished, Abandoned):
        assert not {"urgent", "priority", "急ぎ"} & set(state.model_fields)


def test_落ちた中身の無い失敗が書けない() -> None:
    with pytest.raises(ValidationError):
        Failed()  # type: ignore[call-arg]


def test_理由の無い打ち切りが書けない() -> None:
    with pytest.raises(ValidationError):
        Abandoned(by=ALICE)  # type: ignore[call-arg]


def test_状態は素の文字列から作れない() -> None:
    ta = TypeAdapter(State)
    assert ta.validate_python(Ready()) == Ready()
    with pytest.raises(ValidationError):
        ta.validate_python("実行中")
    with pytest.raises(ValidationError):
        ta.validate_python({"name": "存在しない状態"})


def test_終わったは承認を必ず持つ() -> None:
    Finished(approval=_approval())
    with pytest.raises(ValidationError):
        Finished()  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Submitted()  # type: ignore[call-arg]


def test_打ち切った人は人だけ() -> None:
    Abandoned(by=Human(name="座長"), reason="源が直らない")
    with pytest.raises(ValidationError):
        Abandoned(by=Agent(name="一号"), reason="源が直らない")  # type: ignore[arg-type]

