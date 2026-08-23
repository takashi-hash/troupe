"""算定の導出の口の宣言の壊しかた。筋道 §4——裁く・確定する口は無い。"""

from __future__ import annotations

from app.ports.emr_charge_port import EmrChargePort


class 導出の口の偽物:
    def derive(self) -> tuple[str, ...]:
        return ()


def test_宣言は名乗りだけで満たせる() -> None:
    口: EmrChargePort = 導出の口の偽物()
    assert 口.derive() == ()


def test_裁く口も確定する口も無い() -> None:
    """自動から判断へ届く道が型に無いこと——公理の実物。"""
    assert not hasattr(EmrChargePort, "resolve")
    assert not hasattr(EmrChargePort, "confirm")
