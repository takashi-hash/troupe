"""依頼 — 人が「これをやって」と言った事実。

設計: 設計/仕事とは何か.md §2「仕事」・§3。
| `Request` | 頼んだ人・時刻・中身を持つ | どれか欠けて作れたら赤 |

**頼めるのは人だけ。** AI は仕事をこなすが、頼まない。
"""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank
from domain.values.people.human import Human


class Request(Value):
    """依頼 — 頼んだ人・時刻・中身の3つで、起きた事実を固定する。"""

    by: Human
    at: datetime
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "依頼の中身")
        return self
