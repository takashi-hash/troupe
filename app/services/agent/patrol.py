"""見回る — AI が始めるもの。2つ目の見に来る先。

設計: 設計/仕事が回る筋道.md §1「AI が始めるもの」。
**人の手が要る仕事**（**上限に触れた・やり直しが尽きた**・確かめ期日が来た・**根拠なしで終わった**）
——**見立てを書く**。2つ目が無いと、**落ちた仕事に見立てが付かない**。
| 見立てを書く | `assess` | 読んだ結果と理由を積む。**担当でなくても書ける**（I13 の例外）。**状態を変えない** | **事実の報告と案。決めるのは人** |
| 人へ回す | `hand_over` | もう自力で進めないと**仕様が言ったとき**、見立てを書いて人の判断を待つ | **進めないという事実の報告** |

書くべきかは仕様 `should_assess` が、進めないかは仕様 `is_stuck` が言う——ここは運ぶだけ。
見立ての本文も事実の数を並べるだけで、比べない——比べたのは仕様。
姿の合わない行は触らずに飛ばす——一生に傷をつけない。
"""

from __future__ import annotations

from typing import Any

from app.ports.clock_port import ClockPort
from app.ports.llm_port import LlmPort
from app.ports.job_state_reader import JobStateReader
from app.ports.work_reader import WorkMaterial, WorkReader
from domain.aggregates.job import assess as 見立て
from domain.aggregates.job import hand_over as 回す
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import Failed, FinishedPendingRecheck, InProgress
from domain.repositories.job_repository import JobRepository
from domain.services.should_assess import should_assess
from domain.services.stuck import is_stuck
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.job_id import JobId
from domain.value_objects.people.agent import Agent


def _fact_reason(job: Job[Any], material: WorkMaterial) -> str:
    """理由 — 仕様が見たのと同じ材料を、数のまま並べる。"""
    return (
        f"使った量 {job.spent.calls}回・{job.spent.seconds}秒"
        f"（上限 {job.budget.calls}回・{job.budget.seconds}秒）／"
        f"やり直し {job.retried}回（上限 {job.max_retries}回）／"
        f"止まった理由 {len(material.fall_reasons)}件"
    )


def patrol(
    jobs: JobRepository,
    states: JobStateReader,
    work: WorkReader,
    llm: LlmPort,
    clock: ClockPort,
    by: Agent,
) -> tuple[JobId, ...]:
    """見立てを書いた・人へ回した仕事の識別子。触らなかった仕事は返らない。"""
    acted: list[JobId] = []

    # 人の手が要る仕事 — 失敗した（上限に触れた・やり直しが尽きた）と、根拠なしで終わったもの。
    for id in states.ids_in("Failed") + states.ids_in("FinishedPendingRecheck"):
        job = jobs.load(id)
        if job is None or not isinstance(job.state, (Failed, FinishedPendingRecheck)):
            continue
        material = work.read(id)
        if not should_assess(
            material.assessments,
            material.fall_reasons,
            job.spent,
            job.budget,
            job.retried,
            job.max_retries,
        ):
            continue
        状況 = (
            f"失敗したまま人の判断を待っている（落ちた中身: {job.state.fallen}）。"
            if isinstance(job.state, Failed)
            else "根拠の在りかが空のまま終わっている（確かめ待ち）。"
        ) + _fact_reason(job, material)
        assessment = _read(llm, 状況, material, fallback_reason=_fact_reason(job, material))
        same_job, written = 見立て.assess(job, assessment, by=by, now=clock.now())
        jobs.save(same_job, (written,))
        acted.append(id)

    # 実行中で行き詰まったもの — 見立てを書いて失敗したへ。
    for id in states.ids_in("InProgress"):
        job = jobs.load(id)
        if job is None or not isinstance(job.state, InProgress):
            continue
        material = work.read(id)
        if not is_stuck(material.previous_result, material.fall_reasons, job.retried):
            continue
        last = material.fall_reasons[-1] if material.fall_reasons else "（記録なし）"
        状況 = f"実行中だが自力では進めない（直近の止まった理由: {last}）。" + _fact_reason(job, material)
        assessment = _read(llm, 状況, material, fallback_reason=_fact_reason(job, material))
        failed_job, written, fell = 回す.hand_over(job, assessment, by=by, now=clock.now())
        jobs.save(failed_job, (written, fell))
        acted.append(id)

    return tuple(acted)


def _read(
    llm: LlmPort, situation: str, material: object, fallback_reason: str
) -> Assessment:
    """LLM に状況を読ませて見立てにする。届かなければ機械の文に倒す。

    **見立てが無いと AI は数字しか出せない**——LLM の一読みが、この仕組みの値打ち。
    届かないとき（LLM が落ちている等）は数字の文で埋める——I15（必ず見立てが在る）を
    環境の故障より優先する。次の巡回では F6 が二度書きを止める。
    """
    fall_reasons = getattr(material, "fall_reasons", ())
    previous = getattr(material, "previous_result", None)
    siblings = getattr(material, "sibling_states", ())
    try:
        finding, reason, _, _ = llm.read_situation(situation, fall_reasons, previous, siblings)
        return Assessment(finding=finding, reason=reason)
    except OSError:
        return Assessment(
            finding=situation, reason=fallback_reason + "（LLM に届かず、機械の文で埋めた）"
        )
