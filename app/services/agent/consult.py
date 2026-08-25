"""LLM に問う — 実行中の仕事で1歩進める。

設計: 設計/仕事が回る筋道.md §1「AI が始めるもの」。
| **LLM に問う** | `consult` | 源を読み（**読めなければ `fail` へ**）、LLM に渡し、
**`Reply` と使った回数・秒**を受け取る。使った量を積み、**仕様に振り分けさせて**、
質問・成果・見立てのどれかを返す | **振り分けるのは仕様**。この操作は運ぶだけ |

出す道では **源をもう一度読んで引用が取れれば**根拠も積む。取れなければ根拠なしで出す。
使った量は `spend` が積む——**上限で止まったら（I14）`exhaust` へ**。
各 domain の操作ごとに `save(job, events)` の対で書く。
業務の判断はしない——姿が合わなければ断りに変えるだけ。
**名乗りは担当と検める**（I13）——姿を変えられるのは自分が担当の仕事だけ。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.llm_port import LlmPort
from app.ports.source_port import Quote, SourcePort, Unreadable
from app.ports.work_reader import WorkReader
from app.services.refusal import Refusal
from domain.aggregates.job import ask as 尋ねる
from domain.aggregates.job import assess as 見立て
from domain.aggregates.job import exhaust as 使い切る
from domain.aggregates.job import fail as 落ちる
from domain.aggregates.job import spend as 積む
from domain.aggregates.job import submit as 出す
from domain.aggregates.job.life import InProgress
from domain.repositories.evidence_store import EvidenceStore
from domain.repositories.job_repository import JobRepository
from domain.repositories.result_store import ResultStore
from domain.services.verify_reply import verify
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.question import Question
from domain.value_objects.job.reply import Mark
from domain.value_objects.job.result import Result
from domain.value_objects.people.agent import Agent


def consult(
    jobs: JobRepository,
    work: WorkReader,
    source: SourcePort,
    llm: LlmPort,
    results: ResultStore,
    evidences: EvidenceStore,
    clock: ClockPort,
    id: JobId,
    by: Agent,
) -> Refusal | None:
    """1歩進めたら None。姿が合わなければ断り。"""
    job = jobs.load(id)
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, InProgress):
        return Refusal(reason="いまは実行中ではありません（もう誰かが動かしました）")
    assignee = job.state.assignee
    if not isinstance(assignee, Agent):
        return Refusal(reason="実行中の担当が AI ではありません（LLM に問うのは AI の操作です）")
    if assignee != by:
        return Refusal(
            reason=f"担当ではありません（担当: {assignee.name}、名乗り: {by.name}）"
            "——姿を変えられるのは自分が担当の仕事だけです"
        )

    # 源を読む — 読めなければ fail へ（落ちた中身＝読めなかった理由）。
    outcome = source.read(job.source)
    if isinstance(outcome, Unreadable):
        fallen_job, fell = 落ちる.fail(job, fallen=outcome.reason, now=clock.now())
        jobs.save(fallen_job, (fell,))
        return None
    source_material = outcome.evidence.quote

    # 集約の外の材料と合わせて LLM へ。
    material = work.read(id)
    reply, calls, seconds = llm.consult(
        instruction=job.instruction.text,
        criteria_terms=job.criteria.required_terms,
        criteria_note=job.criteria.description,
        source_material=source_material,
        answered_questions=material.answered_questions,
        previous_result=material.previous_result,
    )

    # 使った量を積む — 上限で止まったら（I14）exhaust へ。
    try:
        job, spent = 積む.spend(job, calls, seconds, now=clock.now())
    except ValueError:
        exhausted_job, fell = 使い切る.exhaust(job, now=clock.now())
        jobs.save(exhausted_job, (fell,))
        return None
    jobs.save(job, (spent,))

    # 検めた印で振り分ける——振り分けの判断は仕様がした。ここは運ぶだけ。
    mark = verify(reply, job.criteria)
    if mark is Mark.QUESTION:
        question = Question(body=reply.body, to=job.owner)
        next_job, asked = 尋ねる.ask(job, question, now=clock.now())
        jobs.save(next_job, (asked,))
        return None
    if mark is Mark.RESULT:
        result_at = results.put(Result(body=reply.body))
        again = source.read(job.source)
        evidence_at = evidences.put(again.evidence) if isinstance(again, Quote) else None
        next_job, submitted = 出す.submit(job, result_at, evidence_at, now=clock.now())
        jobs.save(next_job, (submitted,))
        return None
    assessment = Assessment(
        finding=reply.body,
        reason=(
            "成果と名乗ったが、必ず含む語がすべては含まれていなかった"
            if reply.mark is Mark.RESULT
            else "印が成果でも質問でもなかった"
        ),
    )
    same_job, written = 見立て.assess(job, assessment, by=assignee, now=clock.now())
    jobs.save(same_job, (written,))
    return None
