"""源 — 材料の在りか。**AI が読みに行く先。**

設計: 設計/仕事とは何か.md §2「決まり」・§3。
| `Source` | 在りかが空でない | 空で作れたら赤 |

**在りかだけを持つ。** 読んだ中身は持たない——読むのは外で、
外の言葉は腐敗防止層を通ってから中へ入る。
"""

from __future__ import annotations

from typing import Final, Self

from pydantic import model_validator

from domain.obligations import Value, not_blank

#: 患者の穴 — 穴を持つ版は患者ごとに展開され、写すときに患者記号で開く（筋道 §1 `create`）。
PATIENT_HOLE: Final = "{患者}"


class Source(Value):
    """源 — AI がどこを読むか。版が持ち、仕事へ写される。"""

    location: str

    @property
    def has_hole(self) -> bool:
        """在りかに患者の穴が残っているか。仕事に写る時点では偽。"""
        return PATIENT_HOLE in self.location

    def open_for(self, patient: str) -> Source:
        """穴を患者記号で開く。**版から写すときに1度だけ通る。**"""
        return Source(location=self.location.replace(PATIENT_HOLE, patient))

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.location, "源の在りか")
        return self
