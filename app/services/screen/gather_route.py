"""道順を集める — その日の担当ごとに、予定の訪問を拠点から近い順に並べる。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの §1「道順」。
| 道順を集める | `gather_route` | その日の担当ごとに、予定の訪問を拠点から近い順に並べる
| 距離の比べだけ。並べて渡す |

並べかたは**貪欲な最近傍**——いまの地点から一番近い訪問へ。最短路の保証はしない
（実装で決めた並べかた。判断ではない——気に入らなければ人が順を無視して回ればいい）。
"""

from __future__ import annotations

import math

from app.dto.route_stop import RouteStop
from app.ports.route_reader import RouteReader, RouteVisit


def _km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    """2点の距離（km）。地球を丸として測る——道順の目安に足りる精度。"""
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def gather_route(
    route: RouteReader, day: str
) -> tuple[tuple[float, float] | None, dict[str, tuple[RouteStop, ...]]]:
    """（拠点の座標, 担当ごとの道順）。拠点から近い順に貪欲に辿る。"""
    base, visits = route.read_day(day)
    担当ごと: dict[str, list[RouteVisit]] = {}
    for v in visits:
        担当ごと.setdefault(v.clinician, []).append(v)
    out: dict[str, tuple[RouteStop, ...]] = {}
    拠点 = (base.lat, base.lng) if base else None
    for 担当, 残り in sorted(担当ごと.items()):
        いま_lat = base.lat if base else 残り[0].lat
        いま_lng = base.lng if base else 残り[0].lng
        stops: list[RouteStop] = []
        while 残り:
            次 = min(残り, key=lambda v: _km(いま_lat, いま_lng, v.lat, v.lng))
            残り.remove(次)
            leg = _km(いま_lat, いま_lng, 次.lat, 次.lng)
            stops.append(
                RouteStop(
                    seq=len(stops) + 1, patient=次.patient, place=次.place,
                    purpose=次.purpose, leg_km=f"{leg:.1f}", lat=次.lat, lng=次.lng,
                )
            )
            いま_lat, いま_lng = 次.lat, 次.lng
        out[担当] = tuple(stops)
    return 拠点, out
