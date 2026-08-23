"""請求の裁きと確定の口。

設計: 設計/仕事が回る筋道.md §4。
| `EmrClaimPort` | Port | 旗の行を理由つきで通す/落とす・1患者1月の請求を確定する。
**人の操作だけが呼ぶ**。確定を書き換える口は、どこにも無い | **app** | adapters |
`resolve_charge`・`confirm_claim` |
"""

from __future__ import annotations

from typing import Protocol


class EmrClaimPort(Protocol):
    def resolve(self, charge_id: str, action: str, reason: str, by: str) -> str | None:
        """旗の行を allow（理由必須——摘要の写し）か drop に裁く。通れば None。"""
        ...

    def confirm(self, patient: str, month: str, by: str) -> str | None:
        """1患者1月の請求を事実とする。月が終わっていなければ断り。通れば None。"""
        ...
