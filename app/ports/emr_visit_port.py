"""訪問の終わりへの口。**人の操作だけが呼ぶ。**

設計: 設計/仕事が回る筋道.md §4。
| `EmrVisitPort` | Port | その日の訪問を終わらせる——**署名済みの記録を積み・訪問を
実施済みへ・使った下書きに印**（診療録の1トランザクション）／**この1回だけ理由つきで
中止へ**。**人の操作だけが呼ぶ**。積んだ記録を書き換える・消す口は無い | **app** | adapters |
`sign_note`・`cancel_visit` |

**署名は予定のままの訪問にだけ。** 実施済み・中止済みへの署名は診療録側の守り
（status のガードと1訪問1記録の一意鍵）が拒み、理由の文字で返る。
"""

from __future__ import annotations

from typing import Protocol


class EmrVisitPort(Protocol):
    def sign(
        self,
        visit_id: str,
        signer: str,
        s: str,
        o: str,
        a: str,
        p: str,
        draft_id: str | None,
    ) -> str | None:
        """署名して訪問を終える。通れば None、断られたら理由の文字。

        1トランザクション: 記録を積む・訪問を実施済みへ・下書きに使用の印。
        どれか1つでも通らなければ全部を巻き戻す。
        """
        ...

    def cancel(self, visit_id: str, reason: str, by: str) -> str | None:
        """この1回だけ理由つきで中止へ。予定のままの訪問にだけ。通れば None。"""
        ...
