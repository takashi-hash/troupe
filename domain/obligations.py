"""全部に共通の義務。

設計: 設計/仕事とは何か.md §3「全部に共通の義務」。

| 共通の義務 | 壊しかた |
|---|---|
| 作るときに検証を通る | 不正な中身で作れたら赤 |
| 同じ中身なら等しい。同じ辞書の鍵になる | 同じ中身の2つが等しくなければ赤 |
| 作ったあと書き換えられない | 属性への代入が通ったら赤 |

**ここに概念は置かない。** 概念はそれぞれのファイルで閉じる。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Value(BaseModel):
    """値オブジェクト。**分類は名札で、義務が本体。**"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    def __hash__(self) -> int:
        """同じ中身なら、同じ辞書の鍵になる。

        pydantic が frozen から作るものと同じだが、**明示する**——
        義務は本体なので、継承ごしに察してもらう形では置かない。
        """
        return hash((type(self), tuple(self.__dict__.values())))


def not_blank(text: str, what: str) -> str:
    """空でないことを、作るときに確かめる。"""
    if not text.strip():
        raise ValueError(f"{what}が空です")
    return text
