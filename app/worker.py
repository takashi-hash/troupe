"""働き手 — 未着手のタスクを着手し、成果物を出すまで進める。

ループ自体に状態を持たない——再開に必要なものは全部帳簿にある（設計/9_働き手 §1）。
プロンプトは2つに割れる: 枠プロンプト（ここ・コード）と業務の指示（業務ルールの版・データ）。
使用上限はここが執行する——超えたら LLM を呼ばずに内容エラーへ落とす。
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import datetime

from domain.artifact import Artifact
from domain.board import Board
from domain.definition import Version, parse_definition_ref
from domain.event import Event
from domain.evidence import Reading, evidence_for, needs_evidence
from domain.job import (
    Briefing,
    CannotTake,
    ContentFailure,
    EnvironmentFailure,
    Job,
    Running,
    crash,
    exceeds_budget,
    spend,
    submit,
    take,
)
from domain.participant import Participant
from domain.ports import LedgerPort, LlmPort, SourcePort

FRAME_PROMPT = """あなたは一座の働き手です。次の作法で仕事をします。

- 作業情報にある源だけを読み、書いてよいのは成果物だけ
- 判断は求めない。材料が欠けたら質問として書く（人が答える）
- 受け入れ基準を自分で読み返し、満たしていることを確かめてから出す
- 成果物は、後から人が読んで確かめられる文章にする
"""


def build_prompt(
    board: Board,
    version: Version,
    briefing: Briefing,
    readings: tuple[Reading, ...] = (),
) -> str:
    """プロンプトを組み立てる — 枠プロンプトと業務の指示と源から。同じ材料からは必ず同じ文（純粋関数）"""
    constitution = board.constitutions[board.frozen - 1] if board.frozen else None
    words = constitution.vocabulary if constitution else ""
    purpose = constitution.purpose if constitution else ""
    return "\n".join(
        [
            FRAME_PROMPT,
            f"# このボードの目的\n{purpose}",
            f"# このボードの言葉\n{words}",
            f"# やること\n{version.instruction}",
            f"# 受け入れ基準\n{version.acceptance}",
            f"# 読むべき源\n{'、'.join(briefing.source_refs) or '（なし）'}",
            f"# 使用上限\n{briefing.budget.calls}回・{briefing.budget.seconds}秒",
            "# 源から読んだもの\n"
            + ("\n\n".join(f"## {r.source_ref}\n{r.quote}" for r in readings) or "（なし）"),
        ]
    )


def work(
    ledger: LedgerPort,
    llm: LlmPort,
    participant: Participant,
    now: datetime,
    sources: Mapping[str, SourcePort] | None = None,
) -> str | None:
    """働く — 未着手のタスクを1件着手し、成果物を出すまで進める1周。取れなければ None"""
    for job_id in ledger.jobs.find_by_state("Ready"):
        got = ledger.jobs.get(job_id)
        if got is None:
            continue
        job, rev = got
        version = _version_of(ledger, job)
        max_retries = version.max_retries if version else 3
        retries_left = max_retries - ledger.events.count(job_id, "Retried")
        try:
            running = take(job, participant, now, retries_left=retries_left)
        except CannotTake:
            continue  # 受けられないタスクは飛ばす（別の働き手が取る）
        if not ledger.jobs.put(
            running,
            rev,
            [
                Event(
                    kind="LeaseTaken",
                    at=now,
                    job_id=job_id,
                    payload={"holder": participant.participant_id},
                )
            ],
        ):
            continue  # 札の取り合いに負けた
        return _run(ledger, llm, running, rev + 1, now, sources or {})
    return None


def _run(
    ledger: LedgerPort,
    llm: LlmPort,
    job: Job,
    rev: int,
    now: datetime,
    sources: Mapping[str, SourcePort],
) -> str | None:
    """実行 — 源を読み、使用上限を見張りながらプロンプトを投げ、成果物と証拠を置いて提出する"""
    state = job.state
    if not isinstance(state, Running):
        return None
    briefing = state.briefing
    board = ledger.boards.get(job.core.board_id)
    name, number = parse_definition_ref(briefing.definition_ref)
    definition = ledger.definitions.get(name)
    if board is None or definition is None:
        return None  # 材料が引けない。札は見回りが回収する
    version = next(v for v in definition.versions if v.number == number)

    if exceeds_budget(job):
        return _give_up(ledger, job, rev, now, "使用上限を使い切っている")

    ledger.events.append(
        [
            Event(
                kind="ProgressLogged",
                at=now,
                job_id=job.core.job_id,
                payload={"note": "作業情報を読んだ"},
            )
        ]
    )
    try:
        readings = _read_sources(briefing.source_refs, sources, now)
    except Exception as error:  # 源が読めない——環境エラー（握りつぶさない）
        return _fall(ledger, job, state, rev, now, f"源が読めない: {error}")
    if readings:
        ledger.events.append(
            [
                Event(
                    kind="ProgressLogged",
                    at=now,
                    job_id=job.core.job_id,
                    payload={"note": f"源を{len(readings)}件読んだ"},
                )
            ]
        )
    started = time.monotonic()
    try:
        body = llm.chat(build_prompt(board, version, briefing, readings))
    except Exception as error:  # 例外を外へ逃がさない——帳簿に落とす（握りつぶさない）
        return _fall(ledger, job, state, rev, now, f"{type(error).__name__}: {error}")
    used = spend(job, calls=1, seconds=int(time.monotonic() - started))
    if exceeds_budget(used):
        return _give_up(ledger, used, rev, now, "使用上限を超えた")

    artifact = Artifact(
        artifact_ref=briefing.artifact_slot, job_id=job.core.job_id, body=body, at=now
    )
    ledger.artifacts.append(artifact)
    if needs_evidence(briefing.source_refs):
        ledger.evidences.append(
            evidence_for(job.core.job_id, artifact.artifact_ref, readings, now)
        )
    if not ledger.jobs.put(
        submit(used, artifact.artifact_ref),
        rev,
        [
            Event(
                kind="JobSubmitted",
                at=now,
                job_id=job.core.job_id,
                payload={"artifact_ref": artifact.artifact_ref},
            )
        ],
    ):
        return None  # 書き込みに負けた（札が切られていた等）——このタスクは進めていない
    return job.core.job_id


def _give_up(ledger: LedgerPort, job: Job, rev: int, now: datetime, reason: str) -> str | None:
    """使用上限を超えたタスクを内容エラーへ落とす（自動で使い続けない）"""
    if not ledger.jobs.put(
        crash(job, ContentFailure(reason=reason)),
        rev,
        [
            Event(kind="BudgetExceeded", at=now, job_id=job.core.job_id, payload={"reason": reason}),
            Event(kind="FailureOccurred", at=now, job_id=job.core.job_id),
        ],
    ):
        return None
    return job.core.job_id


def _fall(
    ledger: LedgerPort, job: Job, state: Running, rev: int, now: datetime, reason: str
) -> str | None:
    """落ちる — 例外を環境エラーに落として帳簿に残す。作業情報は持って帰る（戻れるように）"""
    failure = EnvironmentFailure(
        retries_left=state.retries_left,
        return_to="Ready",
        briefing=state.briefing,
        reason=reason,
    )
    if not ledger.jobs.put(
        crash(job, failure),
        rev,
        [
            Event(
                kind="FailureOccurred",
                at=now,
                job_id=job.core.job_id,
                payload={"種": "環境エラー", "理由": reason, "残り再試行": state.retries_left},
            )
        ],
    ):
        return None
    return job.core.job_id


def _version_of(ledger: LedgerPort, job: Job) -> Version | None:
    """版を読む — タスクが生まれた版（作成元が版を持つ）"""
    from app.manager import version_of

    return version_of(ledger, job)


def _read_sources(
    source_refs: tuple[str, ...], sources: Mapping[str, SourcePort], now: datetime
) -> tuple[Reading, ...]:
    """源を読む — 作業情報が指す源を順に読む。読めなければ例外（環境エラーになる）"""
    readings: list[Reading] = []
    for ref in source_refs:
        port = sources.get(ref)
        if port is None:
            raise LookupError(f"{ref} の読み口が繋がっていない")
        readings.append(Reading(source_ref=ref, quote=port.read(), at=now))
    return tuple(readings)
