"""今日の材料の読み。

設計: 設計/仕事が回る筋道.md §4。
| `TodayReader` | Reader | **今日の材料**（仕様が見る domain の値。欄は人に見えるもの §2 の
今日の行から押せることを除いたもの） | **app** | adapters | `gather_today` |

**Reader の返す型は渡す先で決まる**——渡る先は domain の仕様（押せることを組む）と
`judge_today`。だから返すのは domain の値で、**宣言が app でも依存は内向き**。
今日の行（画面が見る文字）とは別物——材料 → 仕様 → 行 の順に app が詰め替える。
"""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.today_material import TodayMaterial


class TodayReader(Protocol):
    def read(self, id: JobId) -> TodayMaterial | None:
        """1件。**終点も引ける**——詳細は終わった仕事も見る。無ければ None。"""
        ...

    def read_all(self) -> tuple[TodayMaterial, ...]:
        """一覧——**終点は運ばない**（今日に終点は出ない。それ以外を絞るのは `judge_today`）。"""
        ...
