"""警告の判定 — 何が人の目と判断を要するかを決める、たった1箇所。

画面は並べるだけで、何が赤かを決めない（設計/10_画面/画面.md §2「Alert の出口は1本」）。
判定がここに1つあるかぎり、枚が増えても出しわけは食い違わない。

**狼少年を作らない**が全ての行の背骨: 人が今できることが無いものは出さない。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict

from domain.definition import Version
from domain.job import (
    AwaitingAnswer,
    Checkpoint,
    ClosedBySelfReport,
    ClosedWithEvidence,
    ContentFailure,
    FromDefinition,
    Job,
)

AlertKind = Literal["Red", "Checkpoint", "AwaitingAnswer", "SelfReport", "Deadline"]
"""警告の種 — 部品はすべて既にある語（要対応・承認待ち・回答待ち・自己申告・期限）"""

# 上から順に強い。1つのタスクに出る警告は1つだけ——重ねると赤が埋もれる
_ORDER: tuple[AlertKind, ...] = ("Red", "Checkpoint", "AwaitingAnswer", "SelfReport", "Deadline")


class Alert(BaseModel):
    """警告 — 人に見せる注意。判定は1箇所、画面は並べるだけ"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    kind: AlertKind
    job_id: str
    title: str
    detail: str = ""
    deadline: datetime
    state_kind: str
    actionable: bool = False  # この人が押せるか（担当・宛先の本人だけ）


def alert_key(kind: AlertKind, job_id: str) -> str:
    """警告の鍵 — 同じ警告を二度並べないための鍵。二度並べた警告は読まれなくなる"""
    return f"{kind}/{job_id}"


def alerts_for(
    jobs: tuple[Job, ...],
    now: datetime,
    viewer: str,
    versions: Mapping[str, Version | None],
    approvals: Mapping[str, int],
) -> tuple[Alert, ...]:
    """警告を判定する — 今日その人の目と判断が要るものだけを選ぶ。

    版と承認の数を**必ず受け取る**——状態だけでは見えない「すり抜け」があるから
    （下の表の最初の2行）。渡さずに判定できてしまうと、その2行は静かに消える。

    出す・出さないの根拠（全部「人が今できることがあるか」で決まる）:

    | 状態 | 出すか | なぜ |
    |---|---|---|
    | 承認を飛ばして先へ進んだ | 要対応（赤） | **型では塞げない**——このタスクに承認が要るかは状態でなく版が知っている |
    | 裁く版が引けない | 要対応（赤） | 受け入れ基準が空のまま合格にできてしまう。何を基準に通したか言えない |
    | 内容エラー | 要対応（赤） | 再試行が尽きた・成果の質。人の判断が要る |
    | 環境エラー | **出さない** | 再試行の最中。人が今できることが無い |
    | 承認待ち | 承認待ち | 判断は人間——担当の本人だけが押せる |
    | 回答待ち | 回答待ち | 材料の欠けを埋める問い。宛先の本人だけが押せる |
    | 自己申告で完了 | 確かめの期限が来てから | 期限前に出しても、まだ確かめようがない |
    | 証拠で完了 | 出さない | 済んでいる |
    | それ以外 | 期限が今日・過ぎていれば期限 | 先の予定は「今日」に載せない |
    """
    found: dict[str, Alert] = {}
    for job in jobs:
        job_id = job.core.job_id
        alert = _alert_of(job, now, viewer, versions.get(job_id), approvals.get(job_id, 0))
        if alert is not None:
            found.setdefault(alert.key, alert)  # 同じ鍵は1件だけ（冪等）
    return tuple(sorted(found.values(), key=lambda a: (_ORDER.index(a.kind), a.deadline)))


def _alert_of(
    job: Job, now: datetime, viewer: str, version: Version | None, approvals: int
) -> Alert | None:
    """1つのタスクに出る警告（強い順に1つだけ）。出すものが無ければ None"""
    state = job.state
    title, deadline, job_id = _title_of(job), job.core.deadline, job.core.job_id

    def _made(kind: AlertKind, detail: str = "", actionable: bool = False) -> Alert:
        return Alert(
            key=alert_key(kind, job_id),
            kind=kind,
            job_id=job_id,
            title=title,
            detail=detail,
            deadline=deadline,
            state_kind=state.kind,
            actionable=actionable,
        )

    slipped = _slipped_through(job, version, approvals)
    if slipped is not None:
        return _made("Red", slipped)  # 完了していても出す——事故は済んだことにしない
    if isinstance(state, ContentFailure):
        return _made("Red", state.reason)
    if isinstance(state, Checkpoint):
        return _made("Checkpoint", state.position, state.assignee_id == viewer)
    if isinstance(state, AwaitingAnswer):
        return _made("AwaitingAnswer", state.question, state.addressee_id == viewer)
    if isinstance(state, ClosedBySelfReport):
        if state.recheck_deadline <= now:
            return _made("SelfReport", state.recheck_deadline.date().isoformat())
        return None  # 期限前——まだ確かめようがない
    if isinstance(state, ClosedWithEvidence):
        return None  # 済んでいる
    if state.kind == "EnvironmentFailure":
        return None  # 再試行の最中。人が今できることが無い
    if deadline.date() <= now.date():
        return _made("Deadline")
    return None


# 承認待ちを通り過ぎた先の状態——ここに居るなら、承認は済んでいるはず
_PAST_CHECKPOINT = (
    "Confirmed",
    "ApplyAttempt",
    "Applied",
    "ClosedWithEvidence",
    "ClosedBySelfReport",
)


def _slipped_through(job: Job, version: Version | None, approvals: int) -> str | None:
    """すり抜けを見つける — 型が塞げない穴を、結果として見張る。

    型が禁じるのは「承認待ち→承認済み」の無承認だけ。**承認待ちを丸ごと飛ばす道**
    （検証中→承認済み）は禁じられない——承認が要る業務ルールかどうかは、
    状態ではなく版が知っているから。即時の守りが在ることは、結果の見張りを要らなくしない。
    """
    state_kind = job.state.kind
    if state_kind != "Verifying" and state_kind not in _PAST_CHECKPOINT:
        return None
    if isinstance(job.core.origin, FromDefinition) and version is None:
        return "このタスクを裁く業務ルールの版が帳簿から引けない"
    if state_kind == "Verifying":
        return None  # まだ通っていない
    if version is not None and version.checkpoint_position and approvals == 0:
        return "承認が要る業務ルールなのに、承認の記録が無いまま先へ進んでいる"
    return None


def _title_of(job: Job) -> str:
    """そのタスクを指す名（業務ルールの名。指示から作ったものは id）"""
    if isinstance(job.core.origin, FromDefinition):
        return job.core.origin.definition_name
    return job.core.job_id
