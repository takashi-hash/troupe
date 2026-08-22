"""鏡の突合 — domain と tests は1対1。

**1概念1ファイル**（単一責任）の執行者。
domain に概念を足してテストを忘れると、ここが赤くなる。
逆——テストだけが残って概念が消えた——も赤くする。
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _domain_files() -> set[pathlib.Path]:
    return {
        p.relative_to(ROOT / "domain")
        for p in (ROOT / "domain").rglob("*.py")
        if p.name != "__init__.py"
    }


def _mirror(rel: pathlib.Path) -> pathlib.Path:
    return ROOT / "tests" / rel.parent / f"test_{rel.name}"


def test_domain_の1ファイルに_tests_の鏡がある() -> None:
    欠け = [str(rel) for rel in sorted(_domain_files()) if not _mirror(rel).exists()]
    assert not 欠け, "鏡のテストが無い概念:\n" + "\n".join(欠け)


def test_tests_の鏡に_domain_の実物がある() -> None:
    """親を亡くしたテストは、消えた概念の亡霊。"""
    実物 = {_mirror(rel) for rel in _domain_files()}
    亡霊 = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "tests").rglob("test_*.py")
        if p.parent != ROOT / "tests" and p not in 実物
    ]
    assert not 亡霊, "domain に実物の無いテスト:\n" + "\n".join(亡霊)
