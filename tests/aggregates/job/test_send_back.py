"""差し戻すの壊しかた。設計/仕事とは何か.md §4・§6 遷移表・I1・I7。

**使った量とやり直した回数が 0 に戻る**——どの状態からでも。
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import (
    AwaitingApproval,
    Failed,
    FinishedPendingRecheck,
    InProgress,
    Ready,
    StateUnion,
)
from domain.aggregates.job.send_back import send_back
from domain.events.job.sent_back import SentBack
from domain.values.calendar.cycle import Cycle
from domain.values.job.approval import Approval
from domain.values.job.due_date import DueDate
from domain.values.job.recheck_date import RecheckDate
from domain.values.job.send_back import SendBack
from domain.values.job.spent import Spent
from domain.values.people.agent import Agent
from domain.values.people.owner import Owner
from tests.aggregates.job.conftest import make_job, いま, 座長

差し戻し = SendBack(by=座長, reason="件数が源と合っていません。8月分をもう一度数えてください")


def _使った仕事(state: StateUnion, **over: object) -> Job[Any]:
    """使った量とやり直した回数の残る仕事——戻ることを見るための元。"""
    return make_job(state, spent=Spent(calls=3, seconds=120), retried=2, **over)


def _差し戻しの後を確かめる(仕事: Job[Ready], 出来事: SentBack) -> None:
    assert isinstance(仕事.state, Ready)
    assert 仕事.spent == Spent(calls=0, seconds=0)
    assert 仕事.retried == 0
    assert isinstance(出来事, SentBack)
    assert 出来事.by == 座長 and 出来事.at == いま and 出来事.reason == 差し戻し.reason


def test_承認待ちから着手できるへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    元 = _使った仕事(AwaitingApproval(assignee=Owner(person=座長)), result_at="result://1")
    仕事, 出来事 = send_back(元, 差し戻し, now=いま)
    _差し戻しの後を確かめる(仕事, 出来事)


def test_実行中から着手できるへ_使った量と回数が0に戻る() -> None:
    元 = _使った仕事(InProgress(assignee=Agent(name="一号")))
    仕事, 出来事 = send_back(元, 差し戻し, now=いま)
    _差し戻しの後を確かめる(仕事, 出来事)


def test_失敗したから着手できるへ_使った量と回数が0に戻る() -> None:
    元 = _使った仕事(Failed(fallen="源が読めませんでした"))
    仕事, 出来事 = send_back(元, 差し戻し, now=いま)
    _差し戻しの後を確かめる(仕事, 出来事)


def test_終わった確かめ待ちから着手できるへ_使った量と回数が0に戻る() -> None:
    元 = _使った仕事(
        FinishedPendingRecheck(
            approval=Approval(by=座長, at=いま),
            recheck=RecheckDate.first(DueDate.from_start(いま, 3), Cycle.WEEKLY),
        )
    )
    仕事, 出来事 = send_back(元, 差し戻し, now=いま)
    _差し戻しの後を確かめる(仕事, 出来事)


def test_差し戻された仕事は承認を持たない() -> None:
    """禁止状態——着手できるに承認の欄そのものが無い。"""
    元 = _使った仕事(
        FinishedPendingRecheck(
            approval=Approval(by=座長, at=いま),
            recheck=RecheckDate.first(DueDate.from_start(いま, 3), Cycle.WEEKLY),
        )
    )
    仕事, _ = send_back(元, 差し戻し, now=いま)
    assert not hasattr(仕事.state, "approval")


def test_差し戻された仕事は持ちものを引き継ぐ() -> None:
    元 = _使った仕事(AwaitingApproval(assignee=Owner(person=座長)), result_at="result://1")
    仕事, _ = send_back(元, 差し戻し, now=いま)
    assert 仕事.id == 元.id and 仕事.origin == 元.origin


def test_理由の空な差し戻しでは呼べない() -> None:
    """義務が拒む——理由の無い差し戻しがそもそも組めない。"""
    with pytest.raises(ValidationError):
        SendBack(by=座長, reason="  ")


def test_AIの差し戻しでは呼べない() -> None:
    """I7——`SendBack` の `by` の型が `Human`。"""
    with pytest.raises(ValidationError):
        SendBack(by=Agent(name="一号"), reason="まだです")  # type: ignore[arg-type]
