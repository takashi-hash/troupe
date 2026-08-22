"""差し戻されたの壊しかた。設計/仕事が回る筋道.md §5——人が主語。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.sent_back import SentBack
from domain.values.people.human import Human

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
座長 = Human(name="座長")


def test_差し戻されたは理由を残し誰がは共通のbyが持つ() -> None:
    出来事 = SentBack(at=いま, by=座長, reason="対象期間の数字が古い")
    assert set(SentBack.model_fields) == {"at", "by", "reason"}
    assert 出来事.by == 座長 and 出来事.reason == "対象期間の数字が古い"


def test_理由が空では差し戻せない() -> None:
    with pytest.raises(ValidationError, match="差し戻しの理由"):
        SentBack(at=いま, by=座長, reason="")
    with pytest.raises(ValidationError, match="差し戻しの理由"):
        SentBack(at=いま, by=座長, reason="   ")
