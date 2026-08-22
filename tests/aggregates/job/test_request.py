"""頼むの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I3・I7・I12。"""

from __future__ import annotations

from datetime import timedelta

import pytest

from domain.aggregates.job.life import Created
from domain.aggregates.job.request import request
from domain.events.job.job_created import JobCreated
from domain.events.job.job_requested import JobRequested
from domain.values.job.due_date import DueDate
from domain.values.job.job_id import JobId
from domain.values.job.origin import Origin
from domain.values.job.request import Request
from tests.aggregates.job.conftest import make_copied, いま, 座長


def _req() -> Request:
    return Request(by=座長, at=いま, body="今週の依存も棚卸しして")


def test_無いから作られたへ_出来事が2つ一緒に返る() -> None:
    """I1 が型になる——1つの遷移で出来事が2つ残る道。頼めるのは人だけ（I7）。"""
    仕事, 頼まれた, 作られた = request(JobId(text="J-0002"), "R-0001", _req(), make_copied(), いま)
    assert isinstance(仕事.state, Created)
    assert isinstance(頼まれた, JobRequested)
    assert 頼まれた.by == 座長
    assert 頼まれた.body == "今週の依存も棚卸しして"
    assert isinstance(作られた, JobCreated) and 作られた.by == 座長


def test_依頼発は版を持たない() -> None:
    """生まれた版と対象期間は三つとも空——JobCreated の欄も三つ空。"""
    仕事, _, 作られた = request(JobId(text="J-0002"), "R-0001", _req(), make_copied(), いま)
    assert 仕事.born_of is None and 仕事.born_version is None and 仕事.period is None
    assert 作られた.rule_name is None and 作られた.version is None and 作られた.period is None


def test_作成元は依頼の識別子から() -> None:
    """I3 — 同じ依頼から仕事は二度作られない鍵。"""
    仕事, _, _ = request(JobId(text="J-0002"), "R-0001", _req(), make_copied(), いま)
    assert 仕事.origin == Origin.from_request("R-0001")


def test_期日の起点は依頼の時刻() -> None:
    """I12 — 頼まれてから数える。作られた時刻ではない。"""
    依頼 = Request(by=座長, at=いま - timedelta(hours=2), body="今週の依存も棚卸しして")
    仕事, _, _ = request(JobId(text="J-0002"), "R-0001", 依頼, make_copied(), いま)
    assert 仕事.due == DueDate.from_start(依頼.at, 3)


def test_写すものはぜんぶ束から() -> None:
    束 = make_copied()
    仕事, _, _ = request(JobId(text="J-0002"), "R-0001", _req(), 束, いま)
    assert 仕事.instruction == 束.instruction and 仕事.criteria == 束.criteria
    assert 仕事.owner == 束.owner and 仕事.budget == 束.budget
    assert 仕事.source == 束.source and 仕事.cycle == 束.cycle
    assert 仕事.max_retries == 束.max_retries


def test_空の依頼の識別子からは作れない() -> None:
    """義務が拒む——I3 の鍵が空では、二度作らないを守れない。"""
    with pytest.raises(ValueError, match="依頼の識別子"):
        request(JobId(text="J-0002"), " ", _req(), make_copied(), いま)
