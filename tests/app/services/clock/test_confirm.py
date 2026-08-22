"""確かめる（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」・I5。

確かめ待ちは確かめ期日が来たものだけ読む（実装の決め、app/services/clock/confirm.py）。
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.ports.source_port import Quote, Unreadable
from app.services.clock.confirm import confirm
from domain.aggregates.job.life import Cleared, Finished, FinishedPendingRecheck
from domain.events.job.job_finished import JobFinished
from domain.values.job.approval import Approval
from domain.values.job.evidence import Evidence
from domain.values.job.recheck_date import RecheckDate
from domain.values.rule.source import Source
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.clock.conftest import 根拠置き場の偽物, 状態の読みの偽物, 源の偽物
from tests.app.services.conftest import いま, 固定時計, 帳簿の偽物

承認 = Approval(by=座長, at=いま)
引用 = Quote(evidence=Evidence(quote="依存はぜんぶ最新", source=Source(location="deps://prod")))
読めない = Unreadable(reason="源が落ちている")


def test_根拠の在りかが空でなければ_読み直さず終わる() -> None:
    帳簿 = 帳簿の偽物()
    根拠置き場 = 根拠置き場の偽物()
    在りか = 根拠置き場.put(引用.evidence)
    仕事 = make_job(Cleared(approval=承認), result_at="result://1", evidence_at=在りか)
    帳簿.jobs[仕事.id] = 仕事
    源 = 源の偽物(読めない)
    確かめた = confirm(帳簿, 状態の読みの偽物(帳簿), 源, 根拠置き場, 固定時計())
    assert 確かめた == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Finished)
    assert 源.reads == 0  # 積まれた根拠は必ず揃っている——読み直さない
    assert [type(e) for e in 帳簿.events] == [JobFinished]


def test_根拠が無ければ源を読み直し_取れた引用は積んでから終わる() -> None:
    帳簿 = 帳簿の偽物()
    根拠置き場 = 根拠置き場の偽物()
    仕事 = make_job(Cleared(approval=承認), result_at="result://1")
    帳簿.jobs[仕事.id] = 仕事
    源 = 源の偽物(引用)
    確かめた = confirm(帳簿, 状態の読みの偽物(帳簿), 源, 根拠置き場, 固定時計())
    assert 確かめた == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Finished)
    在りか = 帳簿.jobs[仕事.id].evidence_at
    assert 在りか is not None and 根拠置き場.get(在りか) == 引用.evidence


def test_取れなければ確かめ待ちへ_確かめ期日が来るまで触らない() -> None:
    """源を読むのでここだけ結果が変わりうる——変わらない限り2度目は何もしない。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Cleared(approval=承認), result_at="result://1")
    帳簿.jobs[仕事.id] = 仕事
    状態の読み = 状態の読みの偽物(帳簿)
    源 = 源の偽物(読めない)
    assert confirm(帳簿, 状態の読み, 源, 根拠置き場の偽物(), 固定時計()) == (仕事.id,)
    状態 = 帳簿.jobs[仕事.id].state
    assert isinstance(状態, FinishedPendingRecheck) and 状態.recheck.at > いま
    assert confirm(帳簿, 状態の読み, 源, 根拠置き場の偽物(), 固定時計()) == ()
    assert 源.reads == 1 and len(帳簿.events) == 1  # 期日が来るまで読み直さない


def test_確かめ期日が来ていれば読み直し_取れたら終わる() -> None:
    帳簿 = 帳簿の偽物()
    根拠置き場 = 根拠置き場の偽物()
    来た期日 = RecheckDate(
        after=datetime(2026, 8, 10, 9, 0, tzinfo=UTC), at=datetime(2026, 8, 15, 9, 0, tzinfo=UTC)
    )
    仕事 = make_job(
        FinishedPendingRecheck(approval=承認, recheck=来た期日), result_at="result://1"
    )
    帳簿.jobs[仕事.id] = 仕事
    確かめた = confirm(帳簿, 状態の読みの偽物(帳簿), 源の偽物(引用), 根拠置き場, 固定時計())
    assert 確かめた == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Finished)
    assert 帳簿.jobs[仕事.id].evidence_at is not None
