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
from app.services.refusal import Refusal, reason_of
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


#: 周期の語 — 画面に出るのは用語集の語（週・月）、値が持つのは識別子。橋はここ。
_周期の語 = {"週": "weekly", "月": "monthly"}

#: 数の欄の識別子 → 用語集の語。断りは画面に出るので、語で言う。
_欄の語 = {
    "days": "終えるまでの日数",
    "budget_calls": "使用上限（回数）",
    "budget_seconds": "使用上限（秒）",
    "max_retries": "やり直しの上限",
}


def form_from_fields(fields: dict[str, str]) -> VersionForm:
    """欄の文字から版の欄を組む。数に読めない欄は ValueError——断りに変えるのは呼び手。

    **画面から渡るのは文字だけ**（設計 §1）——数に読むのも、周期の語を
    識別子に写すのも、値に組む側（ここ）の仕事。版を積むと頼むが同じ欄を使う。
    """

    def 数(名前: str) -> int | None:
        if 名前 not in fields:
            return None
        try:
            return int(fields[名前])
        except ValueError:
            語 = _欄の語.get(名前, 名前)
            raise ValueError(f"数に読めません: {語}（{fields[名前]}）") from None

    cycle = fields.get("cycle")
    return VersionForm(
        instruction=fields.get("instruction"),
        source=fields.get("source"),
        required_terms=(
            tuple(t.strip() for t in fields["required_terms"].split("、") if t.strip())
            if "required_terms" in fields
            else None
        ),
        description=fields.get("description"),
        cycle=_周期の語.get(cycle, cycle) if cycle is not None else None,
        days=数("days"),
        budget_calls=数("budget_calls"),
        budget_seconds=数("budget_seconds"),
        owner=fields.get("owner"),
        max_retries=数("max_retries"),
    )


def add_version_from_fields(
    rules: RuleRepository,
    topics: TopicPort,
    clock: ClockPort,
    name: str,
    by: str,
    fields: dict[str, str],
) -> Refusal | None:
    """欄の文字から版の欄を組んで積む。数に読めない欄は断りに変える——エラーは投げない。"""
    try:
        form = form_from_fields(fields)
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    return add_version(rules, topics, clock, name, by, form)


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
        return Refusal(reason=reason_of(なぜ))
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
        return Refusal(reason=reason_of(なぜ))
    rules.save(next_rule, (event,))
    return None
