"""署名して訪問を終えるの壊しかた。筋道 §1——空の記録に署名はできない。"""

from __future__ import annotations

from app.services.human.sign_note import sign_note


class 訪問の終わりの偽物:
    def __init__(self, なぜ: str | None = None) -> None:
        self.署名: list[tuple[object, ...]] = []
        self._なぜ = なぜ

    def sign(self, visit_id: str, signer: str, s: str, o: str, a: str, p: str,
             draft_id: str | None) -> str | None:
        if self._なぜ:
            return self._なぜ
        self.署名.append((visit_id, signer, s, o, a, p, draft_id))
        return None

    def cancel(self, visit_id: str, reason: str) -> str | None:
        return None


def test_通れば署名が届く_下書きの識別子つき() -> None:
    口 = 訪問の終わりの偽物()
    assert sign_note(口, "7", "Dr-A", "s", "o", "a", "p", "3", by="Dr-A") is None
    assert 口.署名 == [("7", "Dr-A", "s", "o", "a", "p", "3")]


def test_下書きなしの白紙署名もできる() -> None:
    口 = 訪問の終わりの偽物()
    assert sign_note(口, "7", "Dr-A", "s", "o", "a", "p", "", by="Dr-A") is None
    assert 口.署名[0][6] is None  # 空文字は「使った下書きなし」


def test_SOAPのどれかが空なら断り() -> None:
    口 = 訪問の終わりの偽物()
    断り = sign_note(口, "7", "Dr-A", "s", " ", "a", "p", "", by="Dr-A")
    assert 断り is not None and "O" in 断り.reason
    assert 口.署名 == []


def test_署名者が空なら断り() -> None:
    assert sign_note(訪問の終わりの偽物(), "7", " ", "s", "o", "a", "p", "", by="Dr-A") is not None


def test_診療録の断りは理由ごと届く() -> None:
    断り = sign_note(訪問の終わりの偽物(なぜ="既に署名済みです"), "7", "Dr-A", "s", "o", "a", "p", "", by="Dr-A")
    assert 断り is not None and 断り.reason == "既に署名済みです"
