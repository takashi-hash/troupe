"""今日に出すか — いまこの人の目と判断が要る仕事はどれか。

設計: 設計/人に見えるもの.md §4・仕事が回る筋道.md §2「ドメインサービス」。
| いま**この人の**目と判断が要る仕事はどれか | `judge_today` | 今日の材料の集まり ＋ **それぞれの押せることの列** ＋ **いま** | どの仕事のものでもない |

出すもの: 承認を待っている／答えを待っている／**見立てが書かれた**（実行中・失敗した に限る）／
期日を過ぎていて人が押せる操作がある／確かめ期日が来た自己申告／やり直しが尽きて残っている。
出さないもの: AI が実行中で見立ての書かれていない仕事・自動でやり直している最中の失敗・
期日前で押せる操作が無い仕事（**押せる操作があれば期日前でも出る**）・終わった仕事・打ち切った仕事。

**各行が「人がいま押せること」を1つ以上持つ。持たない行は出さない。**
**呼ぶ順は 今日の材料 → 押せること → judge_today。** 押せることが空の行は返さない。
"""

from __future__ import annotations

from datetime import datetime

from domain.value_objects.job.today_material import TodayMaterial


def judge_today(material: TodayMaterial, actions: tuple[str, ...], now: datetime) -> bool:
    """出すなら真。押せることが空なら必ず偽——先の予定は今日に載せない（赤が埋もれる）。"""
    if not actions:
        return False
    if material.state_name == "AwaitingApproval":
        return True
    if material.state_name == "AwaitingAnswer":
        return True
    if material.assessments and material.state_name in ("InProgress", "Failed"):
        return True
    if now > material.due.at:
        return True
    if material.recheck_at is not None and material.recheck_at <= now:
        return True
    if material.retries_exhausted:
        return True
    return False
