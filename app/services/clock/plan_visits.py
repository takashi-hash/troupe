"""予定を組む — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 予定を組む | `plan_visits` | 有効な定期訪問の取り決めから、先の予定をまだ無ければ
診療録に作る。**取り決めの展開は帳簿づけ** | 作成元が一意（取り決め×日付） |

判断は取り決めを決めたとき（人）に済んでいる——ここは `create` が版×暦から
仕事を作るのと同型の、機械の展開。冪等は診療録の一意の鍵が守る。
"""

from __future__ import annotations

from app.ports.emr_schedule_port import EmrSchedulePort

#: どこまで先を組むか。実装で決めた値——4週あれば、週次の点検が穴を見る前に埋まる。
HORIZON_DAYS = 28


def plan_visits(schedule: EmrSchedulePort) -> tuple[str, ...]:
    """先の分の予定をまだ無ければ作り、新しく作った分の見出しを返す。"""
    return schedule.plan(HORIZON_DAYS)
