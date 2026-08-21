"""マネージャー — 帳簿を回す機体。手を動かさない。判断もしない。

輪は6つ: create（作成）・dispatch（配る）・patrol（見回る）・verify（検証する）と、
まだ実装していない triage（気づく）・surface（並べる）。
どの輪も突合と日付演算だけ——LLM は無い。全部が冪等で、何度回しても同じ。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from domain.definition import Version, current_period, definition_ref
from domain.event import Event
from domain.job import (
    Briefing,
    EnvironmentFailure,
    Core,
    Created,
    FromDefinition,
    Job,
    Ready,
    Verifying,
    block,
    expire,
    escalate,
    origin_key,
    pass_verification,
    retry,
)
from domain.ports import LedgerPort
from domain.verification import Blocked, check


def create(ledger: LedgerPort, now: datetime) -> list[str]:
    """作成 — 有効な業務ルール × いまの対象期間の突合でタスクを作る。

    冪等の鍵は作成元——同じ作成元のタスクはもう在るか、を先に確かめる（二度作成されない）。
    人が思い出して作るのではない。
    """
    created: list[str] = []
    for definition in ledger.definitions.enacted():
        version = next(v for v in definition.versions if v.number == definition.enacted)
        period = current_period(version.cadence, now)
        origin = FromDefinition(
            definition_name=definition.name, version=version.number, period=period
        )
        key = origin_key(origin)
        if key is None or ledger.jobs.find_by_origin(key) is not None:
            continue  # 既に作成済み——冪等
        job = Job(
            core=Core(
                job_id=f"タスク-{uuid.uuid4().hex[:12]}",  # ID に意味を持たせない
                origin=origin,
                board_id=definition.board_id,
                ready_at=now,
                deadline=now + timedelta(days=version.deadline_days),
                budget=version.budget,
            ),
            state=Created(),
        )
        if ledger.jobs.put(
            job,
            expected_rev=0,
            events=[
                Event(kind="JobCreated", at=now, job_id=job.core.job_id, payload={"origin": key})
            ],
        ):
            created.append(job.core.job_id)
    return created


def dispatch(ledger: LedgerPort, now: datetime) -> list[str]:
    """配る — 作成済みのタスクに作業情報を詰めて未着手に。

    関門: 方針が人に凍結されるまで、このボードのタスクは配らない。
    作業情報はすべて参照で指す（重い中身は持たない）。
    """
    dispatched: list[str] = []
    for job_id in ledger.jobs.find_by_state("Created"):
        got = ledger.jobs.get(job_id)
        if got is None:
            continue
        job, rev = got
        board = ledger.boards.get(job.core.board_id)
        if board is None or board.frozen is None:
            continue  # 関門は閉じている
        origin = job.core.origin
        if not isinstance(origin, FromDefinition):
            continue  # 指示発の作業情報は受付の仕事（後の段）
        definition = ledger.definitions.get(origin.definition_name)
        if definition is None:
            continue
        version = next(v for v in definition.versions if v.number == origin.version)
        ref = definition_ref(definition.name, version.number)
        briefing = Briefing(
            definition_ref=ref,
            source_refs=version.source_refs,
            material_refs=(),
            artifact_slot=f"成果物/{definition.name}/{origin.period}",
            acceptance_ref=f"{ref}#受け入れ基準",
            budget=version.budget,
            constitution_ref=f"{board.board_id}/方針/{board.frozen}",
        )
        ready = Job(core=job.core, state=Ready(briefing=briefing))
        if ledger.jobs.put(
            ready, expected_rev=rev, events=[Event(kind="JobDispatched", at=now, job_id=job_id)]
        ):
            dispatched.append(job_id)
    return dispatched


def patrol(ledger: LedgerPort, now: datetime) -> list[str]:
    """見回る — 期限の切れた札を切り、タスクを未着手へ戻す（I4「消えない」の執行者）。

    落ちた働き手のタスクが実行中で固まらないための輪。切れていない札は切らない（冪等）。
    """
    returned: list[str] = []
    for job_id in ledger.jobs.find_by_state("Running"):
        got = ledger.jobs.get(job_id)
        if got is None:
            continue
        job, rev = got
        back = expire(job, now)
        if back is None:
            continue  # まだ切れていない
        if ledger.jobs.put(back, rev, [Event(kind="LeaseExpired", at=now, job_id=job_id)]):
            returned.append(job_id)
    return returned


def verify(ledger: LedgerPort, now: datetime, assignee_id: str) -> list[str]:
    """検証する — 検証中のタスクにチェックをかけ、承認待ちか承認済みへ送る輪。

    止めたら未着手へ戻す（理由は出来事に残る）。判断はしない——機械の判定だけ。
    """
    moved: list[str] = []
    for job_id in ledger.jobs.find_by_state("Verifying"):
        got = ledger.jobs.get(job_id)
        if got is None:
            continue
        job, rev = got
        state = job.state
        if not isinstance(state, Verifying):
            continue
        artifact = ledger.artifacts.get(state.artifact_ref)
        version = version_of(ledger, job)
        result = check(artifact.body if artifact else "", version.must_contain if version else ())
        if isinstance(result, Blocked):
            if ledger.jobs.put(
                block(job),
                rev,
                [
                    Event(
                        kind="CheckBlocked",
                        at=now,
                        job_id=job_id,
                        payload={"reason": result.reason},
                    )
                ],
            ):
                moved.append(job_id)
            continue
        position = version.checkpoint_position if version else None
        if ledger.jobs.put(
            pass_verification(job, position, assignee_id),
            rev,
            [
                Event(kind="CheckPassed", at=now, job_id=job_id),
                Event(
                    kind="CheckpointReached" if position else "JobConfirmed",
                    at=now,
                    job_id=job_id,
                ),
            ],
        ):
            moved.append(job_id)
    return moved


def version_of(ledger: LedgerPort, job: Job) -> Version | None:
    """版を読む — タスクは生まれた版で裁かれる（作成元が版を持つ）"""
    origin = job.core.origin
    if not isinstance(origin, FromDefinition):
        return None
    definition = ledger.definitions.get(origin.definition_name)
    if definition is None:
        return None
    return next((v for v in definition.versions if v.number == origin.version), None)


def triage(ledger: LedgerPort, now: datetime) -> list[str]:
    """気づく — エラーを環境と中身に仕分け、再試行するか人へ上げる輪。

    残りがあれば未着手へ戻す（何度目かは帳簿の Retried の数が持つ）。
    尽きたら内容エラーにして人へ——永久に繰り返さない。
    """
    handled: list[str] = []
    for job_id in ledger.jobs.find_by_state("EnvironmentFailure"):
        got = ledger.jobs.get(job_id)
        if got is None:
            continue
        job, rev = got
        state = job.state
        if not isinstance(state, EnvironmentFailure):
            continue
        if state.retries_left > 0:
            done = ledger.jobs.put(
                retry(job),
                rev,
                [
                    Event(
                        kind="Retried",
                        at=now,
                        job_id=job_id,
                        payload={"残り再試行": state.retries_left - 1, "理由": state.reason},
                    )
                ],
            )
        else:
            done = ledger.jobs.put(
                escalate(job, f"再試行が尽きた（{state.reason}）"),
                rev,
                [
                    Event(
                        kind="FailureOccurred",
                        at=now,
                        job_id=job_id,
                        payload={"種": "内容エラー", "理由": "再試行が尽きた"},
                    )
                ],
            )
        if done:
            handled.append(job_id)
    return handled
