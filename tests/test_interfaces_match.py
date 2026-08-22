"""突合 — 設計の §1 の操作表・§4 の interface 表と、実物を照合する。

正本は設計（設計/仕事が回る筋道.md §1・§4）。
- §1: 識別子 ↔ ファイル（app/services/<起こす者>/ か domain/aggregates/）。両向き
- §4: interface 名 ↔ 宣言のファイルと場所（domain/repositories か app/ports）。両向き
- §4: 要求者欄の識別子が実際にその interface を import しているか
  （丸括弧の中は補足なので照合しない。app のサービスに無い名——domain の操作——は
  ファイルの居場所だけを別の検で見る）
"""

from __future__ import annotations

import importlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
筋道 = (ROOT / "設計" / "仕事が回る筋道.md").read_text(encoding="utf-8")

#: 起こす者の見出し → app/services/ のフォルダ。
起こす者 = {
    "人が始めるもの": "human",
    "AI が始めるもの": "agent",
    "画面が始めるもの": "screen",
    "時計が始めるもの": "clock",
}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()


def _操作表(見出し: str) -> set[str]:
    body = 筋道.split(f"### {見出し}", 1)[1].split("###", 1)[0]
    ids = {
        m.group(1)
        for line in body.splitlines()
        if line.strip().startswith("|")
        and (m := re.match(r"\|[^|]+\| `([a-z_]+)` \|", line.strip()))
    }
    assert ids, f"設計から {見出し} の識別子が1つも読めませんでした"
    return ids


def _interface表() -> list[tuple[str, str, str, str]]:
    """§4 の行——（名, 接尾辞, 宣言, 要求者の欄）。"""
    body = 筋道.split("## 4. interface", 1)[1].split("### 決まり", 1)[0]
    rows: list[tuple[str, str, str, str]] = []
    for line in body.splitlines():
        m = re.match(
            r"\| `([A-Z][A-Za-z]+)` \| (\w+) \|.+\| \**([a-z]+)\** \| adapters \|(.+)\|",
            line.strip(),
        )
        if m:
            rows.append((m.group(1), m.group(2), m.group(3), m.group(4)))
    assert rows, "設計から interface が1行も読めませんでした"
    return rows


def test_操作の識別子にファイルがある() -> None:
    """§1 の識別子は app のサービスか domain の操作として実在する。"""
    for 見出し in 起こす者:
        for id in _操作表(見出し):
            候補 = [
                ROOT / "app" / "services" / 起こす者[見出し] / f"{id}.py",
                ROOT / "domain" / "aggregates" / "job" / f"{id}.py",
                ROOT / "domain" / "aggregates" / "rule" / f"{id}.py",
                ROOT / "app" / "services" / "clock" / f"{id}.py",
            ]
            assert any(p.exists() for p in 候補), f"{見出し}の {id} にファイルが無い"


def test_表に無い操作ファイルが無い() -> None:
    """app/services/<起こす者>/ の1ファイルは §1 の1行——表に無いものは作らない。"""
    for 見出し, folder in 起こす者.items():
        ids = _操作表(見出し)
        for p in (ROOT / "app" / "services" / folder).glob("*.py"):
            if p.stem == "__init__":
                continue
            assert p.stem in ids, f"app/services/{folder}/{p.name} が §1 の表に無い"


def test_interfaceの宣言が表の場所にある() -> None:
    """宣言の場所（domain/repositories か app/ports）に、その名の Protocol が居る。"""
    for name, suffix, 宣言, _ in _interface表():
        assert name.endswith(suffix), f"{name} が接尾辞 {suffix} で終わらない"
        module = {
            "domain": f"domain.repositories.{_snake(name)}",
            "app": f"app.ports.{_snake(name)}",
        }[宣言]
        mod = importlib.import_module(module)
        assert hasattr(mod, name), f"{module} に {name} が居ない"


def test_表に無いinterfaceファイルが無い() -> None:
    names = {name for name, _, _, _ in _interface表()}
    for folder in (ROOT / "domain" / "repositories", ROOT / "app" / "ports"):
        for p in folder.glob("*.py"):
            if p.stem == "__init__":
                continue
            camel = "".join(w.capitalize() for w in p.stem.split("_"))
            assert camel in names, f"{folder.name}/{p.name}（{camel}）が §4 の表に無い"


def test_要求者は本当にそのinterfaceを使っている() -> None:
    """要求者欄の識別子（app のサービスに実在するもの）が、その interface を import している。

    丸括弧の中は補足——「使わない理由」も書かれるので照合しない。
    """
    for name, _, _, 要求者 in _interface表():
        素 = re.sub(r"（[^）]*）", "", 要求者)
        for token in re.findall(r"`([a-z_]+)`", 素):
            hits = list((ROOT / "app" / "services").glob(f"*/{token}.py"))
            if not hits:
                continue  # domain の操作——ファイルの居場所は操作表の検が見る
            text = hits[0].read_text(encoding="utf-8")
            assert name in text, f"§4 は {token} が {name} を使うと言うが、import が無い"
