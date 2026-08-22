"""受け入れ基準の壊しかた。設計/仕事とは何か.md §3・§4。

**①は機械が見る語、②は人と AI が読む文。**
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.calendar.period import Period
from domain.rule.criteria import AcceptanceCriteria


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    語 = ("2026-08 の請求書",)
    assert AcceptanceCriteria(required_terms=語) == AcceptanceCriteria(required_terms=語)
    鍵 = AcceptanceCriteria(required_terms=語)
    assert {鍵: "版1"}[AcceptanceCriteria(required_terms=語)] == "版1"


def test_必ず含む語が空なら作れない() -> None:
    with pytest.raises(ValidationError):
        AcceptanceCriteria(required_terms=())


def test_必ず含む語が1つでもあれば作れる() -> None:
    基準 = AcceptanceCriteria(required_terms=("請求書",), description="先月分の請求が出ていること")
    assert 基準.required_terms == ("請求書",)
    assert 基準.description == "先月分の請求が出ていること"


def test_説明の文は空でもよい() -> None:
    assert AcceptanceCriteria(required_terms=("請求書",)).description == ""


def test_開かれていない波括弧が残っていることを言える() -> None:
    assert not AcceptanceCriteria(required_terms=("{対象期間} の請求書",)).opened


def test_穴の無い語ははじめから開いている() -> None:
    assert AcceptanceCriteria(required_terms=("請求書",)).opened


def test_対象期間で開くと固定の文字列になる() -> None:
    基準 = AcceptanceCriteria(required_terms=("{対象期間} の請求書",))
    開いた = 基準.expand(Period(text="2026-08"))
    assert 開いた.required_terms == ("2026-08 の請求書",)
    assert 開いた.opened


def test_週の対象期間でも開く() -> None:
    基準 = AcceptanceCriteria(required_terms=("{対象期間} の当番表",))
    assert 基準.expand(Period(text="2026-W34")).required_terms == ("2026-W34 の当番表",)


def test_すべての語で開く() -> None:
    基準 = AcceptanceCriteria(required_terms=("{対象期間} の請求書", "{対象期間} の明細", "合計"))
    assert 基準.expand(Period(text="2026-08")).required_terms == (
        "2026-08 の請求書",
        "2026-08 の明細",
        "合計",
    )


def test_説明の文はそのまま写る() -> None:
    基準 = AcceptanceCriteria(required_terms=("{対象期間} の請求書",), description="毎月の請求")
    assert 基準.expand(Period(text="2026-08")).description == "毎月の請求"


def test_開いても元の受け入れ基準は変わらない() -> None:
    基準 = AcceptanceCriteria(required_terms=("{対象期間} の請求書",))
    基準.expand(Period(text="2026-08"))
    assert 基準.required_terms == ("{対象期間} の請求書",)
    assert not 基準.opened
