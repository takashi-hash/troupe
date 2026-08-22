"""源の口の壊しかた。設計/仕事が回る筋道.md §4——出口は引用・読めなかった理由の2つ。

材料の出口は消した——**返す者の居ない出口は置かない**（積む者が空の Store と同型）。
読めた中身は引用として返り、そのまま LLM の材料にも根拠にもなる。
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError
from typing import get_type_hints

from app.ports.source_port import Quote, SourceOutcome, SourcePort, Unreadable
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.rule.source import Source


def _引用() -> Quote:
    return Quote(
        evidence=Evidence(quote="8月分の請求は42件", source=Source(location="file:a.txt"))
    )


def test_出口は2つ() -> None:
    hints = get_type_hints(SourcePort.read)
    assert hints["return"] == SourceOutcome or TypeAdapter(hints["return"]).validate_python(_引用()) == _引用()


def test_引用は根拠を運ぶ() -> None:
    assert _引用().evidence.quote == "8月分の請求は42件"


def test_読めなかった理由は空にできない() -> None:
    with pytest.raises(ValidationError):
        Unreadable(reason="")


def test_出口は名乗り分けられる() -> None:
    ta = TypeAdapter(SourceOutcome)
    assert ta.validate_python(_引用()) == _引用()
    assert ta.validate_python(Unreadable(reason="無いファイル")).kind == "unreadable"
    with pytest.raises(ValidationError):
        ta.validate_python("生の文字列")
