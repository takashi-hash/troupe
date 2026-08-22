"""突合 — 設計の出来事の表と、events/ の実物を照合する。

正本は設計（設計/仕事が回る筋道.md §5）。
"""

from __future__ import annotations

import importlib
import pathlib
import pkgutil
import re

from domain.events.event import Event

ROOT = pathlib.Path(__file__).resolve().parent.parent
設計 = ROOT / "設計"


def _設計の出来事() -> set[str]:
    doc = (設計 / "仕事が回る筋道.md").read_text(encoding="utf-8")
    body = doc.split("## 5. ドメインイベント", 1)[1].split("## 6", 1)[0]
    names = {
        m.group(1)
        for line in body.splitlines()
        if line.strip().startswith("|")
        and (m := re.search(r"\| `([A-Z][A-Za-z]+)` \|\s*$", line.strip()))
    }
    assert names, "設計から出来事が1つも読めませんでした"
    return names


def _実物の出来事() -> set[str]:
    import domain.events as pkg

    found: set[str] = set()
    for mod_info in pkgutil.walk_packages(pkg.__path__, "domain.events."):
        mod = importlib.import_module(mod_info.name)
        for name, obj in vars(mod).items():
            if (
                isinstance(obj, type)
                and issubclass(obj, Event)
                and obj is not Event
                and obj.__module__ == mod_info.name
            ):
                found.add(name)
    return found


def test_出来事の一覧が設計と一致する() -> None:
    設計側 = _設計の出来事()
    実物 = _実物の出来事()
    assert 設計側 == 実物, f"設計だけ: {設計側 - 実物}／コードだけ: {実物 - 設計側}"


def test_出来事は1出来事1ファイル() -> None:
    """ファイル名が識別子の snake_case と一致する——`ls` が §5 を読み上げる。"""
    for name in _実物の出来事():
        snake = re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()
        candidates = list((ROOT / "domain" / "events").rglob(f"{snake}.py"))
        assert candidates, f"{name} のファイル {snake}.py が無い"


def test_出来事の語の橋が設計と一致する() -> None:
    """`EVENT_WORDS` の正本は §5 の表——語も識別子も1対1。"""
    from domain.events.event import EVENT_WORDS

    doc = (設計 / "仕事が回る筋道.md").read_text(encoding="utf-8")
    body = doc.split("## 5. ドメインイベント", 1)[1].split("## 6", 1)[0]
    設計側: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"\| \*?\*?([^|*]+?)\*?\*? \| .+ \| `([A-Z][A-Za-z]+)` \|$", line.strip())
        if m:
            設計側[m.group(1).strip()] = m.group(2)
    assert 設計側 == EVENT_WORDS, (
        f"設計だけ: {set(設計側) - set(EVENT_WORDS)}／橋だけ: {set(EVENT_WORDS) - set(設計側)}"
    )
