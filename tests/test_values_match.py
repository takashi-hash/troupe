"""突合 — 設計 §3 の値オブジェクト一覧と、domain/value_objects の実物を照合する。

正本は設計（設計/仕事とは何か.md §3 の一覧）。
遷移表・出来事には突合があったのに、値には無かった——ここで閉じる。

例外は1つだけ、docstring に書いて認める:
  `Mark`（印）——整えた応答の一部で、`Reply` と同じファイルに同居する（分割漏れではなく意図）。
"""

from __future__ import annotations

import importlib
import pathlib
import pkgutil
import re
from enum import StrEnum

from domain.obligations import Value

ROOT = pathlib.Path(__file__).resolve().parent.parent
設計 = ROOT / "設計"

#: 設計に語が無いが同居を意図した名。増えたら設計に行を足すか、ここに理由ごと書く。
同居の例外 = {"Mark"}


def _設計の値() -> set[str]:
    doc = (設計 / "仕事とは何か.md").read_text(encoding="utf-8")
    body = doc.split("### 一覧", 1)[1].split("## 4.", 1)[0]
    names = {
        m.group(1)
        for line in body.splitlines()
        if line.strip().startswith("| `")
        and (m := re.match(r"\| `([A-Z][A-Za-z]+)` \|", line.strip()))
    }
    assert names, "設計から値が1つも読めませんでした"
    return names


def _実物の値() -> set[str]:
    import domain.value_objects as pkg

    found: set[str] = set()
    for mod_info in pkgutil.walk_packages(pkg.__path__, "domain.value_objects."):
        mod = importlib.import_module(mod_info.name)
        for name, obj in vars(mod).items():
            if name.startswith("_"):
                continue
            if isinstance(obj, type) and obj.__module__ == mod_info.name:
                if issubclass(obj, Value) and obj is not Value or issubclass(obj, StrEnum):
                    found.add(name)
            elif hasattr(obj, "__metadata__"):  # Annotated の直和（担当・起こす者）
                found.add(name)
    return found


def test_値オブジェクトの一覧が設計と一致する() -> None:
    設計側 = _設計の値()
    実物 = _実物の値() - 同居の例外
    assert 設計側 == 実物, f"設計だけ: {設計側 - 実物}／コードだけ: {実物 - 設計側}"


def test_1値1ファイル() -> None:
    """ファイルは値オブジェクトの棚——空のファイルも、無関係の同居も無い。"""
    for path in (ROOT / "domain" / "value_objects").rglob("*.py"):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert re.search(r"^(class [A-Z]|[A-Z][A-Za-z]+ = )", text, re.M), (
            f"{path.relative_to(ROOT)} に値が住んでいない"
        )
