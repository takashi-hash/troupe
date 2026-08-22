"""承認するの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I6・I7。"""

from __future__ import annotations

import pytest

from domain.aggregates.job.approve import approve
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import AwaitingApproval, Cleared
from domain.events.job.approved import Approved
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner
from tests.aggregates.job.conftest import make_job, いま, 座長


def _awaiting() -> Job[AwaitingApproval]:
    return make_job(
        AwaitingApproval(assignee=Owner(person=座長)), result_at="result://1"
    )


def test_承認待ちから承認済みへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = approve(_awaiting(), by=座長, now=いま)
    assert isinstance(仕事.state, Cleared)
    assert 仕事.state.approval.by == 座長
    assert isinstance(出来事, Approved) and 出来事.by == 座長 and 出来事.at == いま


def test_受け持ちの人でなければ承認できない() -> None:
    """I6。"""
    with pytest.raises(ValueError, match="受け持ちの人"):
        approve(_awaiting(), by=Human(name="別の人"), now=いま)


def test_承認済みの仕事は持ちものを引き継ぐ() -> None:
    元 = _awaiting()
    仕事, _ = approve(元, by=座長, now=いま)
    assert 仕事.id == 元.id and 仕事.origin == 元.origin
    assert 仕事.result_at == "result://1"
