"""操作の語と状態の語の橋の壊しかた。設計/人に見えるもの.md §3・§5。

**橋は1枚**——画面ごとに言い換えを持たない。
状態の語の写し（`STATE_GLOSS`）は domain の `STATE_WORDS` と1行ずつ照合する。
**画面は domain を知らない**（依存の契約）ので写しが要るが、
写しである以上ずれうる。だからここが突合になる。
"""

from __future__ import annotations

from domain.aggregates.job.life import STATE_WORDS
from ui.words import ACTION_WORDS, STATE_GLOSS, TEXT_FIELDS, 併記


def test_状態の語の写しが用語集と1行ずつ一致する() -> None:
    """**正本は domain。** 語を増やしても減らしても、写し忘れたらここが赤くなる。"""
    assert STATE_GLOSS == STATE_WORDS


def test_書く欄が要る操作は操作の語に載っている() -> None:
    """欄だけあって語が無い操作は、画面に出しようがない。"""
    assert set(TEXT_FIELDS) <= set(ACTION_WORDS)


def test_併記は用語集の識別子をそのまま出す() -> None:
    assert 併記(ACTION_WORDS["approve"], "approve") == "承認する（approve）"
    assert 併記("承認待ち", STATE_GLOSS["承認待ち"]) == "承認待ち（AwaitingApproval）"


def test_橋が無い語は語だけを出す() -> None:
    """**無い訳をここで発明しない。** 用語集に載っていないものは、載っていないと出す。"""
    assert 併記("なにか", None) == "なにか"
