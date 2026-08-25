"""仕事の一生 — 状態11個の閉じた直和。

設計: 設計/仕事とは何か.md §6「状態と遷移」・§7「禁止状態」。

各状態は**足して持つもの**だけを欄に持つ。**持ってはいけないものは欄が無い**
——だから書けない。閉じた直和は1つの概念なので、この1枚で閉じる。
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from domain.obligations import Value, not_blank
from domain.value_objects.job.approval import Approval
from domain.value_objects.job.recheck_date import RecheckDate
from domain.value_objects.people.assignee import Assignee
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner


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
    """答え待ち — 担当を必ず持つ。質問の本文は出来事 `QuestionAsked` が正本。"""

    name: Literal["AwaitingAnswer"] = "AwaitingAnswer"
    assignee: Assignee


class Submitted(Value):
    """提出済み — 担当を必ず持つ。承認も検査の結果も持てない。

    成果の在りかが空でないことは、仕事の共通の持ちもの側で守る。
    """

    name: Literal["Submitted"] = "Submitted"
    assignee: Assignee


class AwaitingApproval(Value):
    """承認待ち — **担当が受け持ちの人**（I6）。

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

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.fallen, "落ちた中身")
        return self


class FinishedPendingRecheck(Value):
    """終わった（確かめ待ち）— 承認と確かめ期日を必ず持つ。根拠の在りかは持てない。"""

    name: Literal["FinishedPendingRecheck"] = "FinishedPendingRecheck"
    approval: Approval
    recheck: RecheckDate


class Finished(Value):
    """終わった — 承認を必ず持つ。**終点。**

    根拠の在りかが空でないことは、仕事の共通の持ちもの側で守る。
    """

    name: Literal["Finished"] = "Finished"
    approval: Approval


class Abandoned(Value):
    """打ち切られた — 打ち切った人と理由を必ず持つ。**終点。**"""

    name: Literal["Abandoned"] = "Abandoned"
    by: Human
    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.reason, "打ち切りの理由")
        return self


#: 状態の直和（素の並び）。型変数の上限に使う。
StateUnion = (
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
    | Abandoned
)

#: 仕事の一生 — 閉じた直和。素の文字列からは作れない。
State = Annotated[StateUnion, Field(discriminator="name")]

#: 終点。ここから出る遷移は無い。
TERMINAL: frozenset[str] = frozenset({"Finished", "Abandoned"})

#: 日本語⇄識別子の橋。突合が設計の遷移表を読むのに使う。
STATE_WORDS: dict[str, str] = {
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
