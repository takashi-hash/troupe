"""源の壊しかた。設計/仕事とは何か.md §3。

**在りかだけを持つ。** 読んだ中身は源が持たない。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.rule.source import Source


def test_AI_が読みに行く先を持つ() -> None:
    源 = Source(location="records/訪問記録/2026-08")
    assert 源.location == "records/訪問記録/2026-08"


def test_在りかの違う源は別の源() -> None:
    assert Source(location="records/2026-08") != Source(location="records/2026-07")


def test_在りかの空な源は作れない() -> None:
    for location in ("", "   ", "\n", "　"):
        with pytest.raises(ValidationError):
            Source(location=location)


def test_読んだ中身を持たせられない() -> None:
    with pytest.raises(ValidationError):
        Source(location="records/2026-08", 中身="訪問12件")  # type: ignore[call-arg]


def test_写したあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        Source(location="records/2026-08").location = "records/2026-07"  # type: ignore[misc]


def test_患者の穴は開ける_穴の無い源は開いても変わらない() -> None:
    """筋道 §1 create——穴は写すときに患者記号で開く。"""
    穴あき = Source(location="db:chart/{患者}")
    assert 穴あき.has_hole
    assert 穴あき.open_for("P-004") == Source(location="db:chart/P-004")
    assert not 穴あき.open_for("P-004").has_hole
    穴なし = Source(location="db:billing")
    assert not 穴なし.has_hole
    assert 穴なし.open_for("P-004") == 穴なし
