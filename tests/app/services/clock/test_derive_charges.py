"""算定を導出するの壊しかた。判断はどこにも無い——口に任せて名を返すだけ。"""

from __future__ import annotations

from app.services.clock.derive_charges import derive_charges


class 導出の口の偽物:
    def derive(self) -> tuple[str, ...]:
        self.called = True
        return ("P-001 2026-08-20 NV01",)


def test_口が作った名がそのまま返る() -> None:
    口 = 導出の口の偽物()
    assert derive_charges(口) == ("P-001 2026-08-20 NV01",)
    assert 口.called
