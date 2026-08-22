"""成果の置き場の宣言の壊しかた。設計/仕事が回る筋道.md §4。

宣言は Protocol——実装の義務はここで言い切り、実装のテストが同じ検査を通る。
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from domain.ledger.result_store import ResultStore
from domain.values.job.result import Result


def test_積むと在りかが返る() -> None:
    """Store の積むは在りかを返す——振る者と積む者を2つにしない。"""
    hints = get_type_hints(ResultStore.put)
    assert hints["result"] == Result
    assert hints["return"] is str
    params = list(inspect.signature(ResultStore.put).parameters)
    assert params == ["self", "result"]


def test_読みは在りかで1件だけ() -> None:
    hints = get_type_hints(ResultStore.get)
    assert hints["return"] == Result | None
    params = list(inspect.signature(ResultStore.get).parameters)
    assert params == ["self", "at"]
