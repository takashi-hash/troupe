"""検索の読みの壊しかた。設計/仕事が回る筋道.md §4——終わったものも含めて（F1）。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from app.ports.search_reader import SearchHit, SearchReader


def _材料() -> SearchHit:
    return SearchHit(
        id="J-0001",
        rule="週次の依存の棚卸し",
        period="2026-W34",
        instruction="依存の一覧を突き合わせる",
        state_name="Finished",
        due="2026-08-20T09:00:00+00:00",
        assignee_name=None,
    )


def test_条件は4欄で_どれも文字() -> None:
    """キーワード・状態（識別子に写してから）・業務ルール・担当。空は絞らない。"""
    params = inspect.signature(SearchReader.read).parameters
    assert list(params) == ["self", "keyword", "state_name", "rule", "assignee"]
    hints = get_type_hints(SearchReader.read)
    for name in ("keyword", "state_name", "rule", "assignee"):
        assert hints[name] == str | None
    assert hints["return"] == tuple[SearchHit, ...]


def test_欄は検索の行の材料だけ() -> None:
    assert set(SearchHit.model_fields) == {
        "id", "rule", "period", "instruction", "state_name", "due", "assignee_name",
    }


def test_文字とIDだけで_domainの値は出ない() -> None:
    for name, field in SearchHit.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _材料().state_name = "Ready"  # type: ignore[misc]
