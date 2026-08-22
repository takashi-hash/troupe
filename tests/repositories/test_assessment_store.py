"""見立ての置き場の宣言の壊しかた。設計/仕事が回る筋道.md §4。

宣言は Protocol——実装の義務はここで言い切り、実装のテストが同じ検査を通る。
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from domain.repositories.assessment_store import AssessmentStore
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.job_id import JobId


def test_積むと在りかが返る() -> None:
    """Store の積むは在りかを返す——振る者と積む者を2つにしない。"""
    hints = get_type_hints(AssessmentStore.put)
    assert hints["job"] == JobId
    assert hints["a"] == Assessment
    assert hints["return"] is str
    params = list(inspect.signature(AssessmentStore.put).parameters)
    assert params == ["self", "job", "a"]


def test_読みは仕事ごとの列() -> None:
    """「同じ見立てを二度書かない」（F6）がこれまでの見立てを材料に取る。"""
    hints = get_type_hints(AssessmentStore.list_for)
    assert hints["return"] == tuple[Assessment, ...]
    params = list(inspect.signature(AssessmentStore.list_for).parameters)
    assert params == ["self", "job"]
