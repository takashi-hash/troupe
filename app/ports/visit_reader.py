"""訪問の材料の読み。

設計: 設計/仕事が回る筋道.md §4。
| `VisitReader` | Reader | 1訪問の当日入力の材料（患者の要約・未使用の下書き・
署名済みの記録・担当の名簿）を**文字と ID のまま**引く | **app** | adapters | `gather_visit` |

よそのコンテキストの写し——中の語に翻訳しない（`PatientReader` と同じ構え）。
"""

from __future__ import annotations

from typing import Protocol

from app.dto.visit_view import VisitView


class VisitReader(Protocol):
    def read_one(self, visit_id: str) -> VisitView | None:
        """1訪問の材料。居なければ・繋がっていなければ None。"""
        ...
