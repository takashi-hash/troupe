"""使った量を積むの壊しかた。設計/仕事が回る筋道.md §1・仕事とは何か.md §6・I14。

上限は `make_job` の版が決めた `Budget(calls=20, seconds=600)`。
"""

from __future__ import annotations

from typing import Any

import pytest

from domain.aggregates.job.life import InProgress
from domain.aggregates.job.spend import spend
from domain.events.job.spent_increased import SpentIncreased
from domain.aggregates.job.job import Job
from domain.values.job.spent import Spent
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま

働き手 = Agent(name="一号")


def _in_progress(**over: object) -> Job[Any]:
    return make_job(InProgress(assignee=働き手), **over)


def test_状態は変わらないまま使った量が積まれる() -> None:
    仕事, 出来事 = spend(_in_progress(), calls=3, seconds=30, now=いま)
    assert 仕事.state == InProgress(assignee=働き手)
    assert 仕事.spent == Spent(calls=3, seconds=30)
    assert isinstance(出来事, SpentIncreased)
    assert 出来事.calls == 3 and 出来事.seconds == 30
    assert 出来事.by == 働き手 and 出来事.at == いま


def test_上限ちょうどまでは積める() -> None:
    """I14——上限と同じまでは収まっている。"""
    仕事, _ = spend(_in_progress(), calls=20, seconds=600, now=いま)
    assert 仕事.spent == Spent(calls=20, seconds=600)


def test_1超えたら赤_積む前に止まる() -> None:
    """I14。回数が1超えても、秒が1超えても止まる。"""
    with pytest.raises(ValueError, match="I14"):
        spend(_in_progress(), calls=21, seconds=600, now=いま)
    with pytest.raises(ValueError, match="I14"):
        spend(_in_progress(spent=Spent(calls=0, seconds=600)), calls=1, seconds=1, now=いま)


def test_壊しかた_両方0では増えていない() -> None:
    with pytest.raises(ValueError, match="増えていません"):
        spend(_in_progress(), calls=0, seconds=0, now=いま)


def test_壊しかた_負の量は積めない() -> None:
    with pytest.raises(ValueError, match="0以上"):
        spend(_in_progress(spent=Spent(calls=5, seconds=50)), calls=-1, seconds=10, now=いま)
