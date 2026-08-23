"""出来事の共通 — いつ・誰が。

設計: 設計/仕事が回る筋道.md §5「ドメインイベント」。
**過去形。観察だけ。判断を含まない。積むだけ。**

すべての出来事が「いつ・誰が」を持つ。各出来事は**それに足して残るもの**だけを書く
——共通を書き分けると、どこかで落ちる。
`at` はいまを引数で受け取る（domain に時計は置けない）。
"""

from __future__ import annotations

from datetime import datetime

from domain.obligations import Value
from domain.value_objects.people.actor import Actor


class Event(Value):
    """出来事 — いつ・誰が起こしたか。"""

    #: いつ — 起きた時刻。引数で受け取る。
    at: datetime

    #: 誰が — 起こす者（人・AI・時計）。担当とは別。
    by: Actor


#: 日本語⇄識別子の橋（設計 §5 の出来事の欄）。画面の詰め替えと突合が使う。
EVENT_WORDS: dict[str, str] = {
    "仕事が頼まれた": "JobRequested",
    "仕事が作られた": "JobCreated",
    "仕事が配られた": "JobHandedOut",
    "着手された": "JobStarted",
    "手放された": "JobReleased",
    "時間切れで戻った": "JobTimedOut",
    "成果が出された": "ResultSubmitted",
    "検査に通った": "CheckPassed",
    "検査で止まった": "CheckStopped",
    "承認された": "Approved",
    "差し戻された": "SentBack",
    "終わった": "JobFinished",
    "確かめ期日が先へ送られた": "RecheckDatePushed",
    "打ち切られた": "JobAbandoned",
    "期日を過ぎた": "DueDatePassed",
    "下書きが配達された": "DraftDelivered",
    "失敗した": "JobFailed",
    "もう一度やった": "Retried",
    "使った量が増えた": "SpentIncreased",
    "質問された": "QuestionAsked",
    "答えられた": "QuestionAnswered",
    "見立てが書かれた": "AssessmentWritten",
    "版が足された": "RuleVersionAdded",
    "業務ルールが有効になった": "RuleActivated",
    "業務ルールが止められた": "RuleDeactivated",
}
