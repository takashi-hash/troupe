"""題材の実装の壊しかた。設計/どう作るか.md §4・§5——読めない題材は初期値なしと同じ。"""

from __future__ import annotations

import json
from pathlib import Path

from adapters.topic import FolderTopic
from app.ports.topic_port import TopicPort
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.rule.rule_name import RuleName

題材 = {
    "instruction": "先月分の請求を集計する",
    "source": "file:custom/月次請求/請求.csv",
    "required_terms": ["{対象期間}", "請求"],
    "description": "先月分の請求がすべて出ていること",
    "cycle": "monthly",
    "days": 5,
    "budget_calls": 10,
    "budget_seconds": 600,
    "owner": "橋本",
    "max_retries": 3,
}


def _置く(root: Path, name: str, text: str) -> None:
    folder = root / name
    folder.mkdir()
    (folder / "topic.json").write_text(text, encoding="utf-8")


def test_topicjsonから写すものの束が組める(tmp_path: Path) -> None:
    _置く(tmp_path, "月次請求", json.dumps(題材, ensure_ascii=False))
    topics: TopicPort = FolderTopic(root=tmp_path)
    copied = topics.read(RuleName(text="月次請求"))
    assert copied is not None
    assert copied.instruction.text == "先月分の請求を集計する"
    assert copied.criteria.required_terms == ("{対象期間}", "請求")
    assert copied.criteria.description == "先月分の請求がすべて出ていること"
    assert copied.cycle is Cycle.MONTHLY
    assert copied.owner.person.name == "橋本"
    assert copied.budget.calls == 10
    assert copied.budget.seconds == 600
    assert copied.source.location == "file:custom/月次請求/請求.csv"
    assert copied.max_retries == 3
    assert copied.days == 5


def test_題材が無ければNone(tmp_path: Path) -> None:
    assert FolderTopic(root=tmp_path).read(RuleName(text="無い題材")) is None


def test_壊れたJSONはNone(tmp_path: Path) -> None:
    _置く(tmp_path, "月次請求", "{ これは JSON ではない")
    assert FolderTopic(root=tmp_path).read(RuleName(text="月次請求")) is None


def test_欄の足りないJSONもNone(tmp_path: Path) -> None:
    欠け = {k: v for k, v in 題材.items() if k != "cycle"}
    _置く(tmp_path, "月次請求", json.dumps(欠け, ensure_ascii=False))
    assert FolderTopic(root=tmp_path).read(RuleName(text="月次請求")) is None
