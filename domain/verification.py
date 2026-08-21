"""検証の2層 — チェック（機械・止める）とレビュー（AI・差し戻す）。

規則の三分解でいう**仕様**（これは合格か）。仕様はドメインの部品なので、
判定そのものもここに置く——型だけドメイン、規則はアプリ、に割らない。
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

_frozen = ConfigDict(frozen=True, extra="forbid")


class Passed(BaseModel):
    """通った — 検証を通過した結果"""

    model_config = _frozen
    kind: Literal["Passed"] = "Passed"


class Blocked(BaseModel):
    """止めた — チェックが止めた。理由つき。チェックだけが持つ力"""

    model_config = _frozen
    kind: Literal["Blocked"] = "Blocked"
    reason: str


class Returned(BaseModel):
    """差し戻した — レビューが差し戻した。理由つき。レビューに止める力は無い"""

    model_config = _frozen
    kind: Literal["Returned"] = "Returned"
    reason: str


CheckResult = Annotated[Union[Passed, Blocked], Field(discriminator="kind")]
"""チェックの結果 — 決定的。止める力を持つ。差し戻しは無い"""

ReviewResult = Annotated[Union[Passed, Returned], Field(discriminator="kind")]
"""レビューの結果 — 差し戻せる。止める力は無い"""


def check(body: str, must_contain: tuple[str, ...]) -> CheckResult:
    """チェックする — 成果物が受け入れ基準の決定的な部分を満たすか、機械で確かめる。

    白黒つくものだけを見る（止める力を持つ）。曖昧なところはレビューの仕事。
    """
    if not body.strip():
        return Blocked(reason="成果物が空")
    missing = [word for word in must_contain if word not in body]
    if missing:
        return Blocked(reason=f"必ず含む語が無い: {'、'.join(missing)}")
    return Passed()
