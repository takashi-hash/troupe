"""検めるの壊しかた。設計/仕事が回る筋道.md §2「仕様」・I16。

**名乗りを検めるのがここ**——成果と名乗っても語が欠ければ見立てへ。
"""

from __future__ import annotations

import pytest

from domain.services.verify_reply import verify
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.reply import Mark, Reply
from domain.value_objects.rule.criteria import AcceptanceCriteria

基準 = AcceptanceCriteria(
    required_terms=("{対象期間}", "更新"), description="一覧の日付が今週のものである"
).expand(Period(text="2026-W34"))


def test_印が質問なら質問へ() -> None:
    assert verify(Reply(mark=Mark.QUESTION, body="源の在りかはどこですか"), 基準) is Mark.QUESTION


def test_印が成果で_必ず含む語をすべて含めば成果へ() -> None:
    応答 = Reply(mark=Mark.RESULT, body="2026-W34 の依存一覧。更新が3件。")
    assert verify(応答, 基準) is Mark.RESULT


def test_印が成果でも_語が欠ければ見立てへ() -> None:
    """I16 の後半の実物——名乗りを鵜呑みにしない。"""
    応答 = Reply(mark=Mark.RESULT, body="先週の一覧です。更新が3件。")
    assert verify(応答, 基準) is Mark.NEITHER


def test_印がどちらでもないなら_語が揃っていても見立てへ() -> None:
    応答 = Reply(mark=Mark.NEITHER, body="2026-W34 の一覧。更新は読めたが確信がない。")
    assert verify(応答, 基準) is Mark.NEITHER


def test_同じ応答なら何度でも同じ印() -> None:
    応答 = Reply(mark=Mark.RESULT, body="2026-W34 の依存一覧。更新が3件。")
    assert verify(応答, 基準) is verify(応答, 基準)


def test_開かれていない差し込みが仕様に届いたら赤() -> None:
    生 = AcceptanceCriteria(required_terms=("{対象期間}",))
    with pytest.raises(ValueError, match="開かれていない"):
        verify(Reply(mark=Mark.QUESTION, body="なんでも"), 生)
