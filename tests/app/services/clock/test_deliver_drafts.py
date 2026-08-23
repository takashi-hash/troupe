"""下書きを配達する（app）の壊しかた。筋道 §1——印の無いものだけ運ぶ・置いてから刻む。"""

from __future__ import annotations

from app.services.clock.deliver_drafts import deliver_drafts
from domain.aggregates.job.life import Cleared, Ready
from domain.events.job.draft_delivered import DraftDelivered
from domain.value_objects.job.approval import Approval
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.result import Result
from domain.value_objects.rule.source import Source
from tests.aggregates.job.conftest import make_job, いま, 座長
from tests.app.services.clock.conftest import 成果置き場の偽物, 状態の読みの偽物
from tests.app.services.conftest import 固定時計, 帳簿の偽物

承認 = Cleared(approval=Approval(by=座長, at=いま))


class 下書き受けの偽物:
    def __init__(self, 届く: bool = True) -> None:
        self.置いた: list[tuple[str, str, str]] = []
        self._届く = 届く

    def deposit(self, job_id: str, patient_code: str, body: str) -> bool:
        if not self._届く:
            return False
        self.置いた.append((job_id, patient_code, body))
        return True


class 印読みの偽物:
    """帳簿の偽物から導く DeliveredMarkReader——本物と同じ向き（印は出来事から）。"""

    def __init__(self, ledger: 帳簿の偽物) -> None:
        self._ledger = ledger

    def marked_ids(self) -> frozenset[JobId]:
        return frozenset(
            job.id
            for job in self._ledger.jobs.values()
            if any(isinstance(e, DraftDelivered) for e in self._ledger.events)
        ) if any(isinstance(e, DraftDelivered) for e in self._ledger.events) else frozenset()


def _場(state: object, location: str, result_at: str | None = None):
    帳簿 = 帳簿の偽物()
    成果 = 成果置き場の偽物()
    at = result_at or 成果.put(Result(body="SOAP draft body"))
    job = make_job(state, source=Source(location=location), result_at=at)  # type: ignore[arg-type]
    帳簿.jobs[job.id] = job
    return 帳簿, 状態の読みの偽物(帳簿), 成果


def test_承認の済んだカルテの下書きが配達され_出来事が刻まれる() -> None:
    帳簿, 状態, 成果 = _場(承認, "db:chart/P-003")
    受け = 下書き受けの偽物()
    出た = deliver_drafts(帳簿, 状態, 成果, 印読みの偽物(帳簿), 受け, 固定時計())
    assert [j.text for j in 出た] == ["J-0001"]
    assert 受け.置いた[0][1] == "P-003"
    assert any(isinstance(e, DraftDelivered) for e in 帳簿.events)  # 配達は帳簿に残る事実


def test_印のある仕事は二度運ばない() -> None:
    """帳簿が覚えている——診療録の種を入れ直しても再配達されない、の根。"""
    帳簿, 状態, 成果 = _場(承認, "db:chart/P-003")
    受け = 下書き受けの偽物()
    deliver_drafts(帳簿, 状態, 成果, 印読みの偽物(帳簿), 受け, 固定時計())
    二度目 = deliver_drafts(帳簿, 状態, 成果, 印読みの偽物(帳簿), 受け, 固定時計())
    assert 二度目 == () and len(受け.置いた) == 1


def test_診療録に届かなければ刻まない() -> None:
    """置いてから刻む——次の脈がまた来る。"""
    帳簿, 状態, 成果 = _場(承認, "db:chart/P-003")
    出た = deliver_drafts(帳簿, 状態, 成果, 印読みの偽物(帳簿), 下書き受けの偽物(届く=False), 固定時計())
    assert 出た == ()
    assert not any(isinstance(e, DraftDelivered) for e in 帳簿.events)


def test_カルテの下書きでない仕事は配達しない() -> None:
    帳簿, 状態, 成果 = _場(承認, "db:visit-schedule")
    受け = 下書き受けの偽物()
    assert deliver_drafts(帳簿, 状態, 成果, 印読みの偽物(帳簿), 受け, 固定時計()) == ()
    assert 受け.置いた == []


def test_承認前の仕事は配達しない() -> None:
    帳簿, 状態, 成果 = _場(Ready(), "db:chart/P-001")
    受け = 下書き受けの偽物()
    assert deliver_drafts(帳簿, 状態, 成果, 印読みの偽物(帳簿), 受け, 固定時計()) == ()
