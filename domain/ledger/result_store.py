"""成果の置き場 — 積むと在りかが返る。

設計: 設計/仕事が回る筋道.md §4（interface の正本）。
| `ResultStore` | Store | 成果を積む | domain | adapters | 積む: `submit` ／ 読む: `run_check`・`gather_today`・詳細 |

**Store の「積む」は在りかを返す**——在りかを別に振ると、振る者と積む者が2つになる。
`Result` は在りかを持たない——ここが返し、仕事が持つ。
"""

from __future__ import annotations

from typing import Protocol

from domain.values.job.result import Result


class ResultStore(Protocol):
    """置き場の宣言。実装は adapters、注ぐのは main.py だけ。"""

    def put(self, result: Result) -> str:
        """成果を積み、在りかを返す。振る者と積む者を2つにしない。"""
        ...

    def get(self, at: str) -> Result | None:
        """在りかで1件。無ければ None。"""
        ...
