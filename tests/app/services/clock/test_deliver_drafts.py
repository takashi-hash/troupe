"""下書きを配達するの壊しかた。筋道 §1——承認は済んでいる。運ぶだけ・二度置かない。"""

from __future__ import annotations

from app.services.clock.deliver_drafts import deliver_drafts
from domain.aggregates.job.life import Cleared, Ready
from domain.value_objects.job.approval import Approval
from tests.aggregates.job.conftest import いま, 座長
from domain.value_objects.job.result import Result
from domain.value_objects.rule.source import Source
from tests.aggregates.job.conftest import make_job
from tests.app.services.clock.conftest import 成果置き場の偽物, 状態の読みの偽物
from tests.app.services.conftest import 帳簿の偽物


class 下書き受けの偽物:
    def __init__(self, 既に: frozenset[str] = frozenset()) -> None:
        self.置いた: list[tuple[str, str, str]] = []
        self._既に = 既に

    def deposit(self, job_id: str, patient_code: str, body: str) -> bool:
        if job_id in self._既に:
            return False
        self.置いた.append((job_id, patient_code, body))
        return True


def _場(state: object, location: str) -> tuple[帳簿の偽物, 状態の読みの偽物, 成果置き場の偽物]:
    帳簿 = 帳簿の偽物()
    成果 = 成果置き場の偽物()
    at = 成果.put(Result(body="SOAP draft body"))
    job = make_job(state, source=Source(location=location), result_at=at)  # type: ignore[arg-type]
    帳簿.jobs[job.id] = job
    return 帳簿, 状態の読みの偽物(帳簿), 成果


def test_承認の済んだカルテの下書きが患者ごと配達される() -> None:
    帳簿, 状態, 成果 = _場(Cleared(approval=Approval(by=座長, at=いま)), "db:chart/P-003")
    受け = 下書き受けの偽物()
    出た = deliver_drafts(帳簿, 状態, 成果, 受け)
    assert [j.text for j in 出た] == ["J-0001"]
    assert 受け.置いた == [("J-0001", "P-003", "SOAP draft body")]


def test_カルテの下書きでない仕事は配達しない() -> None:
    """源が db:chart/ でない仕事——点検や棚卸し——は診療録に置くものではない。"""
    帳簿, 状態, 成果 = _場(Cleared(approval=Approval(by=座長, at=いま)), "db:visit-schedule")
    受け = 下書き受けの偽物()
    assert deliver_drafts(帳簿, 状態, 成果, 受け) == ()
    assert 受け.置いた == []


def test_同じ仕事から二度置かない() -> None:
    """冪等——決めるのは診療録の一意の鍵。ここは返りを見るだけ。"""
    帳簿, 状態, 成果 = _場(Cleared(approval=Approval(by=座長, at=いま)), "db:chart/P-003")
    受け = 下書き受けの偽物(既に=frozenset({"J-0001"}))
    assert deliver_drafts(帳簿, 状態, 成果, 受け) == ()
    assert 受け.置いた == []


def test_承認前の仕事は配達しない() -> None:
    帳簿, 状態, 成果 = _場(Ready(), "db:chart/P-001")
    受け = 下書き受けの偽物()
    assert deliver_drafts(帳簿, 状態, 成果, 受け) == ()
    assert 受け.置いた == []
