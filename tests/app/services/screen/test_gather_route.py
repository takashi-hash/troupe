"""道順を集めるの壊しかた。人に見えるもの §1——拠点から近い順・担当ごと。"""

from __future__ import annotations

from app.ports.route_reader import RouteBase, RouteVisit
from app.services.screen.gather_route import gather_route

拠点 = RouteBase(name="Clinic", lat=35.6433, lng=139.6690)


def _訪問(code: str, lat: float, lng: float, 担当: str = "Dr-A") -> RouteVisit:
    return RouteVisit(patient=code, clinician=担当, purpose="visit",
                      place=f"{code} landmark", lat=lat, lng=lng)


class 道順読みの偽物:
    def __init__(self, visits: tuple[RouteVisit, ...]) -> None:
        self._visits = visits

    def read_day(self, day: str) -> tuple[RouteBase | None, tuple[RouteVisit, ...]]:
        return 拠点, self._visits


def test_拠点から近い順に並ぶ() -> None:
    遠い = _訪問("P-FAR", 35.70, 139.60)
    近い = _訪問("P-NEAR", 35.645, 139.668)
    中 = _訪問("P-MID", 35.66, 139.66)
    拠点座標, 道順 = gather_route(道順読みの偽物((遠い, 近い, 中)), "2026-08-24")
    assert 拠点座標 == (拠点.lat, 拠点.lng)
    assert [s.patient for s in 道順["Dr-A"]] == ["P-NEAR", "P-MID", "P-FAR"]
    assert 道順["Dr-A"][0].seq == 1


def test_担当ごとに分かれる() -> None:
    _, 道順 = gather_route(道順読みの偽物((_訪問("P-1", 35.65, 139.66, "Dr-A"),
                                           _訪問("P-2", 35.63, 139.66, "Dr-B"))), "2026-08-24")
    assert set(道順) == {"Dr-A", "Dr-B"}


def test_訪問の無い日は空() -> None:
    assert gather_route(道順読みの偽物(()), "2026-08-24")[1] == {}
