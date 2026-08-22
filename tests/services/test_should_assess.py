"""見立てを書くべきかの壊しかた。設計/仕事が回る筋道.md §2「仕様」・I15・F6。"""

from __future__ import annotations

from domain.services.should_assess import should_assess
from domain.values.job.assessment import Assessment
from domain.values.job.spent import Spent
from domain.values.rule.budget import Budget

上限 = Budget(calls=20, seconds=600)
見立て = Assessment(
    finding="20回とも同じ理由で落ちた", reason="源の在りかが変わった可能性が高い"
)


def test_上限に触れたら必ず真() -> None:
    """I15——回数でも秒でも、触れたら見立てが要る。"""
    assert should_assess((), (), Spent(calls=20, seconds=0), 上限, 0, 20) is True
    assert should_assess((), (), Spent(calls=0, seconds=600), 上限, 0, 20) is True


def test_やり直しが尽きたら必ず真() -> None:
    assert should_assess((), (), Spent(calls=0, seconds=0), 上限, 20, 20) is True


def test_書いたら偽() -> None:
    """F6——同じ見立てを二度書かない。書かれてはじめて I15 が満ちる。"""
    assert should_assess((見立て,), (), Spent(calls=20, seconds=0), 上限, 0, 20) is False
    assert should_assess((見立て,), (), Spent(calls=0, seconds=0), 上限, 20, 20) is False


def test_落ちた中身があれば真_書いたら偽() -> None:
    止まった理由 = ("必ず含む語がありません: 2026-W34",)
    assert should_assess((), 止まった理由, Spent(calls=3, seconds=60), 上限, 1, 20) is True
    assert should_assess((見立て,), 止まった理由, Spent(calls=3, seconds=60), 上限, 1, 20) is False


def test_材料が無ければ偽() -> None:
    """数字しか無いところに見立ては書けない。"""
    assert should_assess((), (), Spent(calls=3, seconds=60), 上限, 1, 20) is False
