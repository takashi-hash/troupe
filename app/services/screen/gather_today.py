"""今日の分を集める — 画面が始めるもの。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの.md §2。
| 今日の分を集める | `gather_today` | いまこの人の目と判断が要るものを集める | **判定するのは仕様**。集めて渡すだけ |

**人が画面を開いたときだけ走る。帳簿に書かない。**
**今日の材料**（仕様が見る domain の値）と**今日の行**（画面が見る文字）は別物——
材料 → 仕様 → 行 の順に詰め替える。**詰め替えるのは app**。
**呼ぶ順は 今日の材料 → 押せること → judge_today。** 押せることが空の行は返さない。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.today_reader import TodayReader
from app.dto.today_row import TodayRow
from domain.services.allowed import allowed
from domain.services.judge_today import judge_today
from domain.value_objects.job.today_material import TodayMaterial
from domain.value_objects.people.human import Human


def gather_today(today: TodayReader, clock: ClockPort, viewer: Human) -> tuple[TodayRow, ...]:
    """いまこの人の目と判断が要るものを、今日の行にして返す。読むだけ——帳簿に書かない。"""
    now = clock.now()
    rows: list[TodayRow] = []
    for material in today.read_all():
        actions = allowed(material, viewer, now)
        if not judge_today(material, actions, now):
            continue
        rows.append(_to_row(material, actions))
    return tuple(rows)


def _to_row(material: TodayMaterial, actions: tuple[str, ...]) -> TodayRow:
    """材料（domain の値）を今日の行（文字と ID）へ。本文をそのまま載せる——縮めない。"""
    return TodayRow(
        id=material.id.text,
        rule=material.rule.text if material.rule is not None else None,
        born_version=material.born_version,
        period=material.period.text if material.period is not None else None,
        request_head=material.request_head,
        state_name=material.state_name,
        due=material.due.at.isoformat(),
        assignee_name=material.assignee_name,
        recheck_at=material.recheck_at.isoformat() if material.recheck_at is not None else None,
        result_body=material.result_body,
        evidence_quote=material.evidence_quote,
        question_body=material.question_body,
        answer_body=material.answer_body,
        assessments=tuple((a.finding, a.reason) for a in material.assessments),
        retries_exhausted=material.retries_exhausted,
        spent_calls=material.spent.calls,
        spent_seconds=material.spent.seconds,
        budget_calls=material.budget.calls,
        budget_seconds=material.budget.seconds,
        owner_name=material.owner.person.name,
        actions=actions,
    )
