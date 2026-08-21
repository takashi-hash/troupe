"""対訳 lint — 用語集 §11 の執行者（設計/7_配置/層割当て表.md §4 の5）。

全層について確かめる:
  0. 用語集そのものが**1語1識別子の全単射**か（両向き。片向きしか見ていなかった）
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
LAYERS = ["domain", "app", "adapters", "ui"]

# 道具を持つ層。ここでだけ、下の TOOL_NAMES を名乗れる
TOOL_LAYERS = ("adapters", "ui")

# 道具の構造の名——ドメインの語ではないので登録しない（掟9 の3つ目の線）。
# 足すときは「これはドメインの語か、道具の構造か」を右の1行で言えること。
# domain/ と app/ には道具が無いので、この抜け道はそこでは効かない
TOOL_NAMES = {
    "SqliteLedger": "SQLite という道具＋役割",
    "TomlCustom": "TOML という道具＋役割",
    "StubLlm": "仮物という役割",
    "connection": "SQLite の接続",
    "write": "トランザクションという道具の慣例",
    "MainWindow": "Qt の窓",
    "Page": "Qt の頁",
    "SearchPage": "Qt の頁",
    "JobSheetPage": "Qt の頁",
    "Card": "Qt の部品",
    "FilterBar": "Qt の部品",
    "Row": "画面の行という入れ物",
    "Section": "画面の節という入れ物",
    "populate": "Qt の部品に中身を入れる",
    "mouseReleaseEvent": "Qt が決めた名（override）",
    "run": "起動という道具の慣例",
}


def load_mapping() -> dict[str, str]:
    """全ての表から 識別子 → 語 を読む。**1語1識別子の全単射**を両向きに確かめる"""
    mapping: dict[str, str] = {}
    seen: dict[str, str] = {}
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
        # 逆向きも見る——**1語1識別子の全単射**（2026-08-21 まで片方向しか見ておらず、
        # 「予定」が Outlook と Prospect に、「成果物の置き場」が ArtifactStore と
        # artifact_slot に割り当たっていた。同義語ゼロが2箇所で破れていた）
        if term in seen and seen[term] != ident:
            print(f"語が二重: 「{term}」が {seen[term]} と {ident} の両方に割当——1語1識別子")
            sys.exit(1)
        seen[term] = ident
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
                    if layer in TOOL_LAYERS and name in TOOL_NAMES:
                        continue  # 道具の構造の名（登録しない）
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
    print(
        f"対訳 lint: 緑（全層の識別子は英語で、{len(mapping)} 語の対訳と一致。"
        f"道具の構造 {len(TOOL_NAMES)} 個は登録しない）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
