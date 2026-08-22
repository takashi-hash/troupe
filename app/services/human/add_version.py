"""版を積む — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・§4。
| 版を積む | `add_version` | **題材のデータを初期値として読み、人が上書きした値**で版を積む |
| `TopicPort` | Port | 題材のデータ（版の中身）を読む | **app** | adapters | `add_version` |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
題材のデータが初期値、人が書いた欄がそれを上書きする。題材に無ければ人がぜんぶ書く。
版の番号は最後の版＋1しかありえない（I2）——数えるだけで、判断ではない。
業務の判断はしない。義務が拒んだら**断りに変えるだけ**。
"""

from __future__ import annotations


from app.dto.version_form import VersionForm
from app.ports.clock_port import ClockPort
from app.ports.topic_port import TopicPort
from app.services.refusal import Refusal
from domain.aggregates.rule import add_version as 版積み
from domain.repositories.rule_repository import RuleRepository
from domain.value_objects.people.human import Human
from domain.value_objects.rule.copied import Copied
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.source import Source
from domain.value_objects.rule.version import Version
from domain.value_objects.people.owner import Owner
from domain.value_objects.calendar.cycle import Cycle


def copied_from(form: VersionForm, base: Copied | None) -> Copied:
    """人が書いた欄と題材の初期値から、写しものを組む。

    **欄ごとの上書き**——書いた欄だけが初期値に勝つ。どちらにも無ければ
    「欄が足りません」で断られる（値は黙って発明しない）。
    """

    def 要る(名前: str, 書いた: object | None, 初期: object | None) -> object:
        if 書いた is not None:
            return 書いた
        if 初期 is not None:
            return 初期
        raise ValueError(f"欄が足りません: {名前}")

    terms = form.required_terms if form.required_terms is not None else (
        base.criteria.required_terms if base else None
    )
    if terms is None:
        raise ValueError("欄が足りません: 受け入れ基準の必ず含む語")
    desc = form.description if form.description is not None else (
        base.criteria.description if base else ""
    )
    return Copied(
        instruction=Instruction(text=str(要る("やること", form.instruction, base.instruction.text if base else None))),
        criteria=AcceptanceCriteria(required_terms=terms, description=desc),
        cycle=Cycle(str(要る("周期", form.cycle, base.cycle.value if base else None))),
        owner=Owner(person=Human(name=str(要る("受け持ちの人", form.owner, base.owner.person.name if base else None)))),
        budget=Budget(
            calls=int(str(要る("使用上限の回数", form.budget_calls, base.budget.calls if base else None))),
            seconds=int(str(要る("使用上限の秒", form.budget_seconds, base.budget.seconds if base else None))),
        ),
        source=Source(location=str(要る("源", form.source, base.source.location if base else None))),
        max_retries=int(str(要る("やり直しの上限", form.max_retries, base.max_retries if base else None))),
        days=int(str(要る("終えるまでの日数", form.days, base.days if base else None))),
    )


def add_version(
    rules: RuleRepository,
    topics: TopicPort,
    clock: ClockPort,
    name: str,
    by: str,
    form: VersionForm,
) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——版の列に傷をつけない。

    **画面から渡るのは文字だけ**（設計 §1）——ui は domain を知らないので、
    値に組むのはここ。題材のデータが初期値、人が書いた欄が上書き。
    """
    try:
        鍵, 人 = RuleName(text=name), Human(name=by)
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    base = topics.read(鍵)
    rule = rules.load(鍵)
    last = 0 if rule is None else rule.versions[-1].number
    try:
        copied = copied_from(form, base)
        version = Version(
            number=last + 1,
            instruction=copied.instruction,
            criteria=copied.criteria,
            cycle=copied.cycle,
            days=copied.days,
            budget=copied.budget,
            owner=copied.owner,
            source=copied.source,
            max_retries=copied.max_retries,
        )
        next_rule, event = 版積み.add_version(rule, 鍵, version, by=人, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    rules.save(next_rule, (event,))
    return None
