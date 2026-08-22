"""根拠の置き場 — 積むと在りかが返る。

設計: 設計/仕事が回る筋道.md §4（interface の正本）。
| `EvidenceStore` | Store | 根拠を積む | domain | adapters | 積む: `submit`・`confirm` ／ 読む: `confirm`・`gather_today`・詳細 |

**積む者が空の Store は置かない**——中身が永久に0件になる（根拠がそうなっていた）。
積まれた根拠は必ず揃っている（`Evidence` の義務）——だから `confirm` は
在りかが空でなければ読み直さずに終われる。
"""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.job.evidence import Evidence


class EvidenceStore(Protocol):
    """置き場の宣言。実装は adapters、注ぐのは main.py だけ。"""

    def put(self, evidence: Evidence) -> str:
        """根拠を積み、在りかを返す。振る者と積む者を2つにしない。"""
        ...

    def get(self, at: str) -> Evidence | None:
        """在りかで1件。無ければ None。"""
        ...
