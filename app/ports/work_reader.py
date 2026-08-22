"""AI が1件こなすのに要る材料の読み。

設計: 設計/仕事が回る筋道.md §4。
| `WorkReader` | Reader | **AI が1件こなすのに要る材料**——やること・受け入れ基準・源・
答えのある質問・前に出した成果の中身・**落ちた中身と止まった理由の列**・これまでの見立て・
使った量と上限・やり直した回数と上限・**確かめ期日**・**同じ `RuleName`・同じ `Period` の、
別の版から生まれた仕事の状態** | **app** | adapters | AI が始めるものすべて |

**やること・受け入れ基準・源・使った量と上限・やり直した回数と上限・確かめ期日は
集約が持っている**——`JobRepository` で読めるものをここでも運ぶと正本が2つになる。
ここが運ぶのは**集約の外**（Store と、別の仕事）に在るものだけ。
見立てだけ domain の値——渡る先が domain の仕様（見立てを書くべきか）だから
（**Reader の返す型は渡す先で決まる**）。
"""

from __future__ import annotations

from typing import Protocol

from domain.obligations import Value
from domain.values.job.assessment import Assessment
from domain.values.job.job_id import JobId


class WorkMaterial(Value):
    """AI が1件こなすのに要る、集約の外の材料。"""

    #: 答えのある質問 — （質問の本文, 答えの本文）の対。答えの無い質問は運ばない。
    answered_questions: tuple[tuple[str, str], ...]

    #: 前に出した成果の中身。まだ無ければ None。
    previous_result: str | None

    #: 落ちた中身と止まった理由の列。
    fall_reasons: tuple[str, ...]

    #: これまでの見立て。
    assessments: tuple[Assessment, ...]

    #: 同じ `RuleName`・同じ `Period` の、別の版から生まれた仕事の状態の名。
    sibling_states: tuple[str, ...]


class WorkReader(Protocol):
    def read(self, id: JobId) -> WorkMaterial:
        """鍵で1件ぶんの材料。集約が持つものは `JobRepository` から読む。"""
        ...
