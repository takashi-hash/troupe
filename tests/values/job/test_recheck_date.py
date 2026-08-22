"""確かめ期日の壊しかた。設計/仕事とは何か.md §3・I5。

**期日より後**。**送るたびに先へ進む。** 次にいつ確かめるかを AI は決めない。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from domain.values.calendar.cycle import Cycle
from domain.values.job.due_date import DueDate
from domain.values.job.recheck_date import RecheckDate

起点 = datetime(2026, 8, 22, 9, 0, tzinfo=UTC)
期日 = DueDate.from_start(起点, 3)


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    確かめ = RecheckDate.first(期日, Cycle.WEEKLY)
    同じ = RecheckDate.first(期日, Cycle.WEEKLY)
    assert 確かめ == 同じ
    assert {確かめ: "確かめ待ち"}[同じ] == "確かめ待ち"


def test_作ったあと書き換えられない() -> None:
    確かめ = RecheckDate.first(期日, Cycle.WEEKLY)
    with pytest.raises(ValidationError):
        確かめ.at = 期日.at + timedelta(days=90)  # type: ignore[misc]


def test_期日より後の確かめ期日は作れる() -> None:
    確かめ = RecheckDate(after=期日.at, at=期日.at + timedelta(days=1))
    assert 確かめ.at == datetime(2026, 8, 26, 9, 0, tzinfo=UTC)


def test_期日より前の確かめ期日は作れない() -> None:
    with pytest.raises(ValidationError):
        RecheckDate(after=期日.at, at=期日.at - timedelta(seconds=1))


def test_期日と同じ時刻の確かめ期日は作れない() -> None:
    with pytest.raises(ValidationError):
        RecheckDate(after=期日.at, at=期日.at)


def test_はじめの確かめ期日は_期日に週の周期を足したもの() -> None:
    assert RecheckDate.first(期日, Cycle.WEEKLY).at == datetime(
        2026, 9, 1, 9, 0, tzinfo=UTC
    )


def test_はじめの確かめ期日は_期日に月の周期を足したもの() -> None:
    assert RecheckDate.first(期日, Cycle.MONTHLY).at == datetime(
        2026, 9, 25, 9, 0, tzinfo=UTC
    )


def test_送ると先へ進む() -> None:
    確かめ = RecheckDate.first(期日, Cycle.WEEKLY)
    assert 確かめ.push(Cycle.WEEKLY).at > 確かめ.at


def test_送ったさきは_前の確かめ期日に周期を足したもの() -> None:
    確かめ = RecheckDate.first(期日, Cycle.WEEKLY)
    assert 確かめ.push(Cycle.WEEKLY).at == datetime(2026, 9, 8, 9, 0, tzinfo=UTC)


def test_何度送っても進み続ける() -> None:
    確かめ = RecheckDate.first(期日, Cycle.MONTHLY)
    for _ in range(5):
        送った = 確かめ.push(Cycle.MONTHLY)
        assert 送った.at > 確かめ.at
        確かめ = 送った


def test_送ると基準が前の確かめ期日に移る() -> None:
    """基準が移るから「送って進まない値」は型が作らせない。期日を丸ごとは抱えない。"""
    確かめ = RecheckDate.first(期日, Cycle.WEEKLY)
    assert 確かめ.push(Cycle.WEEKLY).after == 確かめ.at
