"""道順の材料の読み。

設計: 設計/仕事が回る筋道.md §4。
| `RouteReader` | Reader | その日の予定の訪問を、患者の座標つきで担当ごとに引く
| **app** | adapters | `gather_route` |

**Reader の返す型は渡す先で決まる**——並べるのは app（`gather_route`）、
ここは材料（拠点と訪問）を運ぶだけ。
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict


class RouteBase(BaseModel):
    """拠点 — 道順の起点。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    lat: float
    lng: float


class RouteVisit(BaseModel):
    """その日の訪問1件の材料。場所は公共の代役。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient: str
    clinician: str
    purpose: str
    place: str
    lat: float
    lng: float


class RouteReader(Protocol):
    def read_day(self, day: str) -> tuple[RouteBase | None, tuple[RouteVisit, ...]]:
        """その日の予定の訪問と拠点。診療録が繋がっていなければ（None, 空）。"""
        ...
