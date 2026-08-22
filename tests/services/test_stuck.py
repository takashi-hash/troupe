"""行き詰まりの壊しかた。設計/仕事が回る筋道.md §2「仕様」。

線は実装が決めた——①直近2回の止まった理由が同じなら真。
②前に出した成果が無いまま3回以上やり直したなら真。それ以外は偽。
"""

from __future__ import annotations

from domain.services.stuck import is_stuck


def test_直近2回が同じ理由なら真() -> None:
    assert is_stuck("先週の一覧", ["源が読めない", "源が読めない"], retried=1)


def test_間に別の理由を挟んでも直近2回が同じなら真() -> None:
    assert is_stuck(None, ["語が欠けた", "源が読めない", "源が読めない"], retried=2)


def test_直近2回が違う理由なら偽() -> None:
    assert not is_stuck("先週の一覧", ["源が読めない", "語が欠けた"], retried=2)


def test_理由が1つだけでは偽() -> None:
    assert not is_stuck("先週の一覧", ["源が読めない"], retried=1)


def test_成果が無いまま3回やり直したら真() -> None:
    assert not is_stuck(None, [], retried=2)
    assert is_stuck(None, [], retried=3)


def test_成果があれば理由が散っている限り偽() -> None:
    """事実の照合だけ——同じ材料なら何度でも同じ答え。"""
    材料 = ("先週の一覧", ["a", "b", "c"], 10)
    assert is_stuck(*材料) == is_stuck(*材料) == False  # noqa: E712
