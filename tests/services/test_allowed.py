"""押せることの壊しかた。設計/仕事が回る筋道.md §2「仕様」・人に見えるもの §3。"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.services.allowed import allowed
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.people.human import Human
from tests.services.conftest import make_material, いま, 座長

見立て = Assessment(
    finding="20回とも同じ理由で落ちた", reason="源の在りかが変わった可能性が高い"
)


def test_受け持ちの人にだけ() -> None:
    """承認する・差し戻す・答える・打ち切るは、受け持ちの人以外には1つも返さない。"""
    for state, over in (
        ("AwaitingApproval", {}),
        ("AwaitingAnswer", {}),
        ("InProgress", {"assessments": (見立て,)}),
        ("Failed", {"assignee_name": None, "retried": 3}),
    ):
        material = make_material(state_name=state, **over)
        assert allowed(material, 座長, いま), f"{state} で受け持ちの人に何も出ない"
        assert allowed(material, Human(name="別の人"), いま) == ()


def test_承認待ちは承認するか差し戻す() -> None:
    assert allowed(make_material(state_name="AwaitingApproval"), 座長, いま) == (
        "approve",
        "send_back",
    )


def test_答え待ちは答えるだけ() -> None:
    material = make_material(state_name="AwaitingAnswer", question_body="源の場所は変わりましたか")
    assert allowed(material, 座長, いま) == ("answer",)


def test_実行中は見立てを読んでから差し戻すか打ち切る() -> None:
    """見立てが書かれるまで、人がいまできることは無い。"""
    assert allowed(make_material(state_name="InProgress"), 座長, いま) == ()
    material = make_material(state_name="InProgress", assessments=(見立て,))
    assert allowed(material, 座長, いま) == ("send_back", "abandon")


def test_失敗は見立てかやり直しが尽きてから差し戻すか打ち切る() -> None:
    """自動でやり直している最中は空——残ってはいない。"""
    assert allowed(make_material(state_name="Failed", assignee_name=None), 座長, いま) == ()
    書かれた = make_material(state_name="Failed", assignee_name=None, assessments=(見立て,))
    assert allowed(書かれた, 座長, いま) == ("send_back", "abandon")
    尽きた = make_material(state_name="Failed", assignee_name=None, retried=3)
    assert allowed(尽きた, 座長, いま) == ("send_back", "abandon")


def test_自己申告は確かめ期日が来てから差し戻す() -> None:
    まだ = make_material(
        state_name="FinishedPendingRecheck",
        recheck_at=datetime(2026, 8, 24, 9, 0, tzinfo=UTC),
    )
    来た = make_material(
        state_name="FinishedPendingRecheck",
        recheck_at=datetime(2026, 8, 18, 9, 0, tzinfo=UTC),
    )
    assert allowed(まだ, 座長, いま) == ()
    assert allowed(来た, 座長, いま) == ("send_back",)


def test_遷移表に無い操作は返さない() -> None:
    """人の操作の無い状態と終点は、受け持ちの人にも空。"""
    for state in ("Created", "Ready", "Submitted", "Cleared", "Finished", "Abandoned"):
        material = make_material(state_name=state, assignee_name=None)
        assert allowed(material, 座長, いま) == (), f"{state} に操作が出た"
