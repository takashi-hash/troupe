"""帳簿からの読み（SQLite）の壊しかた——履歴・検索・今日の一覧の読みの範囲。

設計/仕事が回る筋道.md §4。SQL は最も壊れやすい層なのに週Aの通しでしか
踏まれていなかった——ここで単体でも踏む。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from adapters.ledger.db import open_ledger
from adapters.ledger.jobs import SqliteJobs
from adapters.ledger.reading import SqliteHistory, SqliteSearch, SqliteToday
from domain.aggregates.job.life import Finished, InProgress, Ready
from domain.events.job.job_finished import JobFinished
from domain.events.job.job_handed_out import JobHandedOut
from domain.events.job.job_started import JobStarted
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.origin import Origin
from domain.value_objects.job.approval import Approval
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.rule_name import RuleName
from tests.aggregates.job.conftest import make_job, 座長

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
あと = datetime(2026, 8, 17, 9, 5, tzinfo=UTC)
一号 = Agent(name="一号")


@pytest.fixture
def conn(tmp_path):  # type: ignore[no-untyped-def]
    conn = open_ledger(tmp_path / "ichiza.db")
    yield conn
    conn.close()


def _second_job(state, **over):  # type: ignore[no-untyped-def]
    rule = RuleName(text="月次の請求の確かめ")
    period = Period(text="2026-08")
    return make_job(
        state,
        id=JobId(text="J-0002"),
        origin=Origin.from_rule(rule, 1, period),
        born_of=rule,
        period=period,
        criteria=AcceptanceCriteria(required_terms=("2026-08",)),
        **over,
    )


def test_履歴は新しい順で_起こす者は生のまま運ぶ(conn) -> None:  # type: ignore[no-untyped-def]
    jobs = SqliteJobs(conn)
    仕事 = make_job(Ready())
    jobs.save(仕事, (JobHandedOut(at=いま, by=Clock()),))
    jobs.save(
        make_job(InProgress(assignee=一号)), (JobStarted(at=あと, by=一号, took=一号),)
    )
    entries = SqliteHistory(conn).read_latest(10)
    assert [e.name for e in entries] == ["JobStarted", "JobHandedOut"]  # 新しい順
    assert entries[0].by_kind == "agent" and entries[0].by_name == "一号"
    assert entries[1].by_kind == "clock" and entries[1].by_name is None  # 語に写すのは app
    assert entries[0].rule == "週次の依存の棚卸し" and entries[0].period == "2026-W34"
    assert entries[0].instruction  # 見出しの材料——どの仕事か判らない列は読めない


def test_履歴の上限が効く(conn) -> None:  # type: ignore[no-untyped-def]
    jobs = SqliteJobs(conn)
    jobs.save(make_job(Ready()), (JobHandedOut(at=いま, by=Clock()),))
    jobs.save(make_job(InProgress(assignee=一号)), (JobStarted(at=あと, by=一号, took=一号),))
    assert len(SqliteHistory(conn).read_latest(1)) == 1


def test_検索は終わったものも引く_条件は重ねられる(conn) -> None:  # type: ignore[no-untyped-def]
    jobs = SqliteJobs(conn)
    jobs.save(make_job(Ready()), (JobHandedOut(at=いま, by=Clock()),))
    jobs.save(
        _second_job(Finished(approval=Approval(by=座長, at=あと)), result_at="r://1", evidence_at="e://1"),
        (JobFinished(at=あと, by=Clock(), evidence_at="e://1", recheck_at=None),),
    )
    search = SqliteSearch(conn)
    全部 = search.read(None, None, None, None)
    assert {h.id for h in 全部} == {"J-0001", "J-0002"}  # 空の条件は絞らない
    終わった = search.read(None, "Finished", None, None)
    assert [h.id for h in 終わった] == ["J-0002"]  # 終わったものも含めて（F1）
    assert 終わった[0].state_name == "Finished" and 終わった[0].instruction
    キーワード = search.read("請求", None, None, None)
    assert [h.id for h in キーワード] == ["J-0002"]
    重ね = search.read("請求", "Ready", None, None)
    assert 重ね == ()  # 条件は AND


def test_今日の一覧は終点を運ばないが_1件では引ける(conn) -> None:  # type: ignore[no-untyped-def]
    jobs = SqliteJobs(conn)
    jobs.save(make_job(Ready()), (JobHandedOut(at=いま, by=Clock()),))
    jobs.save(
        _second_job(Finished(approval=Approval(by=座長, at=あと)), result_at="r://1", evidence_at="e://1"),
        (JobFinished(at=あと, by=Clock(), evidence_at="e://1", recheck_at=None),),
    )
    today = SqliteToday(conn)
    assert [m.id.text for m in today.read_all()] == ["J-0001"]  # 一覧の読みだけは終点を運ばない
    終点 = today.read(JobId(text="J-0002"))
    assert 終点 is not None and 終点.state_name == "Finished"  # 詳細は終わった仕事も見る
