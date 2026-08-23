"""語の橋の壊しかた。設計/人に見えるもの.md §3・§5。

**橋は1枚**——画面ごとに言い換えを持たない。
そのうえで写しが2つある（用語集と状態の語）。写しである以上ずれうるので、
どちらも突合が正本と1行ずつ照合する:

- `GLOSS` ↔ 設計/仕事とは何か.md §2 の用語集（**設計が正本**）
- `STATE_GLOSS` ↔ domain の `STATE_WORDS`（**domain が正本**。画面は domain を知らない）
"""

from __future__ import annotations

import pathlib
import re

from domain.aggregates.job.life import STATE_WORDS
from domain.events.event import EVENT_WORDS
from domain.value_objects.people.actor import ACTOR_WORDS
from ui.words import (
    ACTION_WORDS,
    ACTOR_GLOSS,
    EVENT_GLOSS,
    GLOSS,
    STATE_GLOSS,
    TEXT_FIELDS,
    出来事,
    操作,
    状態,
    起こす者,
    語,
    読める,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def _用語集() -> dict[str, str]:
    """設計 §2 の表から「語 → 識別子」を読む。**正本はここ。**"""
    doc = (ROOT / "設計" / "仕事とは何か.md").read_text(encoding="utf-8")
    body = doc.split("## 2. 語", 1)[1].split("## 3.", 1)[0]
    出た: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"\|\s*\*{0,2}(.+?)\*{0,2}\s*\|.*\|\s*`([A-Za-z_]+)`\s*\|\s*$", line.strip())
        if m and m.group(1) != "語":
            出た[m.group(1)] = m.group(2)
    assert 出た, "設計から用語集が1行も読めませんでした"
    return 出た


def test_語の橋が用語集と1行ずつ一致する() -> None:
    """**正本は設計。** 語を足しても消しても改名しても、写し忘れたらここが赤くなる。"""
    assert GLOSS == _用語集()


def test_状態の語の写しがdomainと1行ずつ一致する() -> None:
    """**正本は domain。** 画面は domain を import できないので写しが要る。"""
    assert STATE_GLOSS == STATE_WORDS


def test_書く欄が要る操作は操作の語に載っている() -> None:
    """欄だけあって語が無い操作は、画面に出しようがない。"""
    assert set(TEXT_FIELDS) <= set(ACTION_WORDS)


# --- 識別子の側から読める形にする。**訳は作らない** ---


def test_識別子は切れ目で割れて頭が大きくなるだけ() -> None:
    assert 読める("send_back") == "Send back"
    assert 読める("AwaitingApproval") == "Awaiting approval"
    assert 読める("approve") == "Approve"
    assert 読める("RecheckDate") == "Recheck date"


def test_用語集の語は識別子の側から読める() -> None:
    assert 語("成果") == "Result"
    assert 語("根拠") == "Evidence"
    assert 語("やること") == "Instruction"
    assert 状態("承認待ち") == "Awaiting approval"
    assert 操作("send_back") == "Send back"


def test_橋に無い語は出せない() -> None:
    """**訳をその場で発明させない。** 足したければ、まず用語集に行を足す。"""
    try:
        語("そんな語は無い")
    except KeyError:
        return
    raise AssertionError("橋に無い語が出てしまいました")


def test_橋に無い状態は語をそのまま出す() -> None:
    """状態は帳簿から来る——古い帳簿の語を、無い訳で塗りつぶさない。"""
    assert 状態("見たことのない状態") == "見たことのない状態"


def test_出来事の語の写しがdomainと1行ずつ一致する() -> None:
    """**正本は domain。** 出来事を足して写し忘れたらここが赤くなる。"""
    assert EVENT_GLOSS == EVENT_WORDS


def test_起こす者の語の写しがdomainと1行ずつ一致する() -> None:
    assert ACTOR_GLOSS == ACTOR_WORDS


def test_出来事は識別子の側から読める() -> None:
    assert 出来事("下書きが配達された") == "Draft delivered"
    assert 起こす者("時計") == "Clock"
