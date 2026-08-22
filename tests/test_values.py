"""値オブジェクトの壊しかた。

設計: 設計/仕事とは何か.md §3 の「壊しかた」の欄を、1行1テストで置く。
掟7 — 仕掛けは「壊して赤を見た」まで書いて完成。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from domain.values import (
    AcceptanceCriteria,
    Agent,
    Answer,
    Approval,
    Assessment,
    Budget,
    Clock,
    Cycle,
    DueDate,
    Evidence,
    Human,
    Instruction,
    JobId,
    Mark,
    Origin,
    Owner,
    Period,
    Question,
    RecheckDate,
    Reply,
    Request,
    Result,
    RuleName,
    SendBack,
    Source,
    Spent,
    Version,
)

T0 = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
ALICE = Human(name="座長")
OWNER = Owner(person=ALICE)
SRC = Source(locator="deps://prod")


def _version(**over: object) -> Version:
    base: dict[str, object] = dict(
        number=1,
        instruction=Instruction(text="依存の一覧を取り更新が来ているものを挙げる"),
        criteria=AcceptanceCriteria(must_contain=("{対象期間}",)),
        cycle=Cycle.WEEKLY,
        days=3,
        budget=Budget(calls=20, seconds=600),
        owner=OWNER,
        source=SRC,
        max_retries=20,
    )
    return Version(**(base | over))  # type: ignore[arg-type]


# ── 全部に共通の義務 ─────────────────────────────────────


def test_同じ中身なら等しい() -> None:
    assert JobId(text="j1") == JobId(text="j1")
    # frozen が基底クラスにあると pyright が __hash__ を見ない（実物は下で確かめる）
    assert {JobId(text="j1"): 1}[JobId(text="j1")] == 1  # pyright: ignore[reportUnhashable]
    assert hash(JobId(text="j1")) == hash(JobId(text="j1"))


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        JobId(text="j1").text = "j2"  # type: ignore[misc]


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        JobId(text="j1", extra="x")  # type: ignore[call-arg]


# ── 禁止値（設計 §7）────────────────────────────────────


def test_空の識別子と空の名前() -> None:
    for make in (
        lambda: JobId(text=""),
        lambda: RuleName(text=""),
        lambda: Human(name=""),
        lambda: Agent(name=" "),
    ):
        with pytest.raises(ValidationError):
            make()


def test_仕事の識別子は前後に空白を持てない() -> None:
    with pytest.raises(ValidationError):
        JobId(text=" j1 ")


def test_AI_を受け持ちの人にできない() -> None:
    with pytest.raises(ValidationError):
        Owner(person=Agent(name="一号"))  # type: ignore[arg-type]


def test_時計は担当になれない() -> None:
    """`Assignee` は人か AI のどちらか。3つ目は無い。"""
    from pydantic import TypeAdapter

    from domain.values import Assignee

    ta = TypeAdapter(Assignee)
    assert ta.validate_python(ALICE) == ALICE
    with pytest.raises(ValidationError):
        ta.validate_python(Clock())


def test_起こす者は素の文字列から作れない() -> None:
    from pydantic import TypeAdapter

    from domain.values import Actor

    ta = TypeAdapter(Actor)
    assert ta.validate_python(Clock()) == Clock()
    with pytest.raises(ValidationError):
        ta.validate_python("時計")


def test_ゼロや負の使用上限() -> None:
    for calls, seconds in ((0, 600), (20, 0), (-1, 600)):
        with pytest.raises(ValidationError):
            Budget(calls=calls, seconds=seconds)


def test_負の使った量() -> None:
    with pytest.raises(ValidationError):
        Spent(calls=-1, seconds=0)


def test_起点より前の期日() -> None:
    with pytest.raises(ValidationError):
        DueDate(start=T0, at=T0 - timedelta(days=1))
    with pytest.raises(ValidationError):
        DueDate(start=T0, at=T0)


def test_期日は起点の時刻と日数から組む() -> None:
    assert DueDate.from_start(T0, 3).at == T0 + timedelta(days=3)


def test_形の違う対象期間() -> None:
    for text in ("来月", "2026-13", "2026-W54", "2026/08", ""):
        with pytest.raises(ValidationError):
            Period(text=text)


def test_対象期間の形が周期を言う() -> None:
    assert Period(text="2026-08").cycle is Cycle.MONTHLY
    assert Period(text="2026-W34").cycle is Cycle.WEEKLY


def test_引用の空な根拠() -> None:
    with pytest.raises(ValidationError):
        Evidence(quote="", read_from=SRC)


def test_誰かいつが欠けた承認() -> None:
    with pytest.raises(ValidationError):
        Approval(by=ALICE)  # type: ignore[call-arg]


def test_理由の無い差し戻しと理由の無い見立て() -> None:
    with pytest.raises(ValidationError):
        SendBack(by=ALICE, at=T0, reason="")
    with pytest.raises(ValidationError):
        Assessment(finding="20回とも同じ理由", reason="", at=T0)


def test_やることの空な版() -> None:
    with pytest.raises(ValidationError):
        Instruction(text="")
    with pytest.raises(ValidationError):
        _version(number=0)
    with pytest.raises(ValidationError):
        _version(days=0)


def test_中身の空な成果と質問と回答と依頼と応答() -> None:
    with pytest.raises(ValidationError):
        Result(body="")
    with pytest.raises(ValidationError):
        Question(body="", to=OWNER)
    with pytest.raises(ValidationError):
        Answer(by=ALICE, at=T0, body="")
    with pytest.raises(ValidationError):
        Request(by=ALICE, at=T0, body="")
    with pytest.raises(ValidationError):
        Reply(mark=Mark.RESULT, body="")


def test_空の源() -> None:
    with pytest.raises(ValidationError):
        Source(locator="")


# ── 受け入れ基準（機械が見る側）──────────────────────────


def test_必ず含む語が空では作れない() -> None:
    with pytest.raises(ValidationError):
        AcceptanceCriteria(must_contain=())
    with pytest.raises(ValidationError):
        AcceptanceCriteria(must_contain=("",))


def test_対象期間の差し込みが写すときに開く() -> None:
    c = AcceptanceCriteria(must_contain=("{対象期間}", "更新"), explanation="今週の日付であること")
    assert not c.opened
    opened = c.expand(Period(text="2026-W34"))
    assert opened.must_contain == ("2026-W34", "更新")
    assert opened.opened
    assert opened.explanation == c.explanation


def test_開かれていない差し込みは検査に届いてはいけない() -> None:
    assert not AcceptanceCriteria(must_contain=("{対象期間}",)).opened


# ── 作成元 — 二度作らない鍵（I3）───────────────────────


def test_同じ中身なら同じ鍵の文字列() -> None:
    a = Origin.from_rule(RuleName(text="週次の依存の棚卸し"), 1, Period(text="2026-W34"))
    b = Origin.from_rule(RuleName(text="週次の依存の棚卸し"), 1, Period(text="2026-W34"))
    assert a == b and a.key == b.key


def test_版が違えば作成元も違う() -> None:
    rule, period = RuleName(text="週次の依存の棚卸し"), Period(text="2026-W34")
    assert Origin.from_rule(rule, 1, period) != Origin.from_rule(rule, 2, period)


def test_空の作成元は作れない() -> None:
    with pytest.raises(ValidationError):
        Origin(key="")
    with pytest.raises(ValueError):  # 鍵を組む前に弾く（ValidationError より手前）
        Origin.from_request("")


# ── 確かめ期日 — 送るたびに先へ進む ───────────────────────


def test_確かめ期日は期日より後() -> None:
    due = DueDate.from_start(T0, 3)
    with pytest.raises(ValidationError):
        RecheckDate(after=due.at, at=due.at - timedelta(days=1))


def test_確かめ期日は送るたびに先へ進む() -> None:
    due = DueDate.from_start(T0, 3)
    first = RecheckDate.first(due, Cycle.WEEKLY)
    assert first.at == due.at + timedelta(days=7)
    pushed = first.push(Cycle.WEEKLY)
    assert pushed.at > first.at


# ── 使った量 — 上限で止まる（I14）───────────────────────


def test_使った量は上限を超えたと言える() -> None:
    budget = Budget(calls=20, seconds=600)
    assert Spent(calls=20, seconds=600).within(budget)
    assert not Spent(calls=21, seconds=600).within(budget)
    assert not Spent(calls=20, seconds=601).within(budget)


def test_使った量は積める() -> None:
    assert Spent().plus(1, 12) == Spent(calls=1, seconds=12)
