"""鏡の突合 — domain と tests は1対1。

**1概念1ファイル**（単一責任）の執行者。
domain に概念を足してテストを忘れると、ここが赤くなる。
逆——テストだけが残って概念が消えた——も赤くする。
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


#: 鏡に映す層。adapters と ui は実装なので、統合の試験が別に見る。
層 = ("domain", "app")


def _watched() -> set[pathlib.Path]:
    found: set[pathlib.Path] = set()
    for layer in 層:
        for p in (ROOT / layer).rglob("*.py"):
            if p.name != "__init__.py":
                found.add(p.relative_to(ROOT))
    return found


def _mirror(rel: pathlib.Path) -> pathlib.Path:
    parts = rel.parts
    if parts[0] == "domain":
        parts = parts[1:]
    return ROOT / "tests" / pathlib.Path(*parts[:-1]) / f"test_{parts[-1]}"


def test_見張る層の1ファイルに_tests_の鏡がある() -> None:
    欠け = [str(rel) for rel in sorted(_watched()) if not _mirror(rel).exists()]
    assert not 欠け, "鏡のテストが無い概念:\n" + "\n".join(欠け)


def test_tests_の鏡に実物がある() -> None:
    """親を亡くしたテストは、消えた概念の亡霊。"""
    実物 = {_mirror(rel) for rel in _watched()}
    亡霊 = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "tests").rglob("test_*.py")
        if p.parent != ROOT / "tests" and p not in 実物
    ]
    assert not 亡霊, "実物の無いテスト:\n" + "\n".join(亡霊)
