"""LLM の道具への口。

設計: 設計/仕事が回る筋道.md §4。
| `LlmPort` | Port | LLM に渡し、**`Reply`（印つき）と、使った回数・秒**を受け取る | **app** | adapters | **`consult` だけ** |

**返す型は渡す先で決まる**——domain の仕様（振り分け）へ渡るので `Reply`。
印を名乗るのは LLM。名乗りを検めるのは domain の仕様（I16——鵜呑みにしない）。
実装は adapters の腐敗防止層。**注ぐのは main.py だけ。**
"""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.job.reply import Reply


class LlmPort(Protocol):
    def consult(
        self,
        instruction: str,
        criteria_terms: tuple[str, ...],
        criteria_note: str,
        source_material: str,
        answered_questions: tuple[tuple[str, str], ...],
        previous_result: str | None,
    ) -> tuple[Reply, int, int]:
        """材料を渡し、（整えた応答, 使った回数, 使った秒）を受け取る。"""
        ...

    def read_situation(
        self,
        situation: str,
        fall_reasons: tuple[str, ...],
        previous_result: str | None,
        sibling_states: tuple[str, ...],
    ) -> tuple[str, str, int, int]:
        """状況を読み、（見立て, そう読んだ理由, 使った回数, 使った秒）を受け取る。

        巡回が呼ぶ——**見立てが無いと AI は数字しか出せない**（設計の値打ちの行）。
        この一呼びは使用上限に数えない：安全弁（I14）は仕事を**進める**暴走を
        止めるもので、見立ての暴走は F6（同じ見立てを二度書かない）が止める。
        """
        ...
