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


def test_検証エラーは義務の文言だけになる_機械の中身は画面に出さない() -> None:
    from pydantic import ValidationError

    from app.services.refusal import reason_of
    from domain.value_objects.job.request import Request

    try:
        Request.model_validate({"by": {"name": "座長"}, "at": "2026-08-22T09:00:00+00:00", "body": ""})
        raise AssertionError("空の中身が通ってはいけない")
    except ValidationError as なぜ:
        文 = reason_of(なぜ)
    assert 文 == "依頼の中身が空です"
    assert "pydantic" not in 文 and "input_value" not in 文


def test_ふつうのValueErrorはそのまま() -> None:
    from app.services.refusal import reason_of

    assert reason_of(ValueError("欄が足りません: 源")) == "欄が足りません: 源"
