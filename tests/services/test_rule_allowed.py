"""業務ルールの押せることの壊しかた。仕事が回る筋道 §2・人に見えるもの §3。"""

from __future__ import annotations

from domain.services.rule_allowed import rule_allowed


def test_版を積むと有効にするはいつでも押せる() -> None:
    assert rule_allowed(None) == ("add_version", "activate")


def test_止めるは有効な版があるときだけ() -> None:
    assert rule_allowed(2) == ("add_version", "activate", "deactivate")
    assert "deactivate" not in rule_allowed(None)
