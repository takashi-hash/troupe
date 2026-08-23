"""診療録の下書き受けへの口。**draft としてだけ置く——署名済みに書く口は無い。**

設計: 設計/仕事が回る筋道.md §4・人に見えるもの.md §2「患者の詳細」。
| `EmrDraftPort` | Port | 承認の済んだ下書きを診療録の**下書き受けにだけ**置く——
**署名済みの記録（final）に書く口は無い**。置けたかを返す（一意の鍵で冪等）
| **app** | adapters | `deliver_drafts` |

**掟の狭い緩め。** 診療録は読むだけ、が原則だった。着地を許すのは下書き受け1つ——
提案（Troupe の成果）が看護師の手元に届くための郵便受けであって、
事実（署名済みの記録）には未来永劫、手が届かない。
署名は看護師が診療録の側でする——一座に署名の操作は無い。
"""

from __future__ import annotations

from typing import Protocol


class EmrDraftPort(Protocol):
    def deposit(self, job_id: str, patient_code: str, body: str) -> bool:
        """下書き受けに置く。置けたら True、既に同じ仕事から置いていたら False。

        冪等の鍵は仕事の識別子——**同じ仕事から二度置かない**。
        """
        ...
