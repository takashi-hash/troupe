"""業務ルール — 集約ルート。

設計: 設計/仕事とは何か.md §4「業務ルールが持つもの」・§7「禁止状態」・不変条件 I2・I7。

| 持ちもの | 決まり |
|---|---|
| `RuleName` | 同一性 |
| 版の列 | **積むだけ**。減らせない・書き換えられない |
| 有効な版の番号 | **0か1つ**。版2を有効にすると版1は自動で無効になる |
| 有効にした人と時刻 | 人だけが有効にできる（I7） |

**版が減った業務ルール**は禁止状態——番号が1から連番であることを義務にすると、
消した姿・飛ばした姿がそもそも書けない（I2 の型側。書き込みの門は前の版列と突き合わせる）。
有効にした人の欄の型が `Human` なので、AI が有効にした姿も書けない（I7）。

**操作は1操作1ファイル**で、この集約ルートを最初の引数に取り、
**（次の姿, 出来事）の対**を返す——出来事なしで姿を書く形が書けない。
"""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import model_validator

from domain.obligations import Value
from domain.values.people.human import Human
from domain.values.rule.rule_name import RuleName
from domain.values.rule.version import Version


class Rule(Value):
    """業務ルール — 繰り返しやる仕事の決まり。これが仕事を生む。同一性は `RuleName`。"""

    #: 業務ルールの識別子 — 同一性。版を積んでも変わらない。
    name: RuleName

    #: 版の列 — **積むだけ。** 空でない。番号は1から連番（I2 の型側）。
    versions: tuple[Version, ...]

    #: 有効な版の番号 — **0か1つ。** 在る版の番号だけ。
    active: int | None

    #: 有効にした人と時刻 — 人だけが有効にできる（I7）。有効なら3つ揃い、無効なら3つ空。
    activated_by: Human | None
    activated_at: datetime | None

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if not self.versions:
            raise ValueError("版の列が空です。版の無い業務ルールは存在できません")
        numbers = [v.number for v in self.versions]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("版の番号は1から連番です（I2: 版は積むだけ——消せない・飛ばせない）")
        activation = (self.active, self.activated_by, self.activated_at)
        if any(x is not None for x in activation) and not all(x is not None for x in activation):
            raise ValueError("有効なら番号・人・時刻の3つが揃い、無効なら3つとも空です")
        if self.active is not None and self.active not in numbers:
            raise ValueError("有効な版の番号は、在る版の番号だけです")
        return self


def fields_of(rule: Rule) -> dict[str, object]:
    """操作が次の姿を組むための、いまの持ちもの一式。

    操作はこれに変わる欄を上書きして `Rule.model_validate` する
    ——全義務が次の姿でも検証し直される。
    """
    return {name: getattr(rule, name) for name in Rule.model_fields}
