"""見立ての壊しかた。設計/仕事とは何か.md §3・公理「判断は人間」。

**見立てが無いと AI は数字しか出せない。**
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.job.assessment import Assessment


def test_読んだ結果と理由を両方持つ見立ては作れる() -> None:
    見立て = Assessment(
        finding="20回とも同じ理由で落ちました",
        reason="源の在りかが変わった可能性が高い",
    )
    assert 見立て.finding == "20回とも同じ理由で落ちました"
    assert 見立て.reason == "源の在りかが変わった可能性が高い"


def test_理由の無い見立ては作れない() -> None:
    with pytest.raises(ValidationError):
        Assessment(finding="20回とも同じ理由で落ちました")  # type: ignore[call-arg]


def test_理由が空な見立ては作れない() -> None:
    for text in ("", "   ", "\n\t"):
        with pytest.raises(ValidationError):
            Assessment(finding="20回とも同じ理由で落ちました", reason=text)


def test_読んだ結果の無い見立ては作れない() -> None:
    with pytest.raises(ValidationError):
        Assessment(reason="源の在りかが変わった可能性が高い")  # type: ignore[call-arg]


def test_読んだ結果が空な見立ては作れない() -> None:
    for text in ("", "   ", "\n\t"):
        with pytest.raises(ValidationError):
            Assessment(finding=text, reason="源の在りかが変わった可能性が高い")


def test_作ったあと書き換えられない() -> None:
    見立て = Assessment(finding="20回とも同じ理由で落ちました", reason="源の在りかが変わった")
    with pytest.raises(ValidationError):
        見立て.reason = "別の理由"  # type: ignore[misc]
