"""見回る（app）の壊しかた。設計/仕事が回る筋道.md §1「AI が始めるもの」。"""

from __future__ import annotations

from app.ports.work_reader import WorkMaterial
from app.services.agent.patrol import patrol
from domain.aggregates.job.life import Failed, FinishedPendingRecheck, InProgress
from domain.events.job.assessment_written import AssessmentWritten
from domain.events.job.job_failed import JobFailed
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.job.approval import Approval
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.reply import Reply
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.recheck_date import RecheckDate
from domain.value_objects.job.spent import Spent
from tests.aggregates.job.conftest import make_job, いま, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物
from tests.app.services.agent.conftest import (
    働き手,
    材料読みの偽物,
    状態読みの偽物,
)


def _見回る(
    帳簿: 帳簿の偽物, 状態読み: 状態読みの偽物, 材料読み: 材料読みの偽物
) -> tuple[JobId, ...]:
    return patrol(帳簿, 状態読み, 材料読み, 状況読みの偽物(), 固定時計(), by=働き手)


class 状況読みの偽物:
    """巡回の口の偽物——決めた見立てを返す。"""

    def __init__(self, finding: str = "源の在りかが変わった可能性が高い", reason: str = "止まった理由が全部同じ") -> None:
        self.finding, self.reason = finding, reason
        self.calls = 0

    def consult(
        self,
        instruction: str,
        criteria_terms: tuple[str, ...],
        criteria_note: str,
        source_material: str,
        answered_questions: tuple[tuple[str, str], ...],
        previous_result: str | None,
    ) -> tuple[Reply, int, int]:
        raise AssertionError("巡回が consult を呼んだ")

    def read_situation(
        self,
        situation: str,
        fall_reasons: tuple[str, ...],
        previous_result: str | None,
        sibling_states: tuple[str, ...],
    ) -> tuple[str, str, int, int]:
        self.calls += 1
        return self.finding, self.reason, 1, 3


def test_尽きた仕事に見立てが付く() -> None:
    """2つ目が無いと、落ちた仕事に見立てが付かない——状態は変えずに見立てだけ刻む。
    引き金は**やり直しが尽きた**（時計がまだ仕分ける仕事は拾わない——実機で
    1回目の失敗に書いて、やり直し0回のまま古びた）。本文は LLM が状況を読んだ言葉。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="源に接続できませんでした"), retried=20)
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
    動いた = _見回る(帳簿, 状態読みの偽物({"Failed": (仕事.id,)}), 材料読み)
    assert 動いた == (仕事.id,)
    書かれた = next(e for e in 帳簿.events if isinstance(e, AssessmentWritten))
    assert 書かれた.assessment.finding == "源の在りかが変わった可能性が高い"
    assert 書かれた.assessment.reason == "止まった理由が全部同じ"  # LLM の言葉がそのまま届く
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Failed)  # 状態は変わらない
    assert [type(e) for e in 帳簿.events] == [AssessmentWritten]


def test_見立てが既に在れば書かない() -> None:
    """F6——同じ見立てを二度書かない。判定したのは仕様。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="源に接続できませんでした"), retried=20)
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
    動いた = _見回る(帳簿, 状態読みの偽物({"Failed": (仕事.id,)}), 材料読み)
    assert 動いた == () and not 帳簿.events


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
    動いた = _見回る(
        帳簿, 状態読みの偽物({"FinishedPendingRecheck": (仕事.id,)}), 材料読みの偽物()
    )
    assert 動いた == (仕事.id,)
    書かれた = next(e for e in 帳簿.events if isinstance(e, AssessmentWritten))
    assert 書かれた.assessment.finding == "源の在りかが変わった可能性が高い"  # 本文は LLM の言葉
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
    動いた = _見回る(帳簿, 状態読みの偽物({"InProgress": (仕事.id,)}), 材料読み)
    assert 動いた == (仕事.id,)
    書かれた = next(e for e in 帳簿.events if isinstance(e, AssessmentWritten))
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Failed) and 後.state.fallen == 書かれた.assessment.finding  # 落ちた中身＝見立ての本文
    assert [type(e) for e in 帳簿.events] == [AssessmentWritten, JobFailed]


def test_行き詰まっていなければ触らない() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手))
    帳簿.jobs[仕事.id] = 仕事
    動いた = _見回る(帳簿, 状態読みの偽物({"InProgress": (仕事.id,)}), 材料読みの偽物())
    assert 動いた == () and not 帳簿.events
    assert 帳簿.jobs[仕事.id] == 仕事
