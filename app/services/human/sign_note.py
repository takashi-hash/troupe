"""署名して訪問を終える — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・人に見えるもの §1「当日入力」。
| 署名して訪問を終える | `sign_note` | 下書きを下敷きに人が書き上げた S/O/A/P を
**署名済みの記録**として診療録に積み、訪問を実施済みへ倒し、使った下書きに使用の印を
入れる（**診療録の1トランザクション**）。**この記録を事実とするのが判断** |

帳簿には書かない——カルテの正本は診療録。**S/O/A/P はどれも空で署名できない**
（空の記録に署名の意味は無い）。組めない文字は断りに変わる。
"""

from __future__ import annotations

from app.ports.emr_visit_port import EmrVisitPort
from app.services.refusal import Refusal


def sign_note(
    visits: EmrVisitPort,
    visit_id: str,
    signer: str,
    s: str,
    o: str,
    a: str,
    p: str,
    draft_id: str = "",
    *,
    by: str,
) -> Refusal | None:
    """通れば None。断られたら理由。署名者が空なら判断の主が居ない——断り。"""
    if not by.strip():
        return Refusal(reason="誰の判断かが空です")
    if not visit_id.strip():
        return Refusal(reason="どの訪問かが空です")
    if not signer.strip():
        return Refusal(reason="署名者が空です")
    for 欄, 値 in (("S", s), ("O", o), ("A", a), ("P", p)):
        if not 値.strip():
            return Refusal(reason=f"{欄} が空です——空の記録に署名はできません")
    なぜ = visits.sign(
        visit_id.strip(), signer.strip(), s.strip(), o.strip(), a.strip(), p.strip(),
        draft_id.strip() or None,
    )
    return None if なぜ is None else Refusal(reason=なぜ)
