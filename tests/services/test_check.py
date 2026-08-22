"""検査の壊しかた。設計/仕事が回る筋道.md §2「仕様」。

**同じ成果なら何度でも同じ結果**——文字の照合だけ。
"""

from __future__ import annotations

import pytest

from domain.services.check import stop_reason
from domain.value_objects.calendar.period import Period
from domain.value_objects.rule.criteria import AcceptanceCriteria

基準 = AcceptanceCriteria(
    required_terms=("{対象期間}", "更新"), description="一覧の日付が今週のものである"
).expand(Period(text="2026-W34"))


def test_必ず含む語が全部あれば通る() -> None:
    assert stop_reason("2026-W34 の依存一覧。更新が3件。", 基準) is None


def test_語が欠けると理由つきで止まる() -> None:
    理由 = stop_reason("先週の一覧です。更新が3件。", 基準)
    assert 理由 is not None and "2026-W34" in 理由


def test_同じ成果なら何度でも同じ結果() -> None:
    成果 = "2026-W34 の依存一覧。更新が3件。"
    assert stop_reason(成果, 基準) == stop_reason(成果, 基準) == None  # noqa: E711


def test_開かれていない差し込みが検査に届いたら赤() -> None:
    生 = AcceptanceCriteria(required_terms=("{対象期間}",))
    with pytest.raises(ValueError, match="開かれていない"):
        stop_reason("なんでも", 生)
