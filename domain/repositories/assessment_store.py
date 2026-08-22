"""見立ての置き場 — 積むと在りかが返る。仕事ごとに列で読める。

設計: 設計/仕事が回る筋道.md §4（interface の正本）。
| `AssessmentStore` | Store | 見立てを積む | domain | adapters | 積む: `assess` ／ 読む: `gather_today`・詳細 |

**Store の「積む」は在りかを返す。** 見立ては仕事へ紐づけて積む——
「いまこの仕事に見立てを書くべきか」（F6——同じ見立てを二度書かない）が
これまでの見立てを材料に取るので、仕事ごとの列で読める。
"""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.job_id import JobId


class AssessmentStore(Protocol):
    """置き場の宣言。実装は adapters、注ぐのは main.py だけ。"""

    def put(self, job: JobId, a: Assessment) -> str:
        """見立てを仕事へ紐づけて積み、在りかを返す。"""
        ...

    def list_for(self, job: JobId) -> tuple[Assessment, ...]:
        """仕事ごとの列。無ければ空の列。"""
        ...
