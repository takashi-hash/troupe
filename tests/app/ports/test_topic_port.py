"""題材の口の壊しかた。設計/仕事が回る筋道.md §4——初期値を読み、人が上書きする。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from app.ports.topic_port import TopicPort
from domain.value_objects.rule.copied import Copied
from domain.value_objects.rule.rule_name import RuleName


def test_読みは業務ルールの名を受けて版の中身か無しを返す() -> None:
    hints = get_type_hints(TopicPort.read)
    assert hints["rule"] is RuleName
    assert hints["return"] == Copied | None
    assert list(inspect.signature(TopicPort.read).parameters) == ["self", "rule"]
