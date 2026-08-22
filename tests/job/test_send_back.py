"""差し戻しの壊しかた。設計/仕事とは何か.md §3・§7・I7。

**理由が空でない。** 理由なしで作れたら赤。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.job.send_back import SendBack


def test_理由を持つ差し戻しは作れる() -> None:
    差し戻し = SendBack(reason="件数が源と合っていません。8月分をもう一度数えてください")
    assert 差し戻し.reason == "件数が源と合っていません。8月分をもう一度数えてください"


def test_理由の無い差し戻しは作れない() -> None:
    with pytest.raises(ValidationError):
        SendBack()  # type: ignore[call-arg]


def test_理由の空な差し戻しは作れない() -> None:
    for text in ("", "   ", "\n\t", "　"):
        with pytest.raises(ValidationError):
            SendBack(reason=text)


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        SendBack(reason="件数が合っていません", urgent=True)  # type: ignore[call-arg]


def test_決めたあと書き換えられない() -> None:
    差し戻し = SendBack(reason="件数が合っていません")
    with pytest.raises(ValidationError):
        差し戻し.reason = "やっぱりよい"  # type: ignore[misc]
