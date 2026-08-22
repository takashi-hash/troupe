"""整えた応答 — LLM の応答を腐敗防止層が整えたもの。印と本文。

設計: 設計/仕事とは何か.md §2「仕事」・§3・不変条件 I16。
| `Reply` | 本文が空でない。**印は成果・質問・どちらでもない の3つのどれか**。
**印を名乗るのは LLM**（adapters は運ぶだけ）。**印は自己申告——仕様が検める** |
印の無い応答が仕様に届いたら赤 |

**生の応答が帳簿へ入らない（I16）。** 腐敗防止層がここへ整え、
成果・質問・見立ての**どれか1つ**になってから入る。

**なぜ印を LLM が名乗るのか。** domain は外の道具を置けない。
だから「この応答は質問か」を中で判定できない——判定するには
LLM を呼ぶ道具が要り、それは外・汎用のものだから。
そこで LLM に名乗らせ、**その名乗りを仕様が検める。**
adapters は名乗りを運ぶだけで、名乗りを信じるかどうかは決めない。
**印は自己申告**——ここが通しているのは「名乗りが在ること」であって、
「名乗りが正しいこと」ではない。

**印は整えた応答の一部**——`Mark` がここに同居するのは分割漏れではなく、
印だけを別の概念として運ぶ者が居ないから。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class Mark(StrEnum):
    """印 — 成果・質問・どちらでもない。**4つ目は無い。** 名乗るのは LLM。"""

    RESULT = "result"
    QUESTION = "question"
    NEITHER = "neither"


class Reply(Value):
    """整えた応答 — 印と本文。**生の応答ではない。** 印は自己申告、検めるのは仕様。"""

    mark: Mark
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "整えた応答の本文")
        return self
