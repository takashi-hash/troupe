"""署名して訪問を終えるの壊しかた。筋道 §1——空の記録に署名はできない。

下書きの識別子は運ばない——使われたかは (患者, 訪問日) が結ぶ記録の存在から導出。
"""

from __future__ import annotations

from app.services.human.sign_note import sign_note


class 訪問の終わりの偽物:
    def __init__(self, なぜ: str | None = None) -> None:
        self.署名: list[tuple[object, ...]] = []
        self._なぜ = なぜ

    def sign(self, visit_id: str, signer: str, s: str, o: str, a: str, p: str) -> str | None:
        if self._なぜ:
            return self._なぜ
        self.署名.append((visit_id, signer, s, o, a, p))
        return None

    def cancel(self, visit_id: str, reason: str, by: str) -> str | None:
        return None


def test_通れば署名が届く() -> None:
    口 = 訪問の終わりの偽物()
    assert sign_note(口, "7", "Dr-A", "s", "o", "a", "p", by="Dr-A") is None
    assert 口.署名 == [("7", "Dr-A", "s", "o", "a", "p")]


def test_SOAPのどれかが空なら断り() -> None:
    口 = 訪問の終わりの偽物()
    断り = sign_note(口, "7", "Dr-A", "s", " ", "a", "p", by="Dr-A")
    assert 断り is not None and "O is empty" in 断り.reason
    assert 口.署名 == []


def test_署名者が空なら断り() -> None:
    assert sign_note(訪問の終わりの偽物(), "7", " ", "s", "o", "a", "p", by="Dr-A") is not None


def test_署名者は押した席そのもの_別名は断り() -> None:
    """筋道 §1——席と署名者が別れる道は無い。"""
    断り = sign_note(訪問の終わりの偽物(), "7", "Dr-B", "s", "o", "a", "p", by="Dr-A")
    assert 断り is not None and "seat" in 断り.reason


def test_診療録の断りは理由ごと届く() -> None:
    断り = sign_note(訪問の終わりの偽物(なぜ="既に署名済みです"), "7", "Dr-A", "s", "o", "a", "p", by="Dr-A")
    assert 断り is not None and 断り.reason == "既に署名済みです"
