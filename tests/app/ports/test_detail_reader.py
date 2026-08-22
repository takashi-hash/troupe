"""詳細の読みの壊しかた。設計/仕事が回る筋道.md §4・人に見えるもの.md §2——文字と ID だけ。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from app.ports.detail_reader import DetailMaterial, DetailReader
from domain.value_objects.job.job_id import JobId


def _材料() -> DetailMaterial:
    return DetailMaterial(
        events=(("2026-08-18 09:02", "human", "座長", "Approved"),),
        questions=(("どの源ですか", "8月分の置き場です"), ("締めはいつですか", None)),
    )


def test_読みは鍵で1件の詳細() -> None:
    hints = get_type_hints(DetailReader.read)
    assert hints["id"] is JobId
    assert hints["return"] is DetailMaterial
    assert list(inspect.signature(DetailReader.read).parameters) == ["self", "id"]


def test_欄は設計の2つだけ() -> None:
    """出来事の列と問答の対の全列。成果・根拠・見立ては今日の材料が運ぶ——運び手は1本。"""
    assert set(DetailMaterial.model_fields) == {"events", "questions"}


def test_文字とIDだけで_domainの値は出ない() -> None:
    hints = get_type_hints(DetailMaterial)
    assert hints["events"] == tuple[tuple[str, str, str | None, str], ...]
    assert hints["questions"] == tuple[tuple[str, str | None], ...]


def test_答えの無い質問も本文のまま届く() -> None:
    材料 = _材料()
    assert 材料.questions[1] == ("締めはいつですか", None)


def test_作ったあと書き換えられない() -> None:
    材料 = _材料()
    with pytest.raises(ValidationError):
        材料.questions = ()  # type: ignore[misc]


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert _材料() == _材料()
    assert {_材料(): "詳細"}[_材料()] == "詳細"
