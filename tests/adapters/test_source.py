"""源の実装の壊しかた。設計/どう作るか.md §4——外の言葉は翻訳されてから中へ入る。"""

from __future__ import annotations

from pathlib import Path

from adapters.acl.source import FileSource
from app.ports.source_port import Quote, SourcePort, Unreadable
from domain.value_objects.rule.source import Source


def test_ファイルが読めれば引用が返る(tmp_path: Path) -> None:
    """読めた中身は引用として返る——根拠に積めるのは引用だけだから。"""
    (tmp_path / "請求.txt").write_text("8月分の請求は42件、計84万円", encoding="utf-8")
    source = Source(location="file:請求.txt")
    reader: SourcePort = FileSource(root=tmp_path)
    outcome = reader.read(source)
    assert isinstance(outcome, Quote)
    assert outcome.evidence.quote == "8月分の請求は42件、計84万円"
    assert outcome.evidence.source == source


def test_無いファイルは読めなかった理由(tmp_path: Path) -> None:
    outcome = FileSource(root=tmp_path).read(Source(location="file:無い.txt"))
    assert isinstance(outcome, Unreadable)
    assert outcome.reason.strip()


def test_file以外の形も読めなかった理由(tmp_path: Path) -> None:
    for location in ("http://example.com/請求.csv", "cmd:ls", "請求.txt"):
        outcome = FileSource(root=tmp_path).read(Source(location=location))
        assert isinstance(outcome, Unreadable)
        assert outcome.reason.strip()


def test_空のファイルも読めなかった理由(tmp_path: Path) -> None:
    """空の中身は材料にも引用にもなれない——義務が拒む前に、理由へ倒す。"""
    (tmp_path / "空.txt").write_text("   \n", encoding="utf-8")
    outcome = FileSource(root=tmp_path).read(Source(location="file:空.txt"))
    assert isinstance(outcome, Unreadable)
