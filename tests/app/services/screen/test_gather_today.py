"""今日の分を集める（app）の壊しかた。設計/仕事が回る筋道.md §1・人に見えるもの §2・§4。"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.screen.gather_today import gather_today
from domain.value_objects.job.today_material import TodayMaterial
from tests.app.services.conftest import 固定時計
from tests.services.conftest import make_material, 座長

月曜0902 = datetime(2026, 8, 17, 9, 2, tzinfo=UTC)


class 月曜の時計:
    def now(self) -> datetime:
        return 月曜0902


class 読みの偽物:
    """メモリの上の TodayReader。save も置くが、呼ばれたら読み専用の掟が破れた証拠。"""

    def __init__(self, *materials: TodayMaterial) -> None:
        self.materials = materials
        self.writes: list[object] = []

    def read(self, id: object) -> TodayMaterial | None:
        return self.materials[0] if self.materials else None

    def read_all(self) -> tuple[TodayMaterial, ...]:
        return self.materials

    def save(self, *args: object) -> None:
        self.writes.append(args)


def test_承認待ちは承認すると差し戻すつきで出る() -> None:
    """週Aの火09:02。材料 → 仕様 → 行 の順に詰め替わる。"""
    行 = gather_today(読みの偽物(make_material()), 固定時計(), viewer=座長.name)
    assert len(行) == 1
    assert 行[0].id == "J-0001"
    assert 行[0].state_name == "承認待ち"  # 画面に出るのは用語集の語そのまま
    assert 行[0].actions == ("approve", "send_back")
    assert 行[0].result_body == "2026-W34 の依存の一覧"


def test_答え待ちは答えるつきで出る() -> None:
    """週Aの月09:02。期日前でも押せる操作があれば出る。"""
    材料 = make_material(
        state_name="AwaitingAnswer", question_body="源の場所は変わりましたか", result_body=None
    )
    行 = gather_today(読みの偽物(材料), 月曜の時計(), viewer=座長.name)
    assert len(行) == 1
    assert 行[0].actions == ("answer",)
    assert 行[0].question_body == "源の場所は変わりましたか"


def test_AIが実行中で見立ての無い仕事は出ない() -> None:
    """人がいまできることが無い——押せることが空の行は返さない。"""
    材料 = make_material(state_name="InProgress", assignee_name=None)
    assert gather_today(読みの偽物(材料), 固定時計(), viewer=座長.name) == ()


def test_終わった仕事は出ない() -> None:
    材料 = make_material(state_name="Finished", assignee_name=None)
    assert gather_today(読みの偽物(材料), 固定時計(), viewer=座長.name) == ()


def test_帳簿に何も書かれない() -> None:
    """画面が始めるものは帳簿に書かない——Repository も Store も呼ばない。"""
    偽物 = 読みの偽物(make_material(), make_material(state_name="InProgress", assignee_name=None))
    gather_today(偽物, 固定時計(), viewer=座長.name)
    assert not 偽物.writes
