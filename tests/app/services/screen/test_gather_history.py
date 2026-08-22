"""履歴を集めるの壊しかた。人に見えるもの §1・§2——用語集の語と見出しつきで出る。"""

from __future__ import annotations

from app.ports.history_reader import HistoryEntry
from app.services.screen.gather_history import gather_history


class 履歴読みの偽物:
    def __init__(self, entries: tuple[HistoryEntry, ...]) -> None:
        self._entries = entries
        self.asked_limit: int | None = None

    def read_latest(self, limit: int) -> tuple[HistoryEntry, ...]:
        self.asked_limit = limit
        return self._entries


def _entry(**over: object) -> HistoryEntry:
    data: dict[str, object] = {
        "at": "2026-08-22 09:00",
        "by_kind": "clock",
        "by_name": None,
        "name": "JobCreated",
        "job_id": "J-0001",
        "rule": "週次の依存の棚卸し",
        "period": "2026-W34",
        "instruction": "依存の一覧を突き合わせる",
    }
    return HistoryEntry.model_validate(data | over)


def test_出来事は用語集の語で_見出しは業務ルールと対象期間() -> None:
    rows = gather_history(履歴読みの偽物((_entry(),)))
    assert rows[0].what == "仕事が作られた"  # 画面に出るのは用語集の語そのまま
    assert rows[0].by == "時計"  # 名が無ければ起こす者の語（橋は ACTOR_WORDS の1つ）
    assert rows[0].head == "週次の依存の棚卸し　2026-W34"
    assert rows[0].job_id == "J-0001"


def test_依頼発の見出しはやることの先頭() -> None:
    rows = gather_history(
        履歴読みの偽物((_entry(rule=None, period=None, instruction="請求の合計を確かめる\n細かい手順…"),))
    )
    assert rows[0].head == "請求の合計を確かめる"


def test_上限が読みに渡る() -> None:
    読み = 履歴読みの偽物(())
    gather_history(読み, limit=50)
    assert 読み.asked_limit == 50
