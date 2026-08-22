"""見回る（app）の壊しかた。設計/仕事が回る筋道.md §1「AI が始めるもの」。"""

from __future__ import annotations

from app.ports.work_reader import WorkMaterial
from app.services.agent.patrol import patrol
from domain.aggregates.job.life import Failed, FinishedPendingRecheck, InProgress
from domain.events.job.assessment_written import AssessmentWritten
from domain.events.job.job_failed import JobFailed
from domain.values.calendar.cycle import Cycle
from domain.values.job.approval import Approval
from domain.values.job.assessment import Assessment
from domain.values.job.due_date import DueDate
from domain.values.job.job_id import JobId
from domain.values.job.recheck_date import RecheckDate
from domain.values.job.spent import Spent
from tests.aggregates.job.conftest import make_job, いま, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物
from tests.app.services.agent.conftest import (
    働き手,
    材料読みの偽物,
    状態読みの偽物,
    見立て置き場の偽物,
)


def _見回る(
    帳簿: 帳簿の偽物, 状態読み: 状態読みの偽物, 材料読み: 材料読みの偽物
) -> tuple[tuple[JobId, ...], 見立て置き場の偽物]:
    見立て = 見立て置き場の偽物()
    動いた = patrol(帳簿, 状態読み, 材料読み, 見立て, 固定時計(), by=働き手)
    return 動いた, 見立て


def test_落ちた仕事に見立てが付く() -> None:
    """2つ目が無いと、落ちた仕事に見立てが付かない——状態は変えずに見立てだけ刻む。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="源に接続できませんでした"))
    帳簿.jobs[仕事.id] = 仕事
    材料読み = 材料読みの偽物(
        WorkMaterial(
            answered_questions=(),
            previous_result=None,
            fall_reasons=("源に接続できませんでした",),
            assessments=(),
            sibling_states=(),
        )
    )
    動いた, 見立て = _見回る(帳簿, 状態読みの偽物({"Failed": (仕事.id,)}), 材料読み)
    assert 動いた == (仕事.id,)
    (行,) = 見立て.rows
    assert 行[0] == 仕事.id and "源に接続できませんでした" in 行[1].finding
    assert 行[1].reason  # 理由の空な見立ては型が拒む——中身も入っている
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Failed)  # 状態は変わらない
    assert [type(e) for e in 帳簿.events] == [AssessmentWritten]


def test_見立てが既に在れば書かない() -> None:
    """F6——同じ見立てを二度書かない。判定したのは仕様。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="源に接続できませんでした"))
    帳簿.jobs[仕事.id] = 仕事
    材料読み = 材料読みの偽物(
        WorkMaterial(
            answered_questions=(),
            previous_result=None,
            fall_reasons=("源に接続できませんでした",),
            assessments=(Assessment(finding="源の在りかが変わった可能性", reason="同じ理由で落ちた"),),
            sibling_states=(),
        )
    )
    動いた, 見立て = _見回る(帳簿, 状態読みの偽物({"Failed": (仕事.id,)}), 材料読み)
    assert 動いた == () and not 見立て.rows and not 帳簿.events


def test_根拠なしで終わった仕事に見立てが付く() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(
        FinishedPendingRecheck(
            approval=Approval(by=座長, at=いま),
            recheck=RecheckDate.first(DueDate.from_start(いま, 3), Cycle.WEEKLY),
        ),
        result_at="result://1",
        spent=Spent(calls=20, seconds=0),  # 上限（calls=20）に触れている
    )
    帳簿.jobs[仕事.id] = 仕事
    動いた, 見立て = _見回る(
        帳簿, 状態読みの偽物({"FinishedPendingRecheck": (仕事.id,)}), 材料読みの偽物()
    )
    assert 動いた == (仕事.id,)
    (行,) = 見立て.rows
    assert "根拠" in 行[1].finding
    assert isinstance(帳簿.jobs[仕事.id].state, FinishedPendingRecheck)  # 状態は変わらない
    assert [type(e) for e in 帳簿.events] == [AssessmentWritten]


def test_実行中で行き詰まったら人へ回す() -> None:
    """見立てを書いて失敗したへ——進めないという事実の報告。どうするかは人が決める。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手))
    帳簿.jobs[仕事.id] = 仕事
    材料読み = 材料読みの偽物(
        WorkMaterial(
            answered_questions=(),
            previous_result=None,
            fall_reasons=("同じ壁に当たった", "同じ壁に当たった"),  # 直近2回が同じ——行き詰まり
            assessments=(),
            sibling_states=(),
        )
    )
    動いた, 見立て = _見回る(帳簿, 状態読みの偽物({"InProgress": (仕事.id,)}), 材料読み)
    assert 動いた == (仕事.id,)
    (行,) = 見立て.rows
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Failed) and 後.state.fallen == 行[1].finding  # 落ちた中身＝見立ての本文
    assert [type(e) for e in 帳簿.events] == [AssessmentWritten, JobFailed]


def test_行き詰まっていなければ触らない() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手))
    帳簿.jobs[仕事.id] = 仕事
    動いた, 見立て = _見回る(帳簿, 状態読みの偽物({"InProgress": (仕事.id,)}), 材料読みの偽物())
    assert 動いた == () and not 見立て.rows and not 帳簿.events
    assert 帳簿.jobs[仕事.id] == 仕事
