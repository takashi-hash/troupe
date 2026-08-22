"""業務ルールの一覧の読みの壊しかた。設計/仕事が回る筋道.md §4——予定の画面の材料。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from app.ports.rule_reader import RuleLine, RuleReader


def _行() -> RuleLine:
    return RuleLine(name="月次請求", version_number=3, active_version=2, instruction="8月分の請求を集計する")


def test_読みは全件の一覧() -> None:
    hints = get_type_hints(RuleReader.read_all)
    assert hints["return"] == tuple[RuleLine, ...]
    assert list(inspect.signature(RuleReader.read_all).parameters) == ["self"]


def test_欄は名と版の番号と有効な版とやること() -> None:
    assert set(RuleLine.model_fields) == {"name", "version_number", "active_version", "instruction"}


def test_有効な版はまだ無いことがある() -> None:
    行 = RuleLine(name="月次請求", version_number=1, active_version=None, instruction="8月分の請求を集計する")
    assert 行.active_version is None


def test_名の空な行は作れない() -> None:
    with pytest.raises(ValidationError):
        RuleLine(name="  ", version_number=1, active_version=None, instruction="集計する")


def test_やることの空な行は作れない() -> None:
    with pytest.raises(ValidationError):
        RuleLine(name="月次請求", version_number=1, active_version=None, instruction="")


def test_作ったあと書き換えられない() -> None:
    行 = _行()
    with pytest.raises(ValidationError):
        行.name = "書き換え"  # type: ignore[misc]


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert _行() == _行()
    assert {_行(): "予定"}[_行()] == "予定"
