"""根拠の置き場の宣言の壊しかた。設計/仕事が回る筋道.md §4。

宣言は Protocol——実装の義務はここで言い切り、実装のテストが同じ検査を通る。
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from domain.repositories.evidence_store import EvidenceStore
from domain.value_objects.job.evidence import Evidence


def test_積むと在りかが返る() -> None:
    """Store の積むは在りかを返す——振る者と積む者を2つにしない。"""
    hints = get_type_hints(EvidenceStore.put)
    assert hints["evidence"] == Evidence
    assert hints["return"] is str
    params = list(inspect.signature(EvidenceStore.put).parameters)
    assert params == ["self", "evidence"]


def test_読みは在りかで1件だけ() -> None:
    hints = get_type_hints(EvidenceStore.get)
    assert hints["return"] == Evidence | None
    params = list(inspect.signature(EvidenceStore.get).parameters)
    assert params == ["self", "at"]
