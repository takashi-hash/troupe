"""履歴の材料の読み。

設計: 設計/仕事が回る筋道.md §4・人に見えるもの.md §1「履歴」・§2「履歴の行」。
| `HistoryReader` | Reader | 出来事の行を新しい順に——**仕事の識別子と見出しの材料**
（`RuleName`・対象期間・やること）を添えて | **app** | adapters | `gather_history` |

**Reader の返す型は渡す先で決まる**——渡る先は画面なので、**文字と ID だけ**。
見出しに組むのは app（`gather_history`）——ここは材料を運ぶだけ。
"""

from __future__ import annotations

from typing import Protocol

from domain.obligations import Value


class HistoryEntry(Value):
    """履歴の材料 — 出来事1件と、どの仕事かの見出しの材料。文字と ID だけ。"""

    #: 時刻・誰が・何が起きたか（出来事の識別子——語に写すのは app）。
    at: str
    by: str
    name: str

    #: どの仕事か。
    job_id: str

    #: 見出しの材料 — 業務ルールと対象期間（依頼発は空）、やること。
    rule: str | None
    period: str | None
    instruction: str


class HistoryReader(Protocol):
    def read_latest(self, limit: int) -> tuple[HistoryEntry, ...]:
        """出来事の行を新しい順に。集約を再構成しない——画面に要る形で引く。"""
        ...
