"""打ち切るの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I7。

**終点。** 打ち切った人と理由が状態に残る。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.abandon import abandon
from domain.aggregates.job.life import TERMINAL, Abandoned, Failed, InProgress
from domain.events.job.job_abandoned import JobAbandoned
from domain.value_objects.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま, 座長


def test_実行中から打ち切られたへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    元 = make_job(InProgress(assignee=Agent(name="一号")))
    仕事, 出来事 = abandon(元, by=座長, reason="源が廃止されました", now=いま)
    assert isinstance(仕事.state, Abandoned)
    assert isinstance(出来事, JobAbandoned)
    assert 出来事.by == 座長 and 出来事.at == いま and 出来事.reason == "源が廃止されました"


def test_失敗したから打ち切られたへ_人と理由が状態に残る() -> None:
    元 = make_job(Failed(fallen="20回とも同じ理由で落ちました"))
    仕事, _ = abandon(元, by=座長, reason="源の在りかが変わり、もう追えません", now=いま)
    assert isinstance(仕事.state, Abandoned)
    assert 仕事.state.by == 座長
    assert 仕事.state.reason == "源の在りかが変わり、もう追えません"


def test_打ち切りは終点() -> None:
    仕事, _ = abandon(
        make_job(Failed(fallen="落ちました")), by=座長, reason="追えません", now=いま
    )
    assert type(仕事.state).__name__ in TERMINAL


def test_打ち切られた仕事は持ちものを引き継ぐ() -> None:
    元 = make_job(Failed(fallen="落ちました"))
    仕事, _ = abandon(元, by=座長, reason="追えません", now=いま)
    assert 仕事.id == 元.id and 仕事.origin == 元.origin


def test_理由が空だと打ち切れない() -> None:
    """義務が拒む——理由の無い打ち切られたが書けない。"""
    with pytest.raises(ValidationError):
        abandon(make_job(Failed(fallen="落ちました")), by=座長, reason="  ", now=いま)


def test_AIは打ち切れない() -> None:
    """I7——`by` の型が `Human`。"""
    with pytest.raises(ValidationError):
        abandon(
            make_job(Failed(fallen="落ちました")),
            by=Agent(name="一号"),  # type: ignore[arg-type]
            reason="やめます",
            now=いま,
        )
