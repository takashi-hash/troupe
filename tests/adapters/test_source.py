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


# --- 診療録（EMR）— db: の形。設計/どう作るか §4「源は腐敗防止層で翻訳」 ---

import pytest  # noqa: E402

from adapters.acl.source import EmrSource, Sources  # noqa: E402


def test_繋がっていなければ読めなかった理由に倒す() -> None:
    """診療録が無いのは環境の不足——例外ではなく、fail へ向かう材料になる。"""
    out = EmrSource(dsn=None).read(Source(location="db:chart/P-001"))
    assert isinstance(out, Unreadable)
    assert "ICHIZA_EMR_DSN" in out.reason


def test_名指しに無い在りかは読めなかった理由に倒す() -> None:
    """SQL は在りかに書けない——読めるのは名指しの抽出だけ。"""

    class _空の口:
        def execute(self, sql: str, args: tuple[object, ...] = ()) -> "_空の口":
            return self

        def fetchall(self) -> list[tuple[object, ...]]:
            return []

        def close(self) -> None: ...

    out = EmrSource(dsn="x", connect=lambda dsn: _空の口()).read(
        Source(location="db:patients; DROP TABLE patients")
    )
    assert isinstance(out, Unreadable)


def test_居ない患者のカルテは読めなかった理由に倒す() -> None:
    class _空の口:
        def execute(self, sql: str, args: tuple[object, ...] = ()) -> "_空の口":
            return self

        def fetchall(self) -> list[tuple[object, ...]]:
            return []

        def close(self) -> None: ...

    out = EmrSource(dsn="x", connect=lambda dsn: _空の口()).read(
        Source(location="db:chart/P-999")
    )
    assert isinstance(out, Unreadable)


def test_源の口の束は形で選ぶだけ(tmp_path: Path) -> None:
    """file: は書類、db: は診療録。**選ぶだけで、翻訳はそれぞれの実装がする。**"""
    (tmp_path / "書類.txt").write_text("中身", encoding="utf-8")
    束 = Sources(FileSource(tmp_path), EmrSource(dsn=None))
    ファイルの出 = 束.read(Source(location="file:書類.txt"))
    assert isinstance(ファイルの出, Quote)
    診療録の出 = 束.read(Source(location="db:chart/P-001"))
    assert isinstance(診療録の出, Unreadable)


def test_本物の診療録からカルテ抽出が引用になる() -> None:
    """本物の Postgres で（在りかが渡ったときだけ——器は買うもの）。"""
    import os

    dsn = os.environ.get("ICHIZA_EMR_DSN")
    if not dsn:
        pytest.skip("ICHIZA_EMR_DSN が無いので、診療録は読まない")
    out = EmrSource(dsn).read(Source(location="db:chart/P-003"))
    assert isinstance(out, Quote)
    assert "P-003" in out.evidence.quote
    assert "Parkinson" in out.evidence.quote
    assert out.evidence.source.location == "db:chart/P-003"
