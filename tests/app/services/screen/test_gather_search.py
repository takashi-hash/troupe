"""検索するの壊しかた。人に見えるもの §1・§2——状態の語→識別子の橋は app。"""

from __future__ import annotations

from app.dto.row_filter import RowFilter
from app.ports.search_reader import SearchHit
from app.services.screen.gather_search import gather_search


class 検索読みの偽物:
    def __init__(self, hits: tuple[SearchHit, ...] = ()) -> None:
        self._hits = hits
        self.asked: tuple[str | None, ...] | None = None

    def read(
        self,
        keyword: str | None,
        state_name: str | None,
        rule: str | None,
        assignee: str | None,
    ) -> tuple[SearchHit, ...]:
        self.asked = (keyword, state_name, rule, assignee)
        return self._hits


def _hit(**over: object) -> SearchHit:
    data: dict[str, object] = {
        "id": "J-0001",
        "rule": "週次の依存の棚卸し",
        "period": "2026-W34",
        "instruction": "依存の一覧を突き合わせる",
        "state_name": "Finished",
        "due": "2026-08-20T09:00:00+00:00",
        "assignee_name": None,
    }
    return SearchHit.model_validate(data | over)


def test_状態は用語集の語で書き_識別子に写して渡る() -> None:
    読み = 検索読みの偽物()
    gather_search(読み, RowFilter(state_label="終わった"))
    assert 読み.asked == (None, "Finished", None, None)


def test_空の欄は絞らない() -> None:
    読み = 検索読みの偽物()
    gather_search(読み, RowFilter())
    assert 読み.asked == (None, None, None, None)


def test_行の状態は用語集の語に写し戻る() -> None:
    rows = gather_search(検索読みの偽物((_hit(),)), RowFilter())
    assert rows[0].state_name == "終わった"
    assert rows[0].head == "週次の依存の棚卸し　2026-W34"
    assert rows[0].due == "2026-08-20 09:00"
