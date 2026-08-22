"""仕事 — 集約ルート。

設計: 設計/仕事とは何か.md §4「仕事が持つもの」・不変条件 I1・I3・I14。

**持ちものは状態ごとに書き分けない**——共通はここに1度だけ。
状態に足して持つもの（担当・承認…）は一生（life）の各状態が持つ。

**操作は1操作1ファイル**で、この集約ルートを最初の引数に取り、
**（次の姿, 出来事）の対**を返す——出来事なしで状態を書く形が書けない。
これが I1（状態が変わったら、理由のドメインイベントが必ず一緒に残る）の型。
帳簿の書き込みの門が、最終的に対のまま受け取って一緒に積む。

**引数の型が「から」、返りの型が「へ」。** `Ready` の仕事に承認を
渡す行は型検査が赤にする——行けない遷移は型が作らせない。
"""

from __future__ import annotations

from typing import Any, Generic, Self, TypeVar

from pydantic import model_validator

from domain.aggregates.job.life import (
    AwaitingApproval,
    Cleared,
    Finished,
    FinishedPendingRecheck,
    StateUnion,
    Submitted,
)
from domain.obligations import Value
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.origin import Origin
from domain.value_objects.job.spent import Spent
from domain.value_objects.people.owner import Owner
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source

S = TypeVar("S", bound=StateUnion)


class Job(Value, Generic[S]):
    """仕事 — 頼まれてから終わるまでの1件。同一性は `JobId`。"""

    #: 仕事の識別子 — 一意。あとから変えない。
    id: JobId

    #: 作成元 — 二度作らない鍵（I3）。
    origin: Origin

    #: 生まれた版 — 業務ルール発のみ。生成の時点で固定。あとで版が積まれても書き換えない。
    born_of: RuleName | None
    born_version: int | None

    #: 対象期間 — 業務ルール発のみ。
    period: Period | None

    #: 版から写したもの。**写すのであって、指すのではない。**
    instruction: Instruction
    criteria: AcceptanceCriteria
    owner: Owner
    budget: Budget
    source: Source
    cycle: Cycle
    max_retries: int

    #: 期日 — 起点の時刻 ＋ 版の日数。
    due: DueDate

    #: 使った量 — `Spent(calls=0, seconds=0)` で生まれる。
    spent: Spent

    #: やり直した回数 — 0 で生まれる。`Retried` が +1、`SentBack` が 0 に戻す。
    retried: int

    #: 成果の在りか・根拠の在りか — 出てから持つ（それまでは空）。
    result_at: str | None
    evidence_at: str | None

    #: いま居る状態 — 一生のどれか1つ。
    state: S

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        born = (self.born_of, self.born_version, self.period)
        if any(x is not None for x in born) and not all(x is not None for x in born):
            raise ValueError("生まれた版と対象期間は、業務ルール発なら三つ揃い、依頼発なら三つとも空です")
        if self.born_of is not None and self.born_version is not None and self.period is not None:
            if self.origin != Origin.from_rule(self.born_of, self.born_version, self.period):
                raise ValueError("作成元が生まれた版と食い違っています（I3 の鍵が嘘になる）")
        if not self.criteria.opened:
            raise ValueError(
                "開かれていない差し込みが残っています"
                "（業務ルール発は写すときに開く。依頼発の基準に差し込みは書けない——開く相手が居ない）"
            )
        if self.retried < 0:
            raise ValueError("やり直した回数は0以上です")
        if self.max_retries < 0:
            raise ValueError("やり直しの上限は0以上です")
        st = self.state
        if isinstance(st, (Submitted, AwaitingApproval, Cleared)) and self.result_at is None:
            raise ValueError(f"{type(st).__name__} は成果の在りかが空であってはいけません")
        if isinstance(st, Finished) and self.evidence_at is None:
            raise ValueError("終わったは根拠の在りかが空であってはいけません")
        if isinstance(st, FinishedPendingRecheck) and self.evidence_at is not None:
            raise ValueError("終わった（確かめ待ち）は根拠の在りかを持ってはいけません")
        return self


def fields_of(job: Job[Any]) -> dict[str, object]:
    """操作が次の姿を組むための、いまの持ちもの一式。

    操作はこれに `state`（と変わる欄）を上書きして `Job[次の状態].model_validate` する
    ——全義務が次の姿でも検証し直される。
    """
    return {name: getattr(job, name) for name in Job.model_fields}
