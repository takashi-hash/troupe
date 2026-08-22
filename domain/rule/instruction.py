"""やること — その仕事で何をするのか。**AI が読む指示。**

設計: 設計/仕事とは何か.md §2「決まり」・§3。
| `Instruction` | **空でない**。AI が読んで何をするか分かる文 | 空で作れたら赤 |

**版が「やること」を持つのが要。**
持たないと **AI は何をすればよいか永久に知れない。**
版が持ち、仕事が生まれるときに**写される**——指すのではない。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class Instruction(Value):
    """やること — AI が読んで何をするか分かる文。**コードではなくデータ。**"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.text, "やること")
        return self
