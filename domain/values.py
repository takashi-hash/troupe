"""値オブジェクト。

設計: 設計/仕事とは何か.md §3。
**不正な値を存在させない。** 分類は名札で、義務が本体。

全部に共通の義務（frozen=True と pydantic の検証で守る）:
  - 作るときに検証を通る
  - 同じ中身なら等しい。同じ辞書の鍵になる
  - 作ったあと書き換えられない
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Value(BaseModel):
    """値オブジェクトの共通の義務をここで1度だけ守る。"""

    model_config = ConfigDict(frozen=True, extra="forbid")


def _not_blank(text: str, what: str) -> str:
    if not text.strip():
        raise ValueError(f"{what}が空です")
    return text


# ── 人と場 ───────────────────────────────────────────────


class Human(Value):
    """人 — 判断する者。"""

    kind: Literal["human"] = "human"
    name: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.name, "人の名")
        return self


class Agent(Value):
    """AI — 仕事をこなす働き手。担当を持つ。判断はしない。"""

    kind: Literal["agent"] = "agent"
    name: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.name, "AI の名")
        return self


class Clock(Value):
    """時計 — 誰も呼ばなくても回る者。起こす者にはなるが、担当にはならない。"""

    kind: Literal["clock"] = "clock"


#: 担当 — 人か AI のどちらか。3つ目は無い。
Assignee = Annotated[Human | Agent, Field(discriminator="kind")]

#: 起こす者 — 人・AI・時計のどれか。担当とは別。
Actor = Annotated[Human | Agent | Clock, Field(discriminator="kind")]


class Owner(Value):
    """受け持ちの人 — 承認をし、AI の質問を受ける人。版が決める。

    `Human` そのもの。AI は受け持ちの人になれない。
    """

    person: Human


# ── 仕事の中身 ───────────────────────────────────────────


class JobId(Value):
    """仕事の識別子 — 一意。あとから変えない。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.text, "仕事の識別子")
        if self.text != self.text.strip():
            raise ValueError("仕事の識別子の前後に空白があります")
        return self


class RuleName(Value):
    """業務ルールの識別子 — 一意。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.text, "業務ルールの識別子")
        return self


class Cycle(StrEnum):
    """周期 — 月か週。3つ目の値は無い。"""

    MONTHLY = "monthly"
    WEEKLY = "weekly"

    @property
    def span(self) -> timedelta:
        return timedelta(days=31 if self is Cycle.MONTHLY else 7)


_MONTHLY = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_WEEKLY = re.compile(r"^\d{4}-W(0[1-9]|[1-4]\d|5[0-3])$")


class Period(Value):
    """対象期間 — 月なら 2026-08、週なら 2026-W34 の形だけ。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if not (_MONTHLY.match(self.text) or _WEEKLY.match(self.text)):
            raise ValueError(f"対象期間の形が違います: {self.text!r}")
        return self

    @property
    def cycle(self) -> Cycle:
        return Cycle.MONTHLY if _MONTHLY.match(self.text) else Cycle.WEEKLY


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


class Budget(Value):
    """使用上限 — 使ってよい回数と時間。暴走を止める安全弁。"""

    calls: int
    seconds: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.calls < 1 or self.seconds < 1:
            raise ValueError("使用上限は回数も秒も1以上です")
        return self


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
        return self.calls <= budget.calls and self.seconds <= budget.seconds


