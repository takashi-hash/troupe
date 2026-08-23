"""診療録の読み。**よそのコンテキストの写し——中の語に翻訳しない。**

設計: 設計/仕事が回る筋道.md §4・人に見えるもの.md §1「患者」・§2。
| `PatientReader` | Reader | 診療録の患者の行とカルテ抽出を**文字と ID のまま**引く——
**よそのコンテキストの写し。中の語に翻訳しない**（患者は一座の集約にならない——境界の外）
| **app** | adapters | `gather_patients`・`gather_patient` |

**患者は一座の集約にならない。** 診療録は事業所の正本で、一座は客。
よそのエンティティを自分の domain に写して集約を立てると、境界が侵食される
——だから domain を通らず、Reader が画面に要る形（文字と ID）で引くだけ。
書く口は無い。
"""

from __future__ import annotations

from typing import Protocol

from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientView


class PatientReader(Protocol):
    def read_all(self) -> tuple[PatientRow, ...]:
        """患者の行の一覧。診療録が繋がっていなければ空。"""
        ...

    def read_one(self, code: str) -> PatientView | None:
        """1人のカルテ抽出。居なければ・繋がっていなければ None。"""
        ...
