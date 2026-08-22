"""作成元の壊しかた。設計/仕事とは何か.md §3・不変条件 I3。

**二度作らない鍵。** 同じ中身なら同じ鍵の文字列、違う中身なら違う鍵。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.calendar.period import Period
from domain.values.job.origin import Origin
from domain.values.rule.rule_name import RuleName

月次 = RuleName(text="月次突合")
八月 = Period(text="2026-08")


def test_依頼発の作成元は作れる() -> None:
    assert Origin.from_request("REQ-0001").key != ""


def test_業務ルール発の作成元は作れる() -> None:
    assert Origin.from_rule(月次, 1, 八月).key != ""


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    一つ目 = Origin.from_rule(月次, 1, 八月)
    二つ目 = Origin.from_rule(月次, 1, 八月)
    assert 一つ目 == 二つ目
    assert {一つ目: "八月の一件"}[二つ目] == "八月の一件"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        Origin.from_request("REQ-0001").key = "REQ-0002"  # type: ignore[misc]


def test_空の鍵では作れない() -> None:
    for text in ("", "   "):
        with pytest.raises(ValidationError):
            Origin(key=text)


def test_空の依頼の識別子では作れない() -> None:
    # 作りかたが先に断るので `ValueError`。`ValidationError` もその一種。
    for text in ("", "   "):
        with pytest.raises(ValueError):
            Origin.from_request(text)


def test_同じ依頼の識別子なら同じ鍵を出す() -> None:
    assert Origin.from_request("REQ-0001").key == Origin.from_request("REQ-0001").key


def test_同じ業務ルールと版と対象期間なら同じ鍵を出す() -> None:
    assert Origin.from_rule(月次, 1, 八月).key == Origin.from_rule(月次, 1, 八月).key


def test_版が違えば鍵も違う() -> None:
    assert Origin.from_rule(月次, 1, 八月).key != Origin.from_rule(月次, 2, 八月).key


def test_対象期間が違えば鍵も違う() -> None:
    assert Origin.from_rule(月次, 1, 八月).key != Origin.from_rule(月次, 1, Period(text="2026-09")).key


def test_業務ルールが違えば鍵も違う() -> None:
    assert Origin.from_rule(月次, 1, 八月).key != Origin.from_rule(RuleName(text="週次突合"), 1, 八月).key


def test_依頼の識別子が違えば鍵も違う() -> None:
    assert Origin.from_request("REQ-0001").key != Origin.from_request("REQ-0002").key


def test_依頼発と業務ルール発は同じ鍵にならない() -> None:
    ルール発 = Origin.from_rule(月次, 1, 八月)
    assert Origin.from_request(ルール発.key) != ルール発
