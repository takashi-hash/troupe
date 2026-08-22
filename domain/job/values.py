"""仕事の集約が持つ値。

設計: 設計/仕事とは何か.md §2「仕事」・§3。

版から写したもの（やること・受け入れ基準・受け持ちの人・使用上限・源・周期・
やり直しの上限）は `domain.rule.values` に住む。**写すのであって、指すのではない。**
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from domain.rule.values import Budget, RuleName, Source
from domain.shared import Cycle, Human, Owner, Period, Value, not_blank


class JobId(Value):
    """仕事の識別子 — 一意。あとから変えない。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.text, "仕事の識別子")
        if self.text != self.text.strip():
            raise ValueError("仕事の識別子の前後に空白があります")
        return self


class Origin(Value):
    """作成元 — どこから生まれたか。二度作らない鍵（I3）。

    同じ中身なら同じ鍵の文字列。
    """

    key: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.key, "作成元の鍵")
        return self

    @classmethod
    def from_request(cls, request_id: str) -> Origin:
        return cls(key=f"request:{not_blank(request_id, '依頼の識別子')}")

    @classmethod
    def from_rule(cls, rule: RuleName, version: int, period: Period) -> Origin:
        return cls(key=f"rule:{rule.text}:v{version}:{period.text}")


class DueDate(Value):
    """期日 — 終えるべき時刻。起点の時刻を受け取って比べる（I12）。"""

    start: datetime
    at: datetime

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.at <= self.start:
            raise ValueError("期日が起点の時刻より後ではありません")
        return self

    @classmethod
    def from_start(cls, start: datetime, days: int) -> DueDate:
        """起点の時刻 ＋ 版の日数。"""
        return cls(start=start, at=start + timedelta(days=days))


class RecheckDate(Value):
    """確かめ期日 — 根拠が無いまま終えたとき、あとで確かめる時刻。

    前の確かめ期日（無ければ期日）＋ 写した周期。AI が決めるのではない。
    送るたびに先へ進む。
    """

    after: datetime
    at: datetime

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.at <= self.after:
            raise ValueError("確かめ期日が期日より後ではありません")
        return self

    @classmethod
    def first(cls, due: DueDate, cycle: Cycle) -> RecheckDate:
        return cls(after=due.at, at=due.at + cycle.span)

    def push(self, cycle: Cycle) -> RecheckDate:
        """先へ送る。送るたびに進む。"""
        return RecheckDate(after=self.at, at=self.at + cycle.span)


class Spent(Value):
    """使った量 — これまでに使った回数と秒。上限とは別の値。"""

    calls: int = 0
    seconds: int = 0

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.calls < 0 or self.seconds < 0:
            raise ValueError("使った量は回数も秒も0以上です")
        return self

    def plus(self, calls: int, seconds: int) -> Spent:
        return Spent(calls=self.calls + calls, seconds=self.seconds + seconds)

    def within(self, budget: Budget) -> bool:
        """I14 — 使った量は使用上限を超えない。"""
        return self.calls <= budget.calls and self.seconds <= budget.seconds


class Request(Value):
    """依頼 — 人が「これをやって」と言った事実。"""

    by: Human
    at: datetime
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "依頼の中身")
        return self


class Result(Value):
    """成果 — 仕事が生んだもの。出したら書き換えない。

    在りかは持たない——積んだ Store が返し、仕事が持つ。
    """

    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "成果の中身")
        return self


class Evidence(Value):
    """根拠 — 終わったと言える裏づけ。源から読んだ引用。AI の言葉は根拠にならない。

    どの源から読んだかを持つ（積んだ先ではない）。
    """

    quote: str
    read_from: Source

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.quote, "根拠の引用")
        return self


class Approval(Value):
    """承認 — 人が「進んでよい」と決めた事実。誰がといつを両方持つ。"""

    by: Human
    at: datetime


class SendBack(Value):
    """差し戻し — 人が「まだだ」と決めた事実。"""

    by: Human
    at: datetime
    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.reason, "差し戻しの理由")
        return self


class Question(Value):
    """質問 — 材料が足りないとき AI が尋ねること。判断は求めない。

    相手は仕事の受け持ちの人——AI が選ばない。
    """

    body: str
    to: Owner

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "質問の中身")
        return self


class Answer(Value):
    """回答 — 人が答えた事実。答えは根拠にならない。"""

    by: Human
    at: datetime
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "回答の中身")
        return self


class Assessment(Value):
    """見立て — AI が状況を読んだ結果と理由。判断ではない。

    見立てが無いと AI は数字しか出せない——
    「20回使い切りました」ではなく「20回とも同じ理由で落ちました」と言えること。
    """

    finding: str
    reason: str
    at: datetime

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.finding, "見立ての結果")
        not_blank(self.reason, "見立ての理由")
        return self


class Mark(StrEnum):
    """整えた応答の印。LLM が名乗る。仕様が検める。"""

    RESULT = "result"
    QUESTION = "question"
    NEITHER = "neither"


class Reply(Value):
    """整えた応答 — LLM の応答を腐敗防止層が整えたもの。印と本文。

    印を名乗るのは LLM（adapters は運ぶだけ）。印は自己申告——仕様が検める（I16）。
    """

    mark: Mark
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "応答の本文")
        return self
