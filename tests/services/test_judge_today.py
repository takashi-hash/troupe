"""今日に出すかの壊しかた。設計/人に見えるもの.md §4 の表を1行1テストで。"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.services.judge_today import judge_today
from domain.value_objects.job.assessment import Assessment
from tests.services.conftest import make_material, いま

見立て = Assessment(
    finding="20回とも同じ理由で落ちた", reason="源の在りかが変わった可能性が高い"
)

期日の翌朝 = datetime(2026, 8, 21, 9, 0, tzinfo=UTC)


# ---------- 出すもの ----------


def test_承認を待っているは出る() -> None:
    material = make_material(state_name="AwaitingApproval")
    assert judge_today(material, ("approve", "send_back"), いま) is True


def test_答えを待っているは出る() -> None:
    material = make_material(
        state_name="AwaitingAnswer", question_body="源の場所は変わりましたか", result_body=None
    )
    assert judge_today(material, ("answer",), いま) is True


def test_見立てが書かれた実行中は出る() -> None:
    material = make_material(state_name="InProgress", assessments=(見立て,))
    assert judge_today(material, ("send_back", "abandon"), いま) is True


def test_見立てが書かれた失敗は出る() -> None:
    material = make_material(state_name="Failed", assignee_name=None, assessments=(見立て,))
    assert judge_today(material, ("send_back", "abandon"), いま) is True


def test_見立てが書かれても実行中と失敗以外の行にはならない() -> None:
    """限る——自己申告に見立てがあっても、確かめ期日が来るまでは出ない。"""
    material = make_material(
        state_name="FinishedPendingRecheck",
        assessments=(見立て,),
        recheck_at=datetime(2026, 8, 24, 9, 0, tzinfo=UTC),
    )
    assert judge_today(material, ("send_back",), いま) is False


def test_期日を過ぎていて人が押せる操作があれば出る() -> None:
    material = make_material(state_name="Failed", assignee_name=None)
    assert judge_today(material, ("send_back", "abandon"), 期日の翌朝) is True


def test_確かめ期日が来た自己申告は出る() -> None:
    material = make_material(
        state_name="FinishedPendingRecheck",
        recheck_at=datetime(2026, 8, 18, 9, 0, tzinfo=UTC),
    )
    assert judge_today(material, ("send_back",), いま) is True


def test_やり直しが尽きて残っているは出る() -> None:
    material = make_material(state_name="Failed", assignee_name=None, retried=3)
    assert judge_today(material, ("send_back", "abandon"), いま) is True


# ---------- 出さないもの ----------


def test_実行中で見立ての書かれていない仕事は出ない() -> None:
    """人がいまできることが無い——押せることが空で来る。"""
    material = make_material(state_name="InProgress")
    assert judge_today(material, (), いま) is False


def test_自動でやり直している最中の失敗は出ない() -> None:
    material = make_material(state_name="Failed", assignee_name=None)
    assert judge_today(material, (), いま) is False


def test_期日前で押せる操作が無い仕事は出ない() -> None:
    """先の予定は今日に載せない——赤が埋もれる。"""
    material = make_material(state_name="Ready", assignee_name=None, result_body=None)
    assert judge_today(material, (), いま) is False


def test_押せる操作があれば期日前でも出る() -> None:
    material = make_material(state_name="AwaitingApproval")
    assert いま < material.due.at
    assert judge_today(material, ("approve", "send_back"), いま) is True


def test_終わった仕事と打ち切った仕事は出ない() -> None:
    for state in ("Finished", "Abandoned"):
        material = make_material(state_name=state, assignee_name=None)
        assert judge_today(material, (), いま) is False


def test_押せることが空なら必ず偽() -> None:
    """各行が「人がいま押せること」を1つ以上持つ。持たない行は出さない。"""
    material = make_material(state_name="AwaitingApproval", retried=3)
    assert judge_today(material, (), 期日の翌朝) is False
