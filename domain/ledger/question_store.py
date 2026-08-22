"""質問と回答の置き場 — 質問を積むと在りかが返り、回答はその在りかへ紐づく。

設計: 設計/仕事が回る筋道.md §4（interface の正本）。
| `QuestionStore` | Store | 質問と回答を積む | domain | adapters | 積む: `ask`・`answer` ／ 読む: `gather_today`・詳細（**`start` は `WorkReader` から読む**） |

**Store の「積む」は在りかを返す。** 回答は質問の在りかへ紐づけて積む——
回答だけが宙に浮く形が書けない。読みは（質問, 回答または None）の対で返る。
"""

from __future__ import annotations

from typing import Protocol

from domain.values.job.answer import Answer
from domain.values.job.question import Question


class QuestionStore(Protocol):
    """置き場の宣言。実装は adapters、注ぐのは main.py だけ。"""

    def put_question(self, q: Question) -> str:
        """質問を積み、在りかを返す。振る者と積む者を2つにしない。"""
        ...

    def put_answer(self, question_at: str, a: Answer) -> None:
        """回答を質問の在りかへ紐づけて積む。"""
        ...

    def get(self, at: str) -> tuple[Question, Answer | None] | None:
        """在りかで1件——（質問, 回答または None）の対。無ければ None。"""
        ...
