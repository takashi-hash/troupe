"""源の口の壊しかた。設計/仕事が回る筋道.md §4——出口は3つ、4つ目は無い。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from app.ports.source_port import Material, Quote, SourcePort, Unreadable
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.rule.source import Source

源 = Source(location="s3://ichiza/請求/2026-08.csv")


def test_読みは源を受けて出口3つのどれかを返す() -> None:
    hints = get_type_hints(SourcePort.read)
    assert hints["source"] is Source
    assert hints["return"] == Material | Quote | Unreadable
    assert list(inspect.signature(SourcePort.read).parameters) == ["self", "source"]


def test_3すくみは互いに判別できる() -> None:
    材料 = Material(text="8月分の請求は42件")
    引用 = Quote(evidence=Evidence(quote="請求42件、計84万円", source=源))
    読めない = Unreadable(reason="源に接続できませんでした")
    assert {材料.kind, 引用.kind, 読めない.kind} == {"material", "quote", "unreadable"}


def test_よその印は名乗れない() -> None:
    with pytest.raises(ValidationError):
        Material(kind="quote", text="8月分の請求は42件")  # type: ignore[arg-type]


def test_中身の空な材料は作れない() -> None:
    for text in ("", "   ", "\n\t"):
        with pytest.raises(ValidationError):
            Material(text=text)


def test_理由の空な読めなかったは作れない() -> None:
    for reason in ("", "   "):
        with pytest.raises(ValidationError):
            Unreadable(reason=reason)


def test_引用は根拠の形でしか運べない() -> None:
    """AI の言葉は根拠にならない——引用の空な根拠は `Evidence` が拒む。"""
    assert get_type_hints(Quote)["evidence"] is Evidence
    with pytest.raises(ValidationError):
        Quote(evidence=Evidence(quote="", source=源))


def test_作ったあと書き換えられない() -> None:
    材料 = Material(text="8月分の請求は42件")
    with pytest.raises(ValidationError):
        材料.text = "書き換え"  # type: ignore[misc]
