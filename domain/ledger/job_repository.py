"""仕事の帳簿 — 集約ルートを鍵で1件。**書き込みの門。**

設計: 設計/仕事が回る筋道.md §4（interface の正本）・不変条件 I1。
| `JobRepository` | Repository | 仕事の集約ルートを鍵で1件 | domain | adapters | 集約: 仕事（I1）／すべての書き込み |

**積むのは（次の姿, 出来事の列）の対だけ**——出来事なしで状態を書く口が無い。
これが I1（状態が変わったら、理由のドメインイベントが必ず一緒に残る）の最終の執行者。
楽観ロックは adapters の中に隠す——業務の語ではない。
"""

from __future__ import annotations

from typing import Any, Protocol

from domain.aggregates.job.job import Job
from domain.events.event import Event
from domain.values.job.job_id import JobId


class JobRepository(Protocol):
    """帳簿の宣言。実装は adapters、注ぐのは main.py だけ。"""

    def load(self, id: JobId) -> Job[Any] | None:
        """鍵で1件。無ければ None。返すのは集約ルートだけ。"""
        ...

    def save(self, job: Job[Any], events: tuple[Event, ...]) -> None:
        """書き込みの門 — 姿と出来事を**一緒に**積む（I1）。出来事が空なら拒む。"""
        ...
