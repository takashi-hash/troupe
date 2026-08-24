"""いまを集めるの壊しかた。設計/仕事が回る筋道.md §1・人に見えるもの §1「いま」。"""

from __future__ import annotations

from app.ports.history_reader import HistoryEntry
from app.services.screen.gather_now import gather_now
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.today_material import TodayMaterial
from tests.services.conftest import make_material


class 読みの偽物:
    def __init__(self, *materials: TodayMaterial) -> None:
        self.materials = materials

    def read(self, id: JobId) -> TodayMaterial | None:
        return None

    def read_all(self) -> tuple[TodayMaterial, ...]:
        return self.materials


class 履歴の偽物:
    def __init__(self, *entries: HistoryEntry) -> None:
        self.entries = entries

    def read_latest(self, limit: int, offset: int = 0) -> tuple[HistoryEntry, ...]:
        return self.entries[:limit]

    def count(self) -> int:
        return len(self.entries)


def _出来事(kind: str, at: str) -> HistoryEntry:
    return HistoryEntry(
        at=at, by_kind=kind, by_name=None, name="JobCreated",
        job_id="J-0001", rule=None, period=None, instruction="調べ物",
    )


def test_状態が段ごとに数えられる() -> None:
    """着手できる=待ち・実行中=作業中(見出しつき)・提出済み=検査中・承認待ち=人待ち。"""
    v = gather_now(
        読みの偽物(
            make_material(state_name="Ready"),
            make_material(state_name="InProgress"),
            make_material(state_name="Submitted"),
            make_material(state_name="AwaitingApproval"),
            make_material(state_name="AwaitingAnswer"),
        ),
        履歴の偽物(),
    )
    assert (v.queued, len(v.working), v.checking, v.waiting) == (1, 1, 1, 2)
    assert v.working[0][0] == "J-0001"  # 識別子と見出しの対
    assert v.working[0][1]


def test_最後の脈は時計の出来事の最新() -> None:
    """人やAIの出来事は脈ではない——時計の行だけを拾う。"""
    v = gather_now(
        読みの偽物(),
        履歴の偽物(
            _出来事("human", "2026-08-24 12:05"),
            _出来事("clock", "2026-08-24 12:04"),
            _出来事("clock", "2026-08-24 12:03"),
        ),
    )
    assert v.beat_at == "2026-08-24 12:04"


def test_脈がまだ無ければ空のまま発明しない() -> None:
    v = gather_now(読みの偽物(), 履歴の偽物(_出来事("agent", "2026-08-24 12:05")))
    assert v.beat_at is None
