"""状態と遷移。

設計: 設計/仕事とは何か.md §6（正本）。
**行けない遷移は書かない。型が作らせない。**

各状態は別の型で、§6「足して持つもの」だけを持つ。
持ってはいけないものは**欄が無い**——だから書けない。
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from domain.values import Approval, Assignee, Human, Owner, RecheckDate, Value

# ── 状態（設計 §6）──────────────────────────────────────


class Created(Value):
    """作られた — 担当を持ってはいけない。"""

    name: Literal["Created"] = "Created"


class Ready(Value):
    """着手できる — 担当も承認も持ってはいけない。

    承認の欄が無いので「承認を持ったまま着手できるへ戻る」が書けない。
    """

    name: Literal["Ready"] = "Ready"


class InProgress(Value):
    """実行中 — 担当を必ず持つ。承認は持てない。"""

    name: Literal["InProgress"] = "InProgress"
    assignee: Assignee


class AwaitingAnswer(Value):
    """答え待ち — 担当と質問の在りかを必ず持つ。承認は持てない。"""

    name: Literal["AwaitingAnswer"] = "AwaitingAnswer"
    assignee: Assignee
    question_at: str


class Submitted(Value):
    """提出済み — 担当を必ず持つ。承認も検査の結果も持てない。

    成果の在りかが空でないことは `Job` が守る（在りかは共通の持ちもの）。
    """

    name: Literal["Submitted"] = "Submitted"
    assignee: Assignee


class AwaitingApproval(Value):
    """承認待ち — 担当が `Owner`（I6）。承認は持てない。

    担当の型が `Owner` なので、受け持ちの人以外が承認待ちを持てない。
    """

    name: Literal["AwaitingApproval"] = "AwaitingApproval"
    assignee: Owner


class Cleared(Value):
    """承認済み — 承認を必ず持つ（I4）。"""

    name: Literal["Cleared"] = "Cleared"
    approval: Approval


class Failed(Value):
    """失敗した — 落ちた中身を必ず持つ。担当は持てない。"""

    name: Literal["Failed"] = "Failed"
    fallen: str


class FinishedPendingRecheck(Value):
    """終わった（確かめ待ち）— 承認と確かめ期日を必ず持つ。根拠の在りかは持てない。"""

    name: Literal["FinishedPendingRecheck"] = "FinishedPendingRecheck"
    approval: Approval
    recheck: RecheckDate


class Finished(Value):
    """終わった — 承認を必ず持つ。**終点。**

    根拠の在りかが空でないことは `Job` が守る。
    """

    name: Literal["Finished"] = "Finished"
    approval: Approval


class Abandoned(Value):
    """打ち切られた — 打ち切った人と理由を必ず持つ。**終点。**"""

    name: Literal["Abandoned"] = "Abandoned"
    by: Human
    reason: str


State = Annotated[
    Created
    | Ready
    | InProgress
    | AwaitingAnswer
    | Submitted
    | AwaitingApproval
    | Cleared
    | Failed
    | FinishedPendingRecheck
    | Finished
    | Abandoned,
    Field(discriminator="name"),
]

#: 終点。ここから先の遷移は無い。
TERMINAL: frozenset[str] = frozenset({"Finished", "Abandoned"})

#: 日本語⇄識別子の橋（設計 §6 の状態の欄）。突合が使う。
STATE_NAMES: dict[str, str] = {
    "作られた": "Created",
    "着手できる": "Ready",
    "実行中": "InProgress",
    "答え待ち": "AwaitingAnswer",
    "提出済み": "Submitted",
    "承認待ち": "AwaitingApproval",
    "承認済み": "Cleared",
    "失敗した": "Failed",
    "終わった（確かめ待ち）": "FinishedPendingRecheck",
    "終わった": "Finished",
    "打ち切られた": "Abandoned",
}


# ── 遷移（設計 §6 の遷移表）──────────────────────────────


class Transition(Value):
    """遷移表の1行。**設計の表と1対1**——突合が確かめる。"""

    frm: str | None
    to: str
    operation: str
    events: tuple[str, ...]
    actor: Literal["人", "AI", "時計"]


_ROWS: list[tuple[str | None, str, str, tuple[str, ...], Literal["人", "AI", "時計"]]] = [
    (None, "Created", "request", ("JobRequested", "JobCreated"), "人"),
    (None, "Created", "create", ("JobCreated",), "時計"),
    ("Created", "Ready", "hand_out", ("JobHandedOut",), "時計"),
    ("Ready", "InProgress", "start", ("JobStarted",), "AI"),
    ("InProgress", "Ready", "release", ("JobReleased",), "AI"),
    ("InProgress", "Ready", "return_timed_out", ("JobTimedOut",), "時計"),
    ("InProgress", "AwaitingAnswer", "ask", ("QuestionAsked",), "AI"),
    ("AwaitingAnswer", "Ready", "answer", ("QuestionAnswered",), "人"),
    ("InProgress", "Submitted", "submit", ("ResultSubmitted",), "AI"),
    ("InProgress", "Failed", "fail", ("JobFailed",), "AI"),
    ("InProgress", "Failed", "hand_over", ("AssessmentWritten", "JobFailed"), "AI"),
    ("InProgress", "Failed", "exhaust", ("JobFailed",), "AI"),
    ("Submitted", "AwaitingApproval", "run_check", ("CheckPassed",), "時計"),
    ("Submitted", "Ready", "run_check", ("CheckStopped", "Retried"), "時計"),
    ("Submitted", "Failed", "run_check", ("CheckStopped", "JobFailed"), "時計"),
    ("AwaitingApproval", "Cleared", "approve", ("Approved",), "人"),
    ("AwaitingApproval", "Ready", "send_back", ("SentBack",), "人"),
    ("InProgress", "Ready", "send_back", ("SentBack",), "人"),
    ("InProgress", "Abandoned", "abandon", ("JobAbandoned",), "人"),
    ("Failed", "Ready", "sort_failures", ("Retried",), "時計"),
    ("Failed", "Failed", "hand_over", ("AssessmentWritten",), "AI"),
    ("Failed", "Ready", "send_back", ("SentBack",), "人"),
    ("Failed", "Abandoned", "abandon", ("JobAbandoned",), "人"),
    ("Cleared", "Finished", "confirm", ("JobFinished",), "時計"),
    ("Cleared", "FinishedPendingRecheck", "confirm", ("JobFinished",), "時計"),
    ("FinishedPendingRecheck", "Finished", "confirm", ("JobFinished",), "時計"),
    (
        "FinishedPendingRecheck",
        "FinishedPendingRecheck",
        "confirm",
        ("RecheckDatePushed",),
        "時計",
    ),
    ("FinishedPendingRecheck", "Ready", "send_back", ("SentBack",), "人"),
]

TRANSITIONS: tuple[Transition, ...] = tuple(
    Transition(frm=f, to=t, operation=o, events=e, actor=a) for f, t, o, e, a in _ROWS
)

#: 人しか起こせない操作（I7 — 公理の執行者）。
#: **日本語の正本は設計の公理の1行**。数はそこにしか書かない（掟3）。
#: `request`・`add_version` も人が始めるが、判断を渡す操作ではないのでここには入らない。
HUMAN_ONLY_BY_WORD: dict[str, str] = {
    "承認": "approve",
    "差し戻し": "send_back",
    "回答": "answer",
    "有効化": "activate",
    "打ち切り": "abandon",
}
HUMAN_ONLY: frozenset[str] = frozenset(HUMAN_ONLY_BY_WORD.values())
