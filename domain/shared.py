"""どちらの集約も使う語。

設計: 設計/仕事とは何か.md §2「人と場」・§3。

**ここに置くのは、仕事と業務ルールの両方が話す語だけ。**
片方しか使わないものを置くと、境界がまた見えなくなる。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Value(BaseModel):
    """値オブジェクトの共通の義務をここで1度だけ守る。

    作るときに検証を通る／同じ中身なら等しい／作ったあと書き換えられない。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


def not_blank(text: str, what: str) -> str:
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
        not_blank(self.name, "人の名")
        return self


class Agent(Value):
    """AI — 仕事をこなす働き手。担当を持つ。判断はしない。"""

    kind: Literal["agent"] = "agent"
    name: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.name, "AI の名")
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


# ── 暦（版が周期を決め、仕事が対象期間を持つ）─────────────


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


# ── 出来事の共通 ─────────────────────────────────────────


class Event(Value):
    """出来事の共通 — いつ・誰が。

    設計 §5「すべての出来事が『いつ・誰が』を持つ」。
    `at` はいまを引数で受け取る（domain に時計は置けない）。
    """

    at: datetime
    by: Actor