class Instruction(Value):
    """やること — その仕事で何をするのか。AI が読む指示。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.text, "やること")
        return self


#: 受け入れ基準の必ず含む語に書ける差し込み。写すときに `Period` で開く。
PERIOD_SLOT = "{対象期間}"


class AcceptanceCriteria(Value):
    """受け入れ基準 — 何をもって成果とするか。

    2つに分かれる。
      ① 必ず含む語の列（空でない。**機械が見る**）
      ② 説明の文（**人と AI が読む**）
    ①に `{対象期間}` と書ける——写すときに `Period` で開くので、
    検査に届く時点では固定の文字列。
    """

    must_contain: tuple[str, ...]
    explanation: str = ""

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if not self.must_contain or any(not w.strip() for w in self.must_contain):
            raise ValueError("必ず含む語が空です")
        return self

    @property
    def opened(self) -> bool:
        """開かれていない差し込みが残っていないか。検査に届く前に真であること。"""
        return not any("{" in w for w in self.must_contain)

    def expand(self, period: Period) -> AcceptanceCriteria:
        """`{対象期間}` を `Period` で開く。仕事が版から写すときに1度だけ呼ぶ。"""
        return AcceptanceCriteria(
            must_contain=tuple(w.replace(PERIOD_SLOT, period.text) for w in self.must_contain),
            explanation=self.explanation,
        )


class Source(Value):
    """源 — 材料の在りか。AI が読みに行く先。"""

    locator: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.locator, "源の在りか")
        return self


class Origin(Value):
    """作成元 — どこから生まれたか。二度作らない鍵（I3）。

    同じ中身なら同じ鍵の文字列。
    """

    key: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.key, "作成元の鍵")
        return self

    @classmethod
    def from_request(cls, request_id: str) -> Origin:
        return cls(key=f"request:{_not_blank(request_id, '依頼の識別子')}")

    @classmethod
    def from_rule(cls, rule: RuleName, version: int, period: Period) -> Origin:
        return cls(key=f"rule:{rule.text}:v{version}:{period.text}")


class Request(Value):
    """依頼 — 人が「これをやって」と言った事実。"""

    by: Human
    at: datetime
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.body, "依頼の中身")
        return self


class Result(Value):
    """成果 — 仕事が生んだもの。出したら書き換えない。

    在りかは持たない——積んだ Store が返し、仕事が持つ。
    """

    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.body, "成果の中身")
        return self


class Evidence(Value):
    """根拠 — 終わったと言える裏づけ。源から読んだ引用。AI の言葉は根拠にならない。

    どの源から読んだかを持つ（積んだ先ではない）。
    """

    quote: str
    read_from: Source

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.quote, "根拠の引用")
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
        _not_blank(self.reason, "差し戻しの理由")
        return self


class Question(Value):
    """質問 — 材料が足りないとき AI が尋ねること。判断は求めない。

    相手は仕事の受け持ちの人——AI が選ばない。
    """

    body: str
    to: Owner

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.body, "質問の中身")
        return self


class Answer(Value):
    """回答 — 人が答えた事実。"""

    by: Human
    at: datetime
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        _not_blank(self.body, "回答の中身")
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
        _not_blank(self.finding, "見立ての結果")
        _not_blank(self.reason, "見立ての理由")
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
        _not_blank(self.body, "応答の本文")
        return self


# ── 決まり ──────────────────────────────────────────────


class Version(Value):
    """版 — 業務ルールの1つの姿。積むだけ。

    版が「やること」を持つのが要。持たないと AI は何をすればよいか永久に知れない。
    """

    number: int
    instruction: Instruction
    criteria: AcceptanceCriteria
    cycle: Cycle
    days: int
    budget: Budget
    owner: Owner
    source: Source
    max_retries: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.number < 1:
            raise ValueError("版の番号は1以上です")
        if self.days < 1:
            raise ValueError("終えるまでの日数は1以上です")
        if self.max_retries < 0:
            raise ValueError("やり直しの上限は0以上です")
        return self


class Copied(Value):
    """写すものの束 — 版から仕事へ写す中身 ＋ 終えるまでの日数。

    版そのものは渡さない。日数は仕事が持たない——`DueDate` になって消える。
    """

    instruction: Instruction
    criteria: AcceptanceCriteria
    owner: Owner
    budget: Budget
    source: Source
    cycle: Cycle
    max_retries: int
    days: int
