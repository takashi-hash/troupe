"""定期訪問を決める — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」。
| 定期訪問を決める | `add_pattern` | 患者と調整した定期訪問の取り決め（曜日・担当）を
診療録に載せる。**取り決めこそが判断** |

帳簿には書かない——取り決めは診療録（よそのコンテキスト）のマスタ。
**画面から渡るのは文字だけ**。組めない文字・載せられない取り決めは断りに変わる。
"""

from __future__ import annotations

from app.ports.emr_pattern_port import EmrPatternPort
from app.services.refusal import Refusal


def add_pattern(
    patterns: EmrPatternPort,
    patient: str, weekday: str, clinician: str, purpose: str, start: str,
    every_weeks: str = "1",
    *,
    by: str,
) -> Refusal | None:
    """通れば None。断られたら理由。人の名が空なら判断の主が居ない——断り。"""
    if not by.strip():
        return Refusal(reason="誰の判断かが空です")
    for 欄, 値 in (("患者", patient), ("曜日", weekday), ("担当", clinician), ("目的", purpose), ("始まり", start)):
        if not 値.strip():
            return Refusal(reason=f"{欄}が空です")
    なぜ = patterns.add(
        patient.strip(), weekday.strip(), clinician.strip(), purpose.strip(),
        start.strip(), every_weeks.strip() or "1",
    )
    return None if なぜ is None else Refusal(reason=なぜ)
