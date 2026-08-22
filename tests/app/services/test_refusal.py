"""断りの壊しかた。設計/人に見えるもの.md §3——操作の失敗はエラーではない。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.refusal import Refusal


def test_理由の無い断りは作れない() -> None:
    with pytest.raises(ValidationError):
        Refusal(reason="")


def test_断りは理由を運ぶ() -> None:
    assert Refusal(reason="担当ではありません").reason == "担当ではありません"
