"""根拠の壊しかた。設計/仕事とは何か.md §3・I5。

**AI の言葉は根拠にならない。** 源から読んだ引用だけが根拠になる。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.job.evidence import Evidence
from domain.values.rule.source import Source


def test_源から読んだ引用は根拠になる() -> None:
    根拠 = Evidence(
        quote="2026-08分の請求書を3件受領しました",
        source=Source(location="mail/請求"),
    )
    assert 根拠.quote == "2026-08分の請求書を3件受領しました"
    assert 根拠.source == Source(location="mail/請求")


def test_引用の空な根拠は作れない() -> None:
    for text in ("", "   ", "\n\t"):
        with pytest.raises(ValidationError):
            Evidence(quote=text, source=Source(location="mail/請求"))


def test_源を持たない根拠は作れない() -> None:
    with pytest.raises(ValidationError):
        Evidence(quote="2026-08分の請求書を3件受領しました")  # type: ignore[call-arg]


def test_在りかの空な源からは根拠を作れない() -> None:
    with pytest.raises(ValidationError):
        Evidence(quote="2026-08分の請求書を3件受領しました", source=Source(location=""))


def test_素の文字列は源にならない() -> None:
    with pytest.raises(ValidationError):
        Evidence(quote="2026-08分の請求書を3件受領しました", source="mail/請求")  # type: ignore[arg-type]


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    根拠 = Evidence(quote="受領しました", source=Source(location="mail/請求"))
    同じ根拠 = Evidence(quote="受領しました", source=Source(location="mail/請求"))
    assert 根拠 == 同じ根拠
    assert {根拠: "終わった"}[同じ根拠] == "終わった"
