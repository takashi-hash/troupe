"""マネージャー — 帳簿を回す機体。手を動かさない。判断もしない。

輪は7つ: create（作成）・dispatch（配る）・patrol（見回る）・verify（検証する）・
triage（気づく）・confirm（確かめる）・surface（並べる）。
どの輪も突合と日付演算だけ——LLM は無い。全部が冪等で、何度回しても同じ。

**この一覧は tests/rings_lint.py が調停図と突き合わせる**——数を直して中身を直さない、
という食い違いが実際に起きた（2026-08-21。設計は7と言い、図と表は6を描き、
実装は別の6を持っていた）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from domain.alert import Alert, alerts_for
from domain.board import constitution_ref, gate_open
from domain.definition import Definition, Version, current_period
from domain.event import Event
from domain.evidence import needs_evidence
from domain.job import (
    CannotClose,
    EnvironmentFailure,
    Core,
    Created,
    FromDefinition,
    Job,
    Ready,
    Verifying,
    block,
    briefing_for,
    close,
    expire,
    escalate,
    origin_key,
    pass_verification,
    retry,
)
from domain.ports import LedgerPort, SheetSource
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
        if board is None or not gate_open(board):
            continue  # 関門は閉じている（判定はドメインの仕様）
        origin = job.core.origin
        if not isinstance(origin, FromDefinition):
            continue  # 指示発の作業情報は受付の仕事（後の段）
        definition = ledger.definitions.get(origin.definition_name)
        if definition is None:
            continue
        version = next(v for v in definition.versions if v.number == origin.version)
        ready = Job(
            core=job.core,
            state=Ready(
                briefing=briefing_for(
                    definition.name, version, origin.period, constitution_ref(board)
                )
            ),
        )
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
        if version is None and isinstance(job.core.origin, FromDefinition):
            continue  # 裁く版が引けない——空の基準で合格にしない。surface が赤で並べる
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


def confirm(ledger: LedgerPort, now: datetime) -> list[str]:
    """確かめる — 証拠を照合して完了へ送る輪。

    **タスクを閉じるのは働き手でも人でもなく、証拠を照合したマネージャー**。
    証拠で閉じる（人の報告に頼らない）が形になる場所。
    適用が要る業務ルールのタスクは、ここでは閉じない——閉じる門が拒む。
    """
    closed: list[str] = []
    for kind in ("Confirmed", "Applied"):
        for job_id in ledger.jobs.find_by_state(kind):
            got = ledger.jobs.get(job_id)
            if got is None:
                continue
            job, rev = got
            version = version_of(ledger, job)
            needs_apply = version.needs_apply if version else False
            source_refs = version.source_refs if version else ()
            evidence_ref = None
            if needs_evidence(source_refs):
                found = ledger.evidences.get(f"証拠/{_artifact_ref_of(job)}")
                if found is None:
                    continue  # 証拠がまだ無い。人の報告は待たない——次の周でまた見る
                evidence_ref = found.evidence_ref
            try:
                done = close(
                    job,
                    evidence_ref,
                    needs_apply,
                    recheck_deadline=now + timedelta(days=7),
                )
            except CannotClose:
                continue  # 適用が要るのに飛ばそうとした——閉じない
            if ledger.jobs.put(
                done,
                rev,
                [
                    Event(
                        kind="JobClosed",
                        at=now,
                        job_id=job_id,
                        payload={"evidence": evidence_ref or "自己申告"},
                    )
                ],
            ):
                closed.append(job_id)
    return closed


def surface(source: SheetSource, now: datetime, viewer: str) -> tuple[Alert, ...]:
    """並べる — 食い違いを1箇所の判定で人に見せる輪（I1「抜けない」の見え方の出口）。

    **帳簿に書かない唯一の輪。**出口は画面（今日の枚）で、判定は domain の1箇所から来る。
    書かないので、抜けていても状態は進み、誰も転ばなかった——実際 2026-08-21 まで抜けていた
    （画面が自分で判定して動いてしまっていた）。だから執行者を置いた: tests/rings_lint.py。

    冪等——同じ材料なら同じ並び。同じ警告は二度出ない（警告の鍵で1件）。

    版と承認の数まで集めるのは、**状態だけでは見えないすり抜けがある**から。
    いまはタスクごとに出来事を引く。件数が増えて遅いと**実測**できたら、
    数え上げを帳簿の側へ移す（消す前に測る・足す前に測る）。
    """
    jobs = source.all_jobs()
    definitions = source.all_definitions()  # 生まれた版で裁く——有効かどうかは関係がない
    versions = {job.core.job_id: _version_by_origin(job, definitions) for job in jobs}
    approvals = {
        job.core.job_id: sum(
            1 for event in source.events_for(job.core.job_id) if event.kind == "CheckpointApproved"
        )
        for job in jobs
    }
    return alerts_for(jobs, now, viewer, versions, approvals)


def _version_by_origin(job: Job, definitions: tuple[Definition, ...]) -> Version | None:
    """そのタスクを裁く版（引けなければ None——それ自体が surface の赤になる）"""
    origin = job.core.origin
    if not isinstance(origin, FromDefinition):
        return None
    found = next((d for d in definitions if d.name == origin.definition_name), None)
    if found is None:
        return None
    return next((v for v in found.versions if v.number == origin.version), None)


def _artifact_ref_of(job: Job) -> str:
    """そのタスクの成果物の参照（承認済み・反映済みが持っている）"""
    return str(getattr(job.state, "artifact_ref", ""))
