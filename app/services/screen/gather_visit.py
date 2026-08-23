"""訪問を集める — 1訪問の当日入力の材料を写す。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの §1「当日入力」。
| 訪問を集める | `gather_visit` | 1訪問の当日入力の材料（患者の要約・未使用の下書き・
署名済みの記録・担当の名簿）を写す | 読むだけ。**中の語に翻訳しない** |
"""

from __future__ import annotations

from app.dto.visit_view import VisitView
from app.ports.visit_reader import VisitReader


def gather_visit(visits: VisitReader, visit_id: str) -> VisitView | None:
    """1訪問の材料。居なければ None。読むだけ——どこにも書かない。"""
    return visits.read_one(visit_id)
