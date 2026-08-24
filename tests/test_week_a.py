"""週A — うまくいく週を、本物の帳簿で最後まで通す。

設計/どう作るか §7 の収束条件「うまくいく週が最後まで通る」の実物。
設計のロールプレイで11回なぞった筋書きを、SQLite の帳簿・本物の
アプリケーションサービス・本物の domain で1手ずつ踏む。
LLM だけは台本（差し替え式の口があることの証明でもある）。

  月09:00 作られる → 配られる → AI が取る
  月09:02 AI が詰まる「本番と手元、どちらの依存か」→ 人に尋ねる
  月09:31 座長が答える「手元です」
  月09:35 AI が成果を出す
  月09:36 機械が検査する → 通る
  火09:02 座長が承認する
  火09:05 根拠を読んで終わる
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from adapters.ledger.db import Ledger, open_cloud_ledger, open_ledger
from adapters.ledger.jobs import SqliteJobs, read_events
from adapters.ledger.reading import (
    SqliteActiveRules,
    SqliteJobStates,
    SqliteOrigins,
    SqliteToday,
    SqliteWork,
)
from adapters.ledger.rules import SqliteRules
from adapters.ledger.stores import (
    SqliteAssessments,
    SqliteEvidence,
    SqliteQuestions,
    SqliteResults,
)
from app.dto.version_form import VersionForm
from app.ports.source_port import Quote, SourceOutcome
from app.services.agent.consult import consult
from app.services.agent.start import start
from app.services.clock.confirm import confirm
from app.services.clock.create import create
from app.services.clock.hand_out import hand_out
from app.services.clock.run_check import run_check
from app.services.human.activate import activate
from app.services.human.add_version import add_version
from app.services.human.answer import answer
from app.services.human.approve import approve
from app.services.screen.gather_today import gather_today
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.reply import Mark, Reply
from domain.value_objects.people.agent import Agent
from domain.value_objects.rule.copied import Copied
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source


def 時(day: int, hour: int, minute: int) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=UTC)


class 進む時計:
    def __init__(self, start: datetime) -> None:
        self.at = start

    def set(self, at: datetime) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at


class 予定なし:
    """予定の訪問が無い ScheduledVisitReader——この週の筋書きに展開の版は出ない。"""

    def read_scheduled(self) -> tuple[tuple[str, str], ...]:
        return ()


class 連番:
    def __init__(self) -> None:
        self.n = 0

    def new_id(self) -> str:
        self.n += 1
        return f"ID-{self.n:04d}"


class 台本LLM:
    """決めた応答を順に返す。使った量も台本どおり。"""

    def __init__(self, replies: list[Reply]) -> None:
        self.replies = replies

    def consult(
        self,
        instruction: str,
        criteria_terms: tuple[str, ...],
        criteria_note: str,
        source_material: str,
        answered_questions: tuple[tuple[str, str], ...],
        previous_result: str | None,
    ) -> tuple[Reply, int, int]:
        return self.replies.pop(0), 1, 12

    def read_situation(
        self,
        situation: str,
        fall_reasons: tuple[str, ...],
        previous_result: str | None,
        sibling_states: tuple[str, ...],
    ) -> tuple[str, str, int, int]:
        raise AssertionError("この筋書きで巡回の見立ては書かれない")



class 引用の源:
    """源はいつでも読めて、引用を返す週。"""

    def __init__(self, text: str) -> None:
        self.text = text

    def read(self, source: Source) -> SourceOutcome:
        return Quote(evidence=Evidence(quote=self.text, source=source))


class 題材なし:
    def read(self, rule: RuleName) -> Copied | None:
        return None


def _まっさらなクラウドの帳簿(dsn: str) -> Ledger:
    """クラウドの帳簿を、毎回まっさらから開き直す。

    前の週の帳簿が残っていると筋書きが変わる。表の名を並べて消すと
    形が2箇所に書かれることになるので、入れ物ごと作り直す。
    """
    帳簿 = open_cloud_ledger(dsn)
    帳簿.execute("DROP SCHEMA public CASCADE")
    帳簿.execute("CREATE SCHEMA public")
    帳簿.commit()
    帳簿.close()
    return open_cloud_ledger(dsn)


@pytest.fixture(params=["手元", "クラウド"])
def 帳簿(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[Ledger]:
    """同じ週を、手元（SQLite）とクラウド（Cloud SQL）の両方で通す。

    **口が1つであることの、いちばん強い証拠**——同じ筋書きが、器を替えても同じ順で残る。
    在りかが渡っていなければクラウドの分は飛ばす（器は買うもので、常に居るとは限らない）。
    """
    if request.param == "手元":
        帳簿 = open_ledger(tmp_path / "ichiza.db")
    else:
        dsn = os.environ.get("ICHIZA_PG_DSN")
        if not dsn:
            pytest.skip("ICHIZA_PG_DSN が無いので、クラウドの帳簿は通さない")
        帳簿 = _まっさらなクラウドの帳簿(dsn)
    yield 帳簿
    帳簿.close()


def test_週Aが本物の帳簿で最後まで通る(帳簿: Ledger) -> None:
    conn = 帳簿
    jobs, rules = SqliteJobs(conn), SqliteRules(conn)
    results, evidences = SqliteResults(conn), SqliteEvidence(conn)
    questions, assessments = SqliteQuestions(conn), SqliteAssessments(conn)
    states, origins = SqliteJobStates(conn), SqliteOrigins(conn)
    active, work, today = SqliteActiveRules(conn), SqliteWork(conn), SqliteToday(conn)
    時計 = 進む時計(時(16, 18, 0))
    一号 = Agent(name="一号")
    源 = 引用の源(
        "2026-W34 時点の依存: requests 2.32（2026-08-16 更新）・pydantic 2.13（2026-08-15 更新）"
    )
    llm = 台本LLM(
        [
            Reply(mark=Mark.QUESTION, body="本番と手元、どちらの依存を棚卸ししますか"),
            Reply(
                mark=Mark.RESULT,
                body="2026-W34 の依存の棚卸し。更新が来ているのは requests 2.32 と pydantic 2.13。",
            ),
        ]
    )

    # 前夜 — 座長が版を積み、有効にする（判断は人間）
    欄 = VersionForm(
        instruction="依存の一覧を取り、更新が来ているものを挙げる",
        source="file:custom/週次の依存の棚卸し/deps.txt",
        required_terms=("{対象期間}",),
        description="一覧の日付が今週のものである",
        cycle="weekly",
        days=3,
        budget_calls=20,
        budget_seconds=600,
        owner="座長",
        max_retries=20,
    )
    assert add_version(rules, 題材なし(), 時計, "週次の依存の棚卸し", by="座長", form=欄) is None
    assert activate(rules, 時計, "週次の依存の棚卸し", 1, by="座長") is None

    # 月09:00 作られる → 配られる（時計）— 対象期間は 2026-W34 に開かれる
    時計.set(時(17, 9, 0))
    made = create(jobs, rules, active, origins, 予定なし(), 連番(), 時計)
    assert len(made) == 1
    id = made[0]
    assert hand_out(jobs, states, 時計) == (id,)
    仕事 = jobs.load(id)
    assert 仕事 is not None and 仕事.criteria.required_terms == ("2026-W34",)

    # 月09:00 AI が取る（引き金は AI 自身）
    assert start(jobs, states, 時計, by=一号) == id

    # 月09:02 詰まる → 人に尋ねる（判断は求めない。材料の不足だけ）
    時計.set(時(17, 9, 2))
    assert consult(jobs, work, 源, llm, questions, results, evidences, assessments, 時計, id, by=一号) is None
    行 = gather_today(today, 時計, viewer="座長")
    assert [r for r in 行 if r.id == id.text and "answer" in r.actions], "答えるが今日に出る"

    # 月09:31 座長が答える → 着手できるへ戻る
    時計.set(時(17, 9, 31))
    assert answer(jobs, questions, 時計, id.text, by="座長", body="手元の依存です") is None

    # 月09:33 AI が取り直す
    時計.set(時(17, 9, 33))
    assert start(jobs, states, 時計, by=一号) == id

    # 月09:35 成果を出す（根拠は源から——AI の言葉は根拠にならない）
    時計.set(時(17, 9, 35))
    assert consult(jobs, work, 源, llm, questions, results, evidences, assessments, 時計, id, by=一号) is None

    # 月09:36 機械が検査する → 通る（担当が受け持ちの人へ移る）
    時計.set(時(17, 9, 36))
    assert run_check(jobs, states, results, 時計) == (id,)

    # 火09:02 座長が今日を開き、成果と根拠を見て、承認する
    時計.set(時(18, 9, 2))
    行 = gather_today(today, 時計, viewer="座長")
    承認待ちの行 = [r for r in 行 if r.id == id.text]
    assert 承認待ちの行 and "approve" in 承認待ちの行[0].actions
    assert 承認待ちの行[0].result_body and "2026-W34" in 承認待ちの行[0].result_body
    assert 承認待ちの行[0].evidence_quote, "根拠の引用が今日の行に在る（F3）"
    assert approve(jobs, 時計, id.text, by="座長") is None

    # 火09:05 根拠を読んで終わる（時計）
    時計.set(時(18, 9, 5))
    assert confirm(jobs, states, 源, evidences, 時計) == (id,)
    終わった = jobs.load(id)
    assert 終わった is not None and type(終わった.state).__name__ == "Finished"
    assert 終わった.evidence_at is not None

    # 帳簿に残った出来事の列が、週Aの筋書きそのもの（F4 何が起きたか説明できる）
    assert [name for name, _ in read_events(conn, id)] == [
        "JobCreated",
        "JobHandedOut",
        "JobStarted",
        "SpentIncreased",
        "QuestionAsked",
        "QuestionAnswered",
        "JobStarted",
        "SpentIncreased",
        "ResultSubmitted",
        "CheckPassed",
        "Approved",
        "JobFinished",
    ]

    # 終わったあとの今日は空——済んだものを出さない（F6）
    assert gather_today(today, 時計, viewer="座長") == ()
