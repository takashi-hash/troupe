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
        """**受けに在る状態にできたら True。** 届かなかったときだけ False。

        既に在った（一意の鍵に弾かれた）も True——望んだ姿には既に成っている。
        **False-on-重複 で実装してはいけない**: 置いてから刻む順なので、置けたのに
        刻めず落ちた仕事は、次の脈の再置きが True を返して初めて印を刻める。
        重複を False にすると、その仕事は永遠に印を刻めない。
        """
        ...
