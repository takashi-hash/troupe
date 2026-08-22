"""失敗を仕分けるの壊しかた。設計/仕事とは何か.md §6 遷移表・仕事が回る筋道.md §1。

**届いていなければやり直す（回数+1）。どちらか届いていれば残す。**
比べるだけ——4つとも仕事が持つ（make_job は上限 calls=20・seconds=600・やり直し20）。
"""

from __future__ import annotations

import pytest

from domain.aggregates.job.life import Failed, Ready
from domain.aggregates.job.sort_failures import sort_failures
from domain.events.job.retried import Retried
from domain.value_objects.job.spent import Spent
from domain.value_objects.people.clock import Clock
from tests.aggregates.job.conftest import make_job, いま

落ちた = Failed(fallen="源が読めませんでした")


def test_届いていなければ着手できるへ_回数が1増えた出来事が返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    結果 = sort_failures(
        make_job(落ちた, spent=Spent(calls=3, seconds=120), retried=2), now=いま
    )
    assert 結果 is not None
    仕事, 出来事 = 結果
    assert isinstance(仕事.state, Ready)
    assert 仕事.retried == 3
    assert 仕事.spent == Spent(calls=3, seconds=120)  # 差し戻しと違い、使った量は戻らない
    assert isinstance(出来事, Retried)
    assert 出来事.times == 3 and 出来事.by == Clock() and 出来事.at == いま


def test_やり直しが上限に届いていれば残す() -> None:
    """遷移しない——見立てを付けるのは AI の巡回、決めるのは人。"""
    assert sort_failures(make_job(落ちた, retried=20), now=いま) is None


def test_使った量の回数が上限に届いていれば残す() -> None:
    assert (
        sort_failures(make_job(落ちた, spent=Spent(calls=20, seconds=0)), now=いま)
        is None
    )


def test_使った量の秒が上限に届いていれば残す() -> None:
    assert (
        sort_failures(make_job(落ちた, spent=Spent(calls=0, seconds=600)), now=いま)
        is None
    )


def test_上限を超えていても仕分けは残すと言える() -> None:
    """I14 の守る場所は積む操作。仕分けは比べるだけ——超えた姿が帳簿から来ても残すへ倒れる。"""
    assert sort_failures(make_job(落ちた, spent=Spent(calls=21, seconds=0)), now=いま) is None
