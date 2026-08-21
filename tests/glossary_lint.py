"""対訳 lint — 用語集 §11 の執行者（設計/7_配置/層割当て表.md §4 の5）。

domain/ と app/ について確かめる:
  1. 和名の識別子が現れたら赤（コードの識別子は英語——読みかた 掟9）
  2. 公開の型・関数の名前が用語集 §11 の対訳に未登録なら赤（勝手訳の禁止）
  3. 登録済みの型・関数の docstring に、対応する設計の語が無ければ赤（grep の錨）
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "設計" / "1_言葉" / "用語集.md"
LAYERS = ["domain", "app"]


def load_mapping() -> dict[str, str]:
    """全ての表から 識別子 → 語 を読む——行の最後の欄が英語の識別子なら対訳とみなす"""
    mapping: dict[str, str] = {}
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        row = line.strip()
        if not row.startswith("|"):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 2:
            continue
        term, ident = cells[0], cells[-1]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", ident):
            continue
        if ident in mapping and mapping[ident] != term:
            print(f"対訳が二重: {ident} が「{mapping[ident]}」と「{term}」の両方に割当")
            sys.exit(1)
        mapping[ident] = term
    return mapping


def main() -> int:
    mapping = load_mapping()
    problems: list[str] = []

    for layer in LAYERS:
        for path in (ROOT / layer).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            where = path.relative_to(ROOT)
            for node in ast.walk(tree):
                names: list[
                    tuple[str, int, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | None]
                ] = []
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.append((node.name, node.lineno, node))
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            names.append((t.id, node.lineno, None))
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    names.append((node.target.id, node.lineno, None))

                for name, lineno, defn in names:
                    if not name.isascii():
                        problems.append(f"{where}:{lineno} {name} — 和名の識別子。英語にする（訳は用語集 §11 へ）")
                        continue
                    if defn is None or name.startswith("_"):
                        continue
                    if name not in mapping:
                        problems.append(f"{where}:{lineno} {name} — 用語集 §11 に未登録。先に対訳を足してから使う")
                        continue
                    term = mapping[name]
                    doc = ast.get_docstring(defn) or ""
                    if term not in doc:
                        problems.append(f"{where}:{lineno} {name} — docstring に「{term}」が無い（grep の錨）")

    if problems:
        print("対訳 lint: 赤")
        for p in problems:
            print(f"  赤 {p}")
        return 1
    print(f"対訳 lint: 緑（domain と app の識別子は英語で、{len(mapping)} 語の対訳と一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
