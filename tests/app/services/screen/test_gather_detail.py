"""詳細を集めるの壊しかた。人に見えるもの §1・§2——出来事の全部が用語集の語で出る。"""

from __future__ import annotations

from app.ports.detail_reader import DetailMaterial
from app.services.screen.gather_detail import gather_detail
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.today_material import TodayMaterial
from tests.app.services.conftest import 固定時計
from tests.services.conftest import make_material


class 今日読みの偽物:
    def __init__(self, material: TodayMaterial | None) -> None:
        self._m = material

    def read(self, id: JobId) -> TodayMaterial | None:
        return self._m

    def read_all(self) -> tuple[TodayMaterial, ...]:
        return (self._m,) if self._m else ()


class 詳細読みの偽物:
    def read(self, id: JobId) -> DetailMaterial:
        return DetailMaterial(
            events=(("2026-08-22 09:00", "clock", None, "JobCreated"), ("2026-08-22 09:01", "agent", "一号", "JobStarted")),
            questions=(("どちらの依存ですか", "手元です"),),
        )


def test_出来事が用語集の語で全部出る() -> None:
    view = gather_detail(今日読みの偽物(make_material()), 詳細読みの偽物(), 固定時計(), "座長", "J-0001")
    assert view is not None
    assert [e.what for e in view.events] == ["仕事が作られた", "着手された"]
    assert [e.by for e in view.events] == ["時計", "一号"]  # 名が無ければ起こす者の語
    assert view.state_name == "承認待ち"  # 画面に出るのは用語集の語そのまま


def test_無い仕事は_None() -> None:
    assert gather_detail(今日読みの偽物(None), 詳細読みの偽物(), 固定時計(), "座長", "J-9999") is None


def test_名が組めなければ_None() -> None:
    assert gather_detail(今日読みの偽物(make_material()), 詳細読みの偽物(), 固定時計(), " ", "J-0001") is None
