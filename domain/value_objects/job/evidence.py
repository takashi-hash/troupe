"""根拠 — 終わったと言える裏づけ。

設計: 設計/仕事とは何か.md §2「仕事」・§3・不変条件 I5。
| `Evidence` | **源から読んだ引用が空でない**。**どの源から読んだか**を持つ（積んだ先ではない） | 引用の空な根拠が作れたら赤 |

**AI の言葉は根拠にならない。** 源から読んだ引用だけが根拠になるので、
どの源から読んだかを必ず持つ。持つのは**読んだ源**であって、積んだ先ではない。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank
from domain.value_objects.rule.source import Source


class Evidence(Value):
    """根拠 — 源から読んだ引用と、その源。**AI の言葉は入らない。**"""

    quote: str
    source: Source

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.quote, "根拠の引用")
        return self
