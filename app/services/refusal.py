"""断り — 押したが、いまの姿では受けられなかったこと。

設計: 設計/人に見えるもの.md §3。
**押して何も起きないのが一番わるい。断られたら断られたと出す。**
**操作の失敗はエラーではない**——仕事の状態は変わらないので、
一生に傷をつけず、画面にだけ理由を出す。
"""

from __future__ import annotations

from typing import Self

from pydantic import ValidationError, model_validator

from domain.obligations import Value, not_blank


class Refusal(Value):
    """断り — 理由つき。None が「通った」、これが「断られた」。"""

    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.reason, "断りの理由")
        return self


def reason_of(error: ValueError) -> str:
    """エラーを断りの理由の文に。義務の文言だけを残す——機械の中身を画面に出さない。

    pydantic の検証エラーは複数の義務をまとめて言うことがある——文言を「。」で繋ぐ。
    """
    if isinstance(error, ValidationError):
        文言 = [str(e.get("msg", "")).removeprefix("Value error, ") for e in error.errors()]
        return "。".join(dict.fromkeys(文言)) or "受けられない値です"
    return str(error)
