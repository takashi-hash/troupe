"""業務ルールの集約が持つ値。

設計: 設計/仕事とは何か.md §2「決まり」・§3。

**版が決めるもの。** 仕事はここから写す——指すのではない。
だから業務ルールは仕事を知らない（import-linter が守る）。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.shared import Cycle, Owner, Period, Value, not_blank


class RuleName(Value):
    """業務ルールの識別子 — 一意。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.text, "業務ルールの識別子")
        return self


class Instruction(Value):
    """やること — その仕事で何をするのか。AI が読む指示。

    版が「やること」を持つのが要。持たないと AI は何をすればよいか永久に知れない。
    """

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.text, "やること")
        return self


#: 受け入れ基準の必ず含む語に書ける差し込み。写すときに `Period` で開く。
PERIOD_SLOT = "{対象期間}"


class AcceptanceCriteria(Value):
    """受け入れ基準 — 何をもって成果とするか。

    2つに分かれる。
      ① 必ず含む語の列（空でない。**機械が見る**）
      ② 説明の文（**人と AI が読む**）
    ①に `{対象期間}` と書ける——写すときに `Period` で開くので、
    検査に届く時点では固定の文字列。
    """

    must_contain: tuple[str, ...]
    explanation: str = ""

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if not self.must_contain or any(not w.strip() for w in self.must_contain):
            raise ValueError("必ず含む語が空です")
        return self

    @property
    def opened(self) -> bool:
        """開かれていない差し込みが残っていないか。検査に届く前に真であること。"""
        return not any("{" in w for w in self.must_contain)

    def expand(self, period: Period) -> AcceptanceCriteria:
        """`{対象期間}` を `Period` で開く。仕事が版から写すときに1度だけ呼ぶ。"""
        return AcceptanceCriteria(
            must_contain=tuple(w.replace(PERIOD_SLOT, period.text) for w in self.must_contain),
            explanation=self.explanation,
        )


class Source(Value):
    """源 — 材料の在りか。AI が読みに行く先。"""

    locator: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.locator, "源の在りか")
        return self


class Budget(Value):
    """使用上限 — 使ってよい回数と時間。暴走を止める安全弁。"""

    calls: int
    seconds: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.calls < 1 or self.seconds < 1:
            raise ValueError("使用上限は回数も秒も1以上です")
        return self


class Version(Value):
    """版 — 業務ルールの1つの姿。積むだけ。減らせない・書き換えられない。"""

    number: int
    instruction: Instruction
    criteria: AcceptanceCriteria
    cycle: Cycle
    days: int
    budget: Budget
    owner: Owner
    source: Source
    max_retries: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.number < 1:
            raise ValueError("版の番号は1以上です")
        if self.days < 1:
            raise ValueError("終えるまでの日数は1以上です")
        if self.max_retries < 0:
            raise ValueError("やり直しの上限は0以上です")
        return self

    def copy_for(self, period: Period | None) -> Copied:
        """写すものの束を渡す。**版そのものは渡さない。**

        写すとき受け入れ基準の `{対象期間}` を開く。業務ルール発なら対象期間が在る。
        """
        return Copied(
            instruction=self.instruction,
            criteria=self.criteria.expand(period) if period else self.criteria,
            owner=self.owner,
            budget=self.budget,
            source=self.source,
            cycle=self.cycle,
            max_retries=self.max_retries,
            days=self.days,
        )


class Copied(Value):
    """写すものの束 — 版から仕事へ写す中身 ＋ 終えるまでの日数。

    日数は仕事が持たない——`DueDate` になって消える。
    """

    instruction: Instruction
    criteria: AcceptanceCriteria
    owner: Owner
    budget: Budget
    source: Source
    cycle: Cycle
    max_retries: int
    days: int
