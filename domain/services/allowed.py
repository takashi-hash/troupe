"""押せること — いまこの仕事に、この人が押せる操作はどれか。

設計: 設計/仕事が回る筋道.md §2「仕様」・人に見えるもの.md §3・仕事とは何か.md §6。
| いまこの仕事に**この人が**押せる操作はどれか | **今日の材料** ＋ **見ている人** ＋ **いま** | 操作の列。**遷移表に無い操作は返さない** |

**受け持ちの人にだけ**: 承認する・差し戻す・答える・打ち切る（人に見えるもの §3）。
実行中・失敗したの差し戻す・打ち切るは**見立てを読んで**——見立てが書かれるまで返さない
（やり直しが尽きて残っている失敗は、見立てが無くても返す）。
自己申告（終わった・確かめ待ち）の差し戻すは**確かめ期日が来てから**。
"""

from __future__ import annotations

from datetime import datetime

from domain.values.job.today_material import TodayMaterial
from domain.values.people.human import Human


def allowed(material: TodayMaterial, viewer: Human, now: datetime) -> tuple[str, ...]:
    """押せる操作の識別子の列（approve・send_back・answer・abandon）。無ければ空。"""
    if viewer != material.owner.person:
        return ()
    state = material.state_name
    if state == "AwaitingApproval":
        return ("approve", "send_back")
    if state == "AwaitingAnswer":
        return ("answer",)
    if state == "InProgress":
        return ("send_back", "abandon") if material.assessments else ()
    if state == "Failed":
        if material.assessments or material.retries_exhausted:
            return ("send_back", "abandon")
        return ()
    if state == "FinishedPendingRecheck":
        if material.recheck_at is not None and material.recheck_at <= now:
            return ("send_back",)
        return ()
    return ()
