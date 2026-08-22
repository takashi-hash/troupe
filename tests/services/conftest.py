"""仕様とドメインサービスのテストが共有する組み立て。"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.value_objects.calendar.period import Period
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.spent import Spent
from domain.value_objects.job.today_material import TodayMaterial
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.rule_name import RuleName

いま = datetime(2026, 8, 18, 9, 2, tzinfo=UTC)
座長 = Human(name="座長")


def make_material(**over: object) -> TodayMaterial:
    """週次の依存の棚卸し・版1から生まれた仕事の今日の材料。欄は over で差し替える。

    期日は 2026-08-20 09:00——`いま` はその前（期日前）。
    """
    data: dict[str, object] = {
        "id": JobId(text="J-0001"),
        "rule": RuleName(text="週次の依存の棚卸し"),
        "born_version": 1,
        "period": Period(text="2026-W34"),
        "request_head": None,
        "instruction": Instruction(text="依存の一覧を突き合わせる"),
        "state_name": "AwaitingApproval",
        "due": DueDate.from_start(datetime(2026, 8, 17, 9, 0, tzinfo=UTC), 3),
        "assignee_name": "座長",
        "recheck_at": None,
        "result_body": "2026-W34 の依存の一覧",
        "evidence_quote": None,
        "question_body": None,
        "answer_body": None,
        "assessments": (),
        "retried": 0,
        "max_retries": 3,
        "spent": Spent(calls=3, seconds=60),
        "budget": Budget(calls=20, seconds=600),
        "owner": Owner(person=座長),
    }
    return TodayMaterial.model_validate(data | over)
