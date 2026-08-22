"""ドメインイベント。

設計: 設計/仕事が回る筋道.md §5（正本）。
**過去形。観察だけ。判断を含まない。積むだけ。**

すべての出来事が「いつ・誰が」を持つ（`Event` の共通）。
各クラスは**それに足して残るもの**だけを書く——共通を書き分けると、どこかで落ちる。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from domain.values import (
    Actor,
    Assessment,
    Assignee,
    Human,
    Owner,
    Period,
    RuleName,
    Value,
)


class Event(Value):
    """出来事の共通 — いつ・誰が。

    `at` はいまを引数で受け取る（domain に時計は置けない）。
    `by` は起こす者（人・AI・時計）。担当とは別。
    """

    at: datetime
    by: Actor


class JobRequested(Event):
    """仕事が頼まれた — 誰が・何を。"""

    name: Literal["JobRequested"] = "JobRequested"
    requested_by: Human
    body: str


class JobCreated(Event):
    """仕事が作られた — どの業務ルールの、どの版の、どの対象期間。"""

    name: Literal["JobCreated"] = "JobCreated"
    rule: RuleName | None = None
    version: int | None = None
    period: Period | None = None


class JobHandedOut(Event):
    """仕事が配られた。"""

    name: Literal["JobHandedOut"] = "JobHandedOut"


class JobStarted(Event):
    """着手された — 誰が取ったか。"""

    name: Literal["JobStarted"] = "JobStarted"
    took: Assignee


class JobReleased(Event):
    """手放された — 誰が離したか。"""

    name: Literal["JobReleased"] = "JobReleased"
    released: Assignee


class JobTimedOut(Event):
    """時間切れで戻った — 誰の担当だったか。"""

    name: Literal["JobTimedOut"] = "JobTimedOut"
    was: Assignee


class ResultSubmitted(Event):
    """成果が出された — 成果の在りか ＋ 根拠の在りか。"""

    name: Literal["ResultSubmitted"] = "ResultSubmitted"
    result_at: str
    evidence_at: str | None


class CheckPassed(Event):
    """検査に通った — 誰へ担当が移ったか。"""

    name: Literal["CheckPassed"] = "CheckPassed"
    moved_to: Owner


class CheckStopped(Event):
    """検査で止まった — 止めた理由。"""

    name: Literal["CheckStopped"] = "CheckStopped"
    reason: str


class Approved(Event):
    """承認された。**人が主語。**"""

    name: Literal["Approved"] = "Approved"


class SentBack(Event):
    """差し戻された — 誰が・理由。**人が主語。**"""

    name: Literal["SentBack"] = "SentBack"
    sent_by: Human
    reason: str


class JobFinished(Event):
    """終わった — 根拠の在りか、または確かめ期日。"""

    name: Literal["JobFinished"] = "JobFinished"
    evidence_at: str | None = None
    recheck_at: datetime | None = None


class RecheckDatePushed(Event):
    """確かめ期日が先へ送られた — 新しい確かめ期日。"""

    name: Literal["RecheckDatePushed"] = "RecheckDatePushed"
    recheck_at: datetime


class JobAbandoned(Event):
    """打ち切られた — 誰が・理由。**人が主語。**"""

    name: Literal["JobAbandoned"] = "JobAbandoned"
    abandoned_by: Human
    reason: str


class DueDatePassed(Event):
    """期日を過ぎた。遷移表の外で刻める3つのうちの1つ。"""

    name: Literal["DueDatePassed"] = "DueDatePassed"


class JobFailed(Event):
    """失敗した — 落ちた中身。"""

    name: Literal["JobFailed"] = "JobFailed"
    fallen: str


class Retried(Event):
    """もう一度やった — 何度目か。"""

    name: Literal["Retried"] = "Retried"
    times: int


class SpentIncreased(Event):
    """使った量が増えた — 増えた回数と秒。遷移表の外で刻める3つのうちの1つ。"""

    name: Literal["SpentIncreased"] = "SpentIncreased"
    calls: int
    seconds: int


class QuestionAsked(Event):
    """質問された — 何を。"""

    name: Literal["QuestionAsked"] = "QuestionAsked"
    body: str


class QuestionAnswered(Event):
    """答えられた — 誰が・何と ＋ 誰の担当が外れたか。**人が主語。**"""

    name: Literal["QuestionAnswered"] = "QuestionAnswered"
    answered_by: Human
    body: str
    unassigned: Assignee


class AssessmentWritten(Event):
    """見立てが書かれた — 読んだ中身と、そう読んだ理由。

    AI が主語だが判断ではない——事実の報告と案で、受けて決めるのは人。
    遷移表の外で刻める3つのうちの1つ。
    """

    name: Literal["AssessmentWritten"] = "AssessmentWritten"
    assessment: Assessment


class RuleVersionAdded(Event):
    """版が足された — どの版か。"""

    name: Literal["RuleVersionAdded"] = "RuleVersionAdded"
    rule: RuleName
    version: int


class RuleActivated(Event):
    """業務ルールが有効になった — 誰が・どの版か。**人が主語。**"""

    name: Literal["RuleActivated"] = "RuleActivated"
    rule: RuleName
    version: int
    activated_by: Human


#: 遷移表の外で刻んでよい出来事は、この3つだけ（設計 §6）。
OUTSIDE_TRANSITIONS: frozenset[str] = frozenset(
    {"DueDatePassed", "SpentIncreased", "AssessmentWritten"}
)
