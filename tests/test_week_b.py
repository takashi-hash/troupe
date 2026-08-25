"""週B — 落ちる週を、本物の帳簿で最後まで通す。

設計/どう作るか §7「動かして、実際に落ちてから直す」の実物。
本番で実際に落とした筋書き（源が読めない——「壊れた棚卸し」）を固定する。
LLM だけは台本——この週、仕事を進める LLM は一度も呼ばれない
（読めなければ `fail` へ）。呼ばれるのは巡回の見立ての一読みだけ。

  月09:00 作られる → 配られる → AI が取る
  月09:05 源が読めない → 落ちる（自動でやり直す最中は今日に出ない）
  月09:10 仕分け → やり直しに出る
  月09:12 AI が取り直す → また読めない → 落ちる（やり直しが尽きた）
  月09:15 仕分け → 残す
  月09:20 巡回が見立てを書く（二度目の巡回は書かない——F6）
  月09:30 座長が今日で見立てを読み、打ち切る（判断は人間）
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from adapters.ledger.db import open_ledger
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
    SqliteEvidence,
    SqliteResults,
)
from app.dto.version_form import VersionForm
from app.ports.source_port import SourceOutcome, Unreadable
from app.services.agent.consult import consult
from app.services.agent.patrol import patrol
from app.services.agent.start import start
from app.services.clock.create import create
from app.services.clock.hand_out import hand_out
from app.services.clock.sort_failures import sort_failures
from app.services.human.abandon import abandon
from app.services.human.activate import activate
from app.services.human.add_version import add_version
from app.services.screen.gather_today import gather_today
from domain.value_objects.job.reply import Reply
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


class 見立てだけのLLM:
    """仕事を進める口は呼ばれない週。見立ての一読みだけが台本どおり返る。"""

    def consult(
        self,
        instruction: str,
        criteria_terms: tuple[str, ...],
        criteria_note: str,
        source_material: str,
        answered_questions: tuple[tuple[str, str], ...],
        previous_result: str | None,
    ) -> tuple[Reply, int, int]:
        raise AssertionError("源が読めない週に、進める LLM は呼ばれない（読めなければ fail へ）")

    def read_situation(
        self,
        situation: str,
        fall_reasons: tuple[str, ...],
        previous_result: str | None,
        sibling_states: tuple[str, ...],
    ) -> tuple[str, str, int, int]:
        return (
            "源の在りかが変わった可能性が高い。版の源を直してから頼み直すのが良い",
            f"{len(fall_reasons)}回とも同じ理由（読めない）で落ちた",
            1,
            8,
        )


class 読めない源:
    """源はこの週ずっと読めない。"""

    def read(self, source: Source) -> SourceOutcome:
        return Unreadable(reason=f"源が見つかりません: {source.location}")


class 題材なし:
    def read(self, rule: RuleName) -> Copied | None:
        return None


def test_週Bが本物の帳簿で最後まで通る(tmp_path: Path) -> None:
    conn = open_ledger(tmp_path / "ichiza.db")
    jobs, rules = SqliteJobs(conn), SqliteRules(conn)
    results, evidences = SqliteResults(conn), SqliteEvidence(conn)
    states, origins = SqliteJobStates(conn), SqliteOrigins(conn)
    active, work, today = SqliteActiveRules(conn), SqliteWork(conn), SqliteToday(conn)
    時計 = 進む時計(時(16, 18, 0))
    一号 = Agent(name="一号")
    源 = 読めない源()
    llm = 見立てだけのLLM()

    # 前夜 — 座長が版を積み、有効にする（やり直しの上限は1）
    欄 = VersionForm(
        instruction="依存の一覧を取り、更新が来ているものを挙げる",
        source="file:custom/壊れた棚卸し/deps.txt",
        required_terms=("{対象期間}",),
        description="一覧の日付が今週のものである",
        cycle="weekly",
        days=3,
        budget_calls=20,
        budget_seconds=600,
        owner="座長",
        max_retries=1,
    )
    assert add_version(rules, 題材なし(), 時計, "壊れた棚卸し", by="座長", form=欄) is None
    assert activate(rules, 時計, "壊れた棚卸し", 1, by="座長") is None

    # 月09:00 作られる → 配られる → AI が取る
    時計.set(時(17, 9, 0))
    made = create(jobs, rules, active, origins, 予定なし(), 連番(), 時計)
    assert len(made) == 1
    id = made[0]
    assert hand_out(jobs, states, 時計) == (id,)
    assert start(jobs, states, 時計, by=一号) == id

    # 月09:05 源が読めない → 落ちる（進める LLM は呼ばれない）
    時計.set(時(17, 9, 5))
    assert consult(jobs, work, 源, llm, results, evidences, 時計, id, by=一号) is None
    落ちた = jobs.load(id)
    assert 落ちた is not None and type(落ちた.state).__name__ == "Failed"

    # 自動でやり直している最中の失敗は、今日に出ない（F6——赤が埋もれない）
    assert gather_today(today, 時計, viewer="座長") == ()

    # 月09:10 仕分け → やり直しに出る（上限1に届いていない）
    時計.set(時(17, 9, 10))
    assert sort_failures(jobs, states, 時計) == (id,)

    # 月09:12 AI が取り直す → また読めない → 落ちる（やり直しが尽きた）
    時計.set(時(17, 9, 12))
    assert start(jobs, states, 時計, by=一号) == id
    assert consult(jobs, work, 源, llm, results, evidences, 時計, id, by=一号) is None

    # 月09:15 仕分け → 残す（何度見ても残る）
    時計.set(時(17, 9, 15))
    assert sort_failures(jobs, states, 時計) == ()
    assert sort_failures(jobs, states, 時計) == ()

    # 月09:20 巡回が見立てを書く。二度目の巡回は書かない（F6——同じ見立てを二度書かない）
    時計.set(時(17, 9, 20))
    assert patrol(jobs, states, work, llm, 時計, by=一号) == (id,)
    assert patrol(jobs, states, work, llm, 時計, by=一号) == ()

    # 月09:30 座長が今日を開く——見立てと「尽きた」が読め、差し戻す・打ち切るが押せる
    時計.set(時(17, 9, 30))
    行 = gather_today(today, 時計, viewer="座長")
    assert [r.id for r in 行] == [id.text]
    row = 行[0]
    assert set(row.actions) == {"send_back", "abandon"}
    assert row.retries_exhausted
    assert row.assessments and "源の在りか" in row.assessments[0][0]
    assert "落ちた" in row.assessments[0][1]

    # 判断は人間——座長が理由をつけて打ち切る
    assert abandon(jobs, 時計, id.text, by="座長", reason="源の在りかを直してから頼み直す") is None
    終点 = jobs.load(id)
    assert 終点 is not None and type(終点.state).__name__ == "Abandoned"

    # 帳簿に残った出来事の列が、週Bの筋書きそのもの（F4 何が起きたか説明できる）
    assert [name for name, _ in read_events(conn, id)] == [
        "JobCreated",
        "JobHandedOut",
        "JobStarted",
        "JobFailed",
        "Retried",
        "JobStarted",
        "JobFailed",
        "AssessmentWritten",
        "JobAbandoned",
    ]

    # 打ち切ったあとの今日は空——済んだものを出さない（F6）
    assert gather_today(today, 時計, viewer="座長") == ()
    conn.close()
