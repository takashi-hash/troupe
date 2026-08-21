"""タスク — 一生を生きる作業の単位。設計/6_型/状態モデル.md の写し。

その状態でしか持てないものを、その状態だけが持つ。
pydantic の frozen＋extra="forbid" で、禁止状態は実行時にも作れない。
識別子の対訳は 設計/1_言葉/用語集.md §11 が1箇所で決める。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from typing import TYPE_CHECKING

from domain.participant import Participant

if TYPE_CHECKING:
    from domain.definition import Version
from domain.verification import Blocked, CheckResult, Passed, Returned, ReviewResult, check

__all__ = ["Blocked", "CheckResult", "Passed", "Returned", "ReviewResult", "check"]  # 検証の2層は domain/verification.py が正本

_frozen = ConfigDict(frozen=True, extra="forbid")


# ---- 作成元（どこから作成済みか。突合の冪等の鍵） ----


class FromDefinition(BaseModel):
    """業務ルールから — 業務ルールの版×対象期間で作成済み（暦も源の一つ）"""

    model_config = _frozen
    kind: Literal["FromDefinition"] = "FromDefinition"
    definition_name: str
    version: int
    period: str


class FromInstruction(BaseModel):
    """指示から — 人のメッセージを受付がタスクに写した"""

    model_config = _frozen
    kind: Literal["FromInstruction"] = "FromInstruction"
    utterance_id: str


class FromParent(BaseModel):
    """サブタスクから — 実行中の親タスクが生んだ"""

    model_config = _frozen
    kind: Literal["FromParent"] = "FromParent"
    parent_job_id: str


Origin = Annotated[
    Union[FromDefinition, FromInstruction, FromParent], Field(discriminator="kind")
]
"""作成元 — 同じ作成元のタスクは二度作成されない"""


# ---- 持ち物 ----


class Lease(BaseModel):
    """札 — タスクへの着手権。持ち主と期限の対。落ちたら切れて戻る"""

    model_config = _frozen
    holder: str
    expires_at: datetime


class Budget(BaseModel):
    """使用上限 — 1つのタスクに使ってよい量と時間。超えたらエラー"""

    model_config = _frozen
    calls: int
    seconds: int


class Briefing(BaseModel):
    """作業情報 — タスク1件が携える文脈。すべて参照で指す（設計/3_部品/部品一覧.md §5）"""

    model_config = _frozen
    definition_ref: str
    source_refs: tuple[str, ...]
    material_refs: tuple[str, ...]
    artifact_slot: str
    acceptance_ref: str
    budget: Budget
    constitution_ref: str
    sensitive: bool = False  # 機微の印。着手で能力申告と突合される


class AttemptRecord(BaseModel):
    """試みの記録 — 外に出す前に先に記す「これからやる」の印（反映の二相の前半）"""

    model_config = _frozen
    actor: str
    at: datetime


class ApprovalRecord(BaseModel):
    """承認の記録 — 承認待ちを承認した人と時刻"""

    model_config = _frozen
    approved_by: str
    at: datetime


class ReversibleApply(BaseModel):
    """可逆の反映 — やり直せる反映の記録"""

    model_config = _frozen
    kind: Literal["ReversibleApply"] = "ReversibleApply"
    actor: str
    at: datetime
    attempt: AttemptRecord


class IrreversibleApply(BaseModel):
    """不可逆の反映 — 承認の記録が型の材料。承認待ちなしの不可逆は値として作れない"""

    model_config = _frozen
    kind: Literal["IrreversibleApply"] = "IrreversibleApply"
    actor: str
    at: datetime
    attempt: AttemptRecord
    approval: ApprovalRecord


ApplyRecord = Annotated[
    Union[ReversibleApply, IrreversibleApply], Field(discriminator="kind")
]
"""反映の記録"""


# ---- 今（どれか1つ。その状態でしか持てないものを、その状態だけが持つ） ----


class Created(BaseModel):
    """作成済み — まだ配られていない"""

    model_config = _frozen
    kind: Literal["Created"] = "Created"


class Ready(BaseModel):
    """未着手 — 解決済みの作業情報を必ず持つ。作業情報の無い未着手は書けない"""

    model_config = _frozen
    kind: Literal["Ready"] = "Ready"
    briefing: Briefing


class Running(BaseModel):
    """実行中 — 札は実行中だけが持つ"""

    model_config = _frozen
    kind: Literal["Running"] = "Running"
    briefing: Briefing
    lease: Lease
    retries_left: int
    calls_used: int = 0  # 使った回数
    seconds_used: int = 0  # 使った秒


class AwaitingAnswer(BaseModel):
    """回答待ち — 尋ねて止まっている。判断は求めない（それは承認待ち）"""

    model_config = _frozen
    kind: Literal["AwaitingAnswer"] = "AwaitingAnswer"
    briefing: Briefing
    question: str
    addressee_id: str


class Verifying(BaseModel):
    """検証中 — チェックとレビューを受けている"""

    model_config = _frozen
    kind: Literal["Verifying"] = "Verifying"
    briefing: Briefing
    artifact_ref: str


class Checkpoint(BaseModel):
    """承認待ち — 人の判断待ち。担当した人しか承認できない"""

    model_config = _frozen
    kind: Literal["Checkpoint"] = "Checkpoint"
    artifact_ref: str
    position: str
    assignee_id: str


class Confirmed(BaseModel):
    """承認済み — 判断済み・まだ外に出ていない。承認待ちの無いタスクでは approval は None"""

    model_config = _frozen
    kind: Literal["Confirmed"] = "Confirmed"
    artifact_ref: str
    approval: ApprovalRecord | None = None


class ApplyAttempt(BaseModel):
    """反映中 — 試みを記してから外に出している途中。見つかったら勝手にやり直さず人へ"""

    model_config = _frozen
    kind: Literal["ApplyAttempt"] = "ApplyAttempt"
    artifact_ref: str
    attempt: AttemptRecord
    approval: ApprovalRecord | None = None


class Applied(BaseModel):
    """反映済み — 外に出た。記録が試みを必ず持つ"""

    model_config = _frozen
    kind: Literal["Applied"] = "Applied"
    artifact_ref: str
    record: ApplyRecord


class ClosedWithEvidence(BaseModel):
    """証拠で閉じた — 完了。人の報告に頼らない"""

    model_config = _frozen
    kind: Literal["ClosedWithEvidence"] = "ClosedWithEvidence"
    evidence_ref: str


class ClosedBySelfReport(BaseModel):
    """自己申告で閉じた — 証拠の読み口が無いタスクの閉じ方。確かめの期限つき"""

    model_config = _frozen
    kind: Literal["ClosedBySelfReport"] = "ClosedBySelfReport"
    recheck_deadline: datetime


class EnvironmentFailure(BaseModel):
    """環境エラー — 外側の事情。残りがあれば自動で再試行。作業情報を持って帰る（戻れるように）"""

    model_config = _frozen
    kind: Literal["EnvironmentFailure"] = "EnvironmentFailure"
    retries_left: int
    return_to: str
    briefing: Briefing
    reason: str


class ContentFailure(BaseModel):
    """内容エラー — 成果の質。人へ。使用上限超えもここ"""

    model_config = _frozen
    kind: Literal["ContentFailure"] = "ContentFailure"
    reason: str


Closed = Annotated[
    Union[ClosedWithEvidence, ClosedBySelfReport], Field(discriminator="kind")
]
"""完了"""

Failure = Annotated[
    Union[EnvironmentFailure, ContentFailure], Field(discriminator="kind")
]
"""エラー"""

State = Annotated[
    Union[
        Created,
        Ready,
        Running,
        AwaitingAnswer,
        Verifying,
        Checkpoint,
        Confirmed,
        ApplyAttempt,
        Applied,
        ClosedWithEvidence,
        ClosedBySelfReport,
        EnvironmentFailure,
        ContentFailure,
    ],
    Field(discriminator="kind"),
]
"""状態 — タスクがいま居るところ。どれか1つ"""


# ---- 芯とタスク ----


class Core(BaseModel):
    """芯 — タスクの全状態に共承認するる不変の部分。緊急フラグという欄は存在しない"""

    model_config = _frozen
    job_id: str
    origin: Origin
    board_id: str
    ready_at: datetime
    deadline: datetime
    budget: Budget
    parent_job_id: str | None = None


class Job(BaseModel):
    """タスク — 芯と今を合わせ持つ。一生を生きる作業の単位"""

    model_config = _frozen
    core: Core
    state: State


class IllegalTransition(Exception):
    """遷移できない — 遷移表に無い移り。合法な State 遷移だけ、の執行"""


class MissingEvent(Exception):
    """出来事の欠け — 遷移に必須の Event が添えられていない。画面が嘘をつかない保証"""


_TRANSITIONS: dict[tuple[str | None, str], frozenset[str]] = {
    (None, "Created"): frozenset({"JobCreated"}),
    ("Created", "Ready"): frozenset({"JobDispatched"}),
    ("Ready", "Running"): frozenset({"LeaseTaken"}),
    ("Running", "Ready"): frozenset({"LeaseReleased", "LeaseExpired"}),
    ("Running", "Verifying"): frozenset({"JobSubmitted"}),
    ("Running", "AwaitingAnswer"): frozenset({"InquiryAsked"}),
    ("AwaitingAnswer", "Running"): frozenset({"InquiryAnswered"}),
    ("Verifying", "Ready"): frozenset({"CheckBlocked", "ReviewReturned"}),
    ("Verifying", "Checkpoint"): frozenset({"CheckpointReached"}),
    ("Verifying", "Confirmed"): frozenset({"JobConfirmed"}),
    ("Checkpoint", "Confirmed"): frozenset({"CheckpointApproved"}),
    ("Confirmed", "ApplyAttempt"): frozenset({"ApplyAttempted"}),
    ("ApplyAttempt", "Applied"): frozenset({"JobApplied"}),
    ("ApplyAttempt", "Confirmed"): frozenset({"JobConfirmed"}),
    ("Confirmed", "ClosedWithEvidence"): frozenset({"JobClosed"}),
    ("Confirmed", "ClosedBySelfReport"): frozenset({"JobClosed"}),
    ("Applied", "ClosedWithEvidence"): frozenset({"JobClosed"}),
    ("Applied", "ClosedBySelfReport"): frozenset({"JobClosed"}),
}


def required_events(old_kind: str | None, new_kind: str) -> frozenset[str] | None:
    """遷移の必須出来事 — 設計/6_型/状態モデル.md §2 の遷移表の写し。

    None は「遷移できない」。空集合は「Event の義務なし」（同じ State への書き直し）。
    Failure への落ちと Failure からの retry はどこからでも起きる。
    """
    if new_kind in ("EnvironmentFailure", "ContentFailure"):
        return frozenset({"FailureOccurred"})
    if old_kind == "EnvironmentFailure":
        return frozenset({"Retried"})
    if old_kind == new_kind:
        return frozenset()
    return _TRANSITIONS.get((old_kind, new_kind))


def origin_key(origin: Origin) -> str | None:
    """作成元の鍵 — Reconciliation の冪等の鍵（帳簿の一意索引に入る）。

    FromDefinition は version を含めない（同じ期間のタスクは版が上がっても1つ）。
    FromParent は None（親の実行が冪等を持つ——一意制約に掛けない）。
    """
    if isinstance(origin, FromDefinition):
        return f"def:{origin.definition_name}:{origin.period}"
    if isinstance(origin, FromInstruction):
        return f"utt:{origin.utterance_id}"
    return None


# ---- 操作（遷移表の写し。呼べる者の制約は操作が守る） ----


class CannotApprove(Exception):
    """承認できない — I2「止まる」。承認待ちは担当した人しか承認できない"""


def approve(job: Job, by: str, at: datetime) -> Job:
    """承認する — 承認待ち → 承認済み。担当の人ID の本人だけが呼べる"""
    if not isinstance(job.state, Checkpoint):
        raise CannotApprove("承認待ちにいないタスクは承認できない")
    if job.state.assignee_id != by:
        raise CannotApprove("担当した人しか承認できない")
    return Job(
        core=job.core,
        state=Confirmed(
            artifact_ref=job.state.artifact_ref,
            approval=ApprovalRecord(approved_by=by, at=at),
        ),
    )


class CannotTake(Exception):
    """着手できない — 照合・手の届く範囲・機微のどれかが通らない"""


def take(
    job: Job,
    participant: Participant,
    at: datetime,
    lease_seconds: int = 600,
    retries_left: int = 3,
) -> Job:
    """着手 — 未着手から実行中へ。照合済みの者だけ。機微の源を指す作業情報なら機微可の者だけ"""
    if not isinstance(job.state, Ready):
        raise IllegalTransition("未着手でないタスクは着手できない")
    if not participant.verified:
        raise CannotTake("照合を通っていない参加者は着手できない")
    briefing = job.state.briefing
    if briefing.sensitive and not participant.capability.sensitivity_ok:
        raise CannotTake("機微の源を指す作業情報は、機微可の申告がある者だけ")
    out_of_reach = set(briefing.source_refs) - set(participant.capability.reachable_ports)
    if out_of_reach:
        raise CannotTake(f"手が届かない源がある: {sorted(out_of_reach)}")
    return Job(
        core=job.core,
        state=Running(
            briefing=briefing,
            lease=Lease(
                holder=participant.participant_id,
                expires_at=at + timedelta(seconds=lease_seconds),
            ),
            retries_left=retries_left,
        ),
    )


def release(job: Job) -> Job:
    """返す — 実行中から未着手へ。札を手放す。理由は出来事に残る"""
    if not isinstance(job.state, Running):
        raise IllegalTransition("実行中でないタスクの札は返せない")
    return Job(core=job.core, state=Ready(briefing=job.state.briefing))


def expire(job: Job, at: datetime) -> Job | None:
    """札を切る — 期限の切れた札を見回りが切り、タスクを未着手へ戻す。切れていなければ None"""
    if not isinstance(job.state, Running) or job.state.lease.expires_at > at:
        return None
    return Job(core=job.core, state=Ready(briefing=job.state.briefing))


def submit(job: Job, artifact_ref: str) -> Job:
    """提出 — 成果物を添えて検証中へ。札の持ち主だけが呼ぶ"""
    if not isinstance(job.state, Running):
        raise IllegalTransition("実行中でないタスクは提出できない")
    return Job(
        core=job.core,
        state=Verifying(briefing=job.state.briefing, artifact_ref=artifact_ref),
    )


def pass_verification(job: Job, checkpoint_position: str | None, assignee_id: str) -> Job:
    """検証を通過 — 位置が業務ルールにあるときは承認待ちへ、無ければ承認済みへ"""
    if not isinstance(job.state, Verifying):
        raise IllegalTransition("検証中でないタスクは検証を通過できない")
    if checkpoint_position is None:
        return Job(
            core=job.core, state=Confirmed(artifact_ref=job.state.artifact_ref, approval=None)
        )
    return Job(
        core=job.core,
        state=Checkpoint(
            artifact_ref=job.state.artifact_ref,
            position=checkpoint_position,
            assignee_id=assignee_id,
        ),
    )


def block(job: Job) -> Job:
    """止める — チェックが止めたタスクを未着手へ戻す（理由は出来事に残る）"""
    if not isinstance(job.state, Verifying):
        raise IllegalTransition("検証中でないタスクは止められない")
    return Job(core=job.core, state=Ready(briefing=job.state.briefing))


def exceeds_budget(job: Job) -> bool:
    """使用上限を超えている — 実行中のタスクが、業務ルールの決めた量か時間を使い切ったか"""
    state = job.state
    if not isinstance(state, Running):
        return False
    budget = state.briefing.budget
    return state.calls_used >= budget.calls or state.seconds_used >= budget.seconds


def spend(job: Job, calls: int, seconds: int) -> Job:
    """使う — 実行中のタスクの使用量を足す。使用上限の見張りはこの数を見る"""
    state = job.state
    if not isinstance(state, Running):
        raise IllegalTransition("実行中でないタスクは使用量を足せない")
    return Job(
        core=job.core,
        state=state.model_copy(
            update={
                "calls_used": state.calls_used + calls,
                "seconds_used": state.seconds_used + seconds,
            }
        ),
    )


def crash(job: Job, failure: EnvironmentFailure | ContentFailure) -> Job:
    """落ちる — どこからでもエラーへ。環境エラーは再試行、内容エラーは人へ"""
    return Job(core=job.core, state=failure)


def retry(job: Job) -> Job:
    """再試行 — 環境エラーのタスクを未着手へ戻す。作業情報はエラーが持って帰っている"""
    state = job.state
    if not isinstance(state, EnvironmentFailure):
        raise IllegalTransition("環境エラーでないタスクは再試行できない")
    if state.retries_left <= 0:
        raise IllegalTransition("残り再試行が尽きたタスクは再試行できない")
    return Job(core=job.core, state=Ready(briefing=state.briefing))


def escalate(job: Job, reason: str) -> Job:
    """人へ上げる — 再試行が尽きたタスクを内容エラーにして人に見せる"""
    return Job(core=job.core, state=ContentFailure(reason=reason))


def briefing_for(
    definition_name: str,
    version: "Version",
    period: str,
    board_constitution_ref: str,
    sensitive: bool = False,
) -> Briefing:
    """作業情報を詰める — 業務ルールとボードから、参照だけの作業情報を組み立てる。

    参照の形式はドメインが持つ（外で文字列を組み立てない）。重い中身は持たず、
    すべて参照で指す——「作業情報の無いタスクは配れない」を機械判定にするため。
    """
    from domain.definition import acceptance_ref, artifact_slot, definition_ref

    return Briefing(
        definition_ref=definition_ref(definition_name, version.number),
        source_refs=version.source_refs,
        material_refs=(),
        artifact_slot=artifact_slot(definition_name, period),
        acceptance_ref=acceptance_ref(definition_name, version.number),
        budget=version.budget,
        constitution_ref=board_constitution_ref,
        sensitive=sensitive,
    )


class CannotClose(Exception):
    """閉じられない — 適用が要るのに飛ばした、証拠が無いなど、完了にできないとき"""


def close(
    job: Job,
    evidence_ref: str | None,
    needs_apply: bool,
    recheck_deadline: datetime | None = None,
) -> Job:
    """閉じる — 証拠で完了にする（人の報告に頼らない）。

    ・適用が要る業務ルールなら、承認済みから直には閉じられない（適用を飛ばせない）
    ・証拠があれば証拠で閉じる。無ければ自己申告＋確かめの期限
    """
    state = job.state
    if isinstance(state, Confirmed):
        if needs_apply:
            raise CannotClose("適用が要る業務ルールのタスクは、適用を飛ばして閉じられない")
    elif not isinstance(state, Applied):
        raise IllegalTransition("承認済みか反映済みでないタスクは閉じられない")
    if evidence_ref is not None:
        return Job(core=job.core, state=ClosedWithEvidence(evidence_ref=evidence_ref))
    if recheck_deadline is None:
        raise CannotClose("証拠が無いなら、確かめの期限が要る（自己申告）")
    return Job(core=job.core, state=ClosedBySelfReport(recheck_deadline=recheck_deadline))


# ---- 仕立て（Factory）——新しい1件が満たすべき形。集約境界図 §6 の表がそのまま ----


def new_job(
    job_id: str,
    origin: Origin,
    board_id: str,
    now: datetime,
    deadline_days: int,
    budget: Budget,
) -> Job:
    """タスクを仕立てる — 新しい1件の形を1箇所で決める。

    **採番は立てた者、形はドメイン**——id は受け取る（誰が立てたかは手順の側の話）。
    期限は**作成した時刻 ＋ 版の日数**。使用上限は版の写しで、参照ではない
    （後から版が変わっても、このタスクは生まれた版の量で裁かれる）。
    """
    return Job(
        core=Core(
            job_id=job_id,
            origin=origin,
            board_id=board_id,
            ready_at=now,
            deadline=now + timedelta(days=deadline_days),
            budget=budget,
        ),
        state=Created(),
    )


# ---- Job の引き（主語が Job のもの。使い道ではなく主語で置く） ----


def assignee_of(job: Job) -> str:
    """担当を読む — そのタスクを承認する人、または札を持っている者。居なければ空"""
    state = job.state
    if isinstance(state, Checkpoint):
        return state.assignee_id
    if isinstance(state, AwaitingAnswer):
        return state.addressee_id
    if isinstance(state, Running):
        return state.lease.holder
    return ""


def definition_of(job: Job) -> str:
    """業務ルールを読む — 作成元が業務ルールなら、その名。指示発なら空"""
    origin = job.core.origin
    return origin.definition_name if isinstance(origin, FromDefinition) else ""


def period_of(job: Job) -> str:
    """対象期間を読む — 作成元が持つ。指示発なら空"""
    origin = job.core.origin
    return origin.period if isinstance(origin, FromDefinition) else ""
