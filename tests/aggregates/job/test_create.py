"""作るの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I3・I12。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.create import create
from domain.aggregates.job.life import Created
from domain.events.job.job_created import JobCreated
from domain.values.calendar.period import Period
from domain.values.job.due_date import DueDate
from domain.values.job.job_id import JobId
from domain.values.job.spent import Spent
from domain.values.people.clock import Clock
from domain.values.rule.criteria import AcceptanceCriteria
from domain.values.rule.rule_name import RuleName
from tests.aggregates.job.conftest import make_copied, いま

規則 = RuleName(text="週次の依存の棚卸し")
期間 = Period(text="2026-W34")


def test_無いから作られたへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = create(JobId(text="J-0001"), 規則, 1, 期間, make_copied(), いま)
    assert isinstance(仕事.state, Created)
    assert isinstance(出来事, JobCreated) and 出来事.by == Clock() and 出来事.at == いま
    assert 出来事.rule_name == 規則 and 出来事.version == 1 and 出来事.period == 期間


def test_同じ版と同じ期間なら同じ作成元() -> None:
    """I3 — 二度作らない鍵。帳簿の一意の鍵はこの文字列で守る。"""
    甲, _ = create(JobId(text="J-0001"), 規則, 1, 期間, make_copied(), いま)
    乙, _ = create(JobId(text="J-0002"), 規則, 1, 期間, make_copied(), いま)
    assert 甲.origin == 乙.origin


def test_版か期間が変われば作成元も変わる() -> None:
    """版の番号も鍵の一部——版が変われば同じ対象期間でも別の仕事が生まれてよい。"""
    甲, _ = create(JobId(text="J-0001"), 規則, 1, 期間, make_copied(), いま)
    乙, _ = create(JobId(text="J-0002"), 規則, 2, 期間, make_copied(), いま)
    丙, _ = create(JobId(text="J-0003"), 規則, 1, Period(text="2026-W35"), make_copied(), いま)
    assert len({甲.origin, 乙.origin, 丙.origin}) == 3


def test_写すものはぜんぶ束から() -> None:
    束 = make_copied()
    仕事, _ = create(JobId(text="J-0001"), 規則, 1, 期間, 束, いま)
    assert 仕事.instruction == 束.instruction and 仕事.criteria == 束.criteria
    assert 仕事.owner == 束.owner and 仕事.budget == 束.budget
    assert 仕事.source == 束.source and 仕事.cycle == 束.cycle
    assert 仕事.max_retries == 束.max_retries
    assert 仕事.born_of == 規則 and 仕事.born_version == 1 and 仕事.period == 期間


def test_期日は作られた時刻が起点で版の日数だけ後() -> None:
    """I12。日数は仕事に残らない——期日になって消える。"""
    仕事, _ = create(JobId(text="J-0001"), 規則, 1, 期間, make_copied(), いま)
    assert 仕事.due == DueDate.from_start(いま, 3)


def test_使った量ゼロ_やり直しゼロで生まれる() -> None:
    仕事, _ = create(JobId(text="J-0001"), 規則, 1, 期間, make_copied(), いま)
    assert 仕事.spent == Spent(calls=0, seconds=0) and 仕事.retried == 0
    assert 仕事.result_at is None and 仕事.evidence_at is None


def test_開かれていない束からは作れない() -> None:
    """義務が拒む——受け入れ基準は写した時点で開かれている（Version.copy_for が開く）。"""
    束 = make_copied(criteria=AcceptanceCriteria(required_terms=("{対象期間}",)))
    with pytest.raises(ValidationError, match="開かれていない"):
        create(JobId(text="J-0001"), 規則, 1, 期間, 束, いま)
