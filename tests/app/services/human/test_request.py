"""頼む（app）の壊しかた。設計/仕事が回る筋道.md §1・§3・人に見えるもの §3。

**画面から渡るのは文字だけ**——依頼の中身も版の欄も、人が書いた文字から app が値に組む。
"""

from __future__ import annotations

from app.dto.version_form import VersionForm
from app.services.human.request import request, request_from_fields
from domain.aggregates.job.life import Created
from domain.events.job.job_created import JobCreated
from domain.events.job.job_requested import JobRequested
from tests.aggregates.job.conftest import 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物, 連番の識別子


def _欄() -> VersionForm:
    return VersionForm(
        instruction="依存の一覧を取り更新が来ているものを挙げる",
        source="file:custom/deps.txt",
        required_terms=("2026-W34",),
        description="一覧の日付が今週のものである",
        cycle="weekly",
        days=3,
        budget_calls=20,
        budget_seconds=600,
        owner=座長.name,
        max_retries=20,
    )


def test_振って_作って_出来事2つを対で書く() -> None:
    """頼む＝`JobRequested`＋`JobCreated`——1つの遷移で出来事が2つ、対のまま書かれる。"""
    帳簿 = 帳簿の偽物()
    断り = request(帳簿, 連番の識別子(), 固定時計(), by=座長.name, body="今週の依存も棚卸しして", form=_欄())
    assert 断り is None
    assert len(帳簿.jobs) == 1
    仕事 = next(iter(帳簿.jobs.values()))
    assert isinstance(仕事.state, Created)
    assert 仕事.origin.key.startswith("request:")  # 作成元は依頼の識別子（I3）
    assert [type(e) for e in 帳簿.events] == [JobRequested, JobCreated]


def test_識別子はIdPortが振る() -> None:
    帳簿 = 帳簿の偽物()
    識別子 = 連番の識別子()
    request(帳簿, 識別子, 固定時計(), by=座長.name, body="今週の依存も棚卸しして", form=_欄())
    assert 識別子.count == 2  # 仕事の識別子と依頼の識別子——立てた者が振る
    assert next(iter(帳簿.jobs)).text == "ID-0001"


def test_開かれていない差し込みは断りに変わる() -> None:
    """依頼発の基準に差し込みは書けない——義務が拒み、エラーではなく断りが返る。"""
    帳簿 = 帳簿の偽物()
    欄 = _欄().model_copy(update={"required_terms": ("{対象期間}",)})
    断り = request(帳簿, 連番の識別子(), 固定時計(), by=座長.name, body="棚卸しして", form=欄)
    assert 断り is not None
    assert not 帳簿.jobs and not 帳簿.events


def test_欄が足りなければ断りに変わる() -> None:
    """依頼発は題材の初期値が無い——書かなかった欄は発明されず、断りが返る。"""
    帳簿 = 帳簿の偽物()
    断り = request(帳簿, 連番の識別子(), 固定時計(), by=座長.name, body="棚卸しして", form=VersionForm())
    assert 断り is not None and "欄が足りません" in 断り.reason
    assert not 帳簿.jobs and not 帳簿.events


def test_欄の文字から組める_周期は用語集の語で書ける() -> None:
    """窓の頼む小窓はここを通る——版を積むと同じ組み立て（正本は1つ）。"""
    帳簿 = 帳簿の偽物()
    断り = request_from_fields(
        帳簿, 連番の識別子(), 固定時計(), by=座長.name, body="今週の依存も棚卸しして",
        fields={
            "instruction": "依存の一覧を取り更新が来ているものを挙げる",
            "source": "file:custom/deps.txt",
            "required_terms": "2026-W34",
            "cycle": "週",
            "days": "3",
            "budget_calls": "20",
            "budget_seconds": "600",
            "owner": 座長.name,
            "max_retries": "20",
        },
    )
    assert 断り is None
    仕事 = next(iter(帳簿.jobs.values()))
    assert 仕事.cycle.value == "weekly" and 仕事.instruction.text.startswith("依存の一覧")


def test_数に読めない欄は断りに変わる_窓は落ちない() -> None:
    帳簿 = 帳簿の偽物()
    断り = request_from_fields(
        帳簿, 連番の識別子(), 固定時計(), by=座長.name, body="棚卸しして", fields={"days": "三日"}
    )
    assert 断り is not None and "終えるまでの日数" in 断り.reason  # 断りも用語集の語で
    assert not 帳簿.jobs and not 帳簿.events


def test_人が書くのは3つだけ_残りは既定が効く() -> None:
    """頼む中身・源・必ず含む語だけで頼める（筋道 §1 の既定）。"""
    帳簿 = 帳簿の偽物()
    断り = request_from_fields(
        帳簿, 連番の識別子(), 固定時計(), by=座長.name, body="今週の依存も棚卸しして",
        fields={"source": "file:custom/deps.txt", "required_terms": "依存"},
    )
    assert 断り is None
    仕事 = next(iter(帳簿.jobs.values()))
    assert 仕事.instruction.text == "今週の依存も棚卸しして"  # やること=頼む中身
    assert 仕事.owner.person.name == 座長.name  # 受け持ち=頼んだ人
    assert 仕事.cycle.value == "weekly" and 仕事.max_retries == 2
    assert 仕事.budget.calls == 20 and 仕事.budget.seconds == 600


def test_中身が空なら断りは義務の文言だけ() -> None:
    """pydantic の生ダンプを画面に出さない。"""
    帳簿 = 帳簿の偽物()
    断り = request_from_fields(
        帳簿, 連番の識別子(), 固定時計(), by=座長.name, body="",
        fields={"source": "file:custom/deps.txt", "required_terms": "依存"},
    )
    assert 断り is not None
    assert 断り.reason == "依頼の中身が空です"
