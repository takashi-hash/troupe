"""警告の判定 — 何が人の目と判断を要するかを決める、たった1箇所。

画面は並べるだけで、何が赤かを決めない（設計/10_画面/画面.md §2「Alert の出口は1本」）。
判定がここに1つあるかぎり、枚が増えても出しわけは食い違わない。

**狼少年を作らない**が全ての行の背骨: 人が今できることが無いものは出さない。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

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


def alerts_for(jobs: tuple[Job, ...], now: datetime, viewer: str) -> tuple[Alert, ...]:
    """警告を判定する — 今日その人の目と判断が要るものだけを選ぶ。

    出す・出さないの根拠（全部「人が今できることがあるか」で決まる）:

    | 状態 | 出すか | なぜ |
    |---|---|---|
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
        alert = _alert_of(job, now, viewer)
        if alert is not None:
            found.setdefault(alert.key, alert)  # 同じ鍵は1件だけ（冪等）
    return tuple(sorted(found.values(), key=lambda a: (_ORDER.index(a.kind), a.deadline)))


def _alert_of(job: Job, now: datetime, viewer: str) -> Alert | None:
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


def _title_of(job: Job) -> str:
    """そのタスクを指す名（業務ルールの名。指示から作ったものは id）"""
    if isinstance(job.core.origin, FromDefinition):
        return job.core.origin.definition_name
    return job.core.job_id
