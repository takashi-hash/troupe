"""AI の材料の読みの壊しかた。設計/仕事が回る筋道.md §4——二重の正本を作らない。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from app.ports.work_reader import WorkMaterial, WorkReader
from domain.values.job.assessment import Assessment
from domain.values.job.job_id import JobId


def _材料() -> WorkMaterial:
    return WorkMaterial(
        answered_questions=(("どの源ですか", "8月分の置き場です"),),
        previous_result="請求42件",
        fall_reasons=("源に接続できませんでした",),
        assessments=(Assessment(finding="源の在りかが変わった可能性", reason="同じ理由で2回落ちた"),),
        sibling_states=("実行中",),
    )


def test_読みは鍵で1件の材料() -> None:
    hints = get_type_hints(WorkReader.read)
    assert hints["id"] is JobId
    assert hints["return"] is WorkMaterial
    assert list(inspect.signature(WorkReader.read).parameters) == ["self", "id"]


def test_運ぶのは集約の外に在るものだけ() -> None:
    """やること・受け入れ基準・源・使った量と上限・確かめ期日は集約が持つ——ここに欄が無い。"""
    assert set(WorkMaterial.model_fields) == {
        "answered_questions",
        "previous_result",
        "fall_reasons",
        "assessments",
        "sibling_states",
    }


def test_見立ては値のまま運ぶ() -> None:
    assert get_type_hints(WorkMaterial)["assessments"] == tuple[Assessment, ...]


def test_前に出した成果は無いことがある() -> None:
    材料 = WorkMaterial(
        answered_questions=(),
        previous_result=None,
        fall_reasons=(),
        assessments=(),
        sibling_states=(),
    )
    assert 材料.previous_result is None


def test_作ったあと書き換えられない() -> None:
    材料 = _材料()
    with pytest.raises(ValidationError):
        材料.previous_result = "書き換え"  # type: ignore[misc]


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert _材料() == _材料()
    assert {_材料(): "材料"}[_材料()] == "材料"
