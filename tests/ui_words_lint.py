"""画面の語 lint — 掟10 の執行者。

画面に出る術語が、用語集 §10「画面に出る語」の一覧にあるかを突き合わせる。
無い語が画面に現れたら赤——画面で別名を作らないための機械の見張り。

見るもの: ui/sheets.py の STATE_LABELS の値・action= の値、ui/gui.py の _PAGES と、
画面に置く短い術語（絞り込みの見出し・既定の選択肢）。
見ないもの: 出来事の名前と説明文（語ではなく文なので、人が読んで確かめる）。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "設計" / "1_言葉" / "用語集.md"


def screen_words() -> set[str]:
    """用語集 §10 の一覧を読む"""
    words: set[str] = set()
    in_section = False
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 10"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("群", "---") or cells[0].startswith("-"):
            continue
        words.update(word.strip() for word in cells[1].split("・") if word.strip())
    return words


def glossary_terms() -> set[str]:
    """§2〜§8 の語（§10 はこの部分集合でなければならない）"""
    terms: set[str] = set()
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        row = line.strip()
        if not row.startswith("|"):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", cells[-1]):
            terms.add(cells[0])
    return terms


def _strings_of(path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """label マップの値と、action= に渡された文字列を取り出す"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    maps: dict[str, list[str]] = {}
    actions: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Dict, ast.Tuple)):
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if isinstance(node.value, ast.Dict):
                    values = [v.value for v in node.value.values if isinstance(v, ast.Constant)]
                else:
                    values = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
                maps[target.id] = [v for v in values if isinstance(v, str)]
        if isinstance(node, ast.keyword) and node.arg == "action":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    actions.append(sub.value)
    return maps, actions


def _short_labels(path: Path) -> list[str]:
    """画面に置く短い術語を拾う——絞り込みの見出しと、既定の選択肢。

    文（説明文・注意書き）は語ではないので拾わない。8文字までの日本語だけを術語とみなす。
    """
    text = path.read_text(encoding="utf-8")
    found: list[str] = []
    for call in re.findall(r"_labeled_combo\(\s*\"([^\"]+)\"", text):
        found.append(call)
    for item in re.findall(r"addItem\(\s*\"([^\"]+)\"\)", text):
        found.append(item)
    return [w for w in dict.fromkeys(found) if not w.isascii() and len(w) <= 8]


def main() -> int:
    allowed = screen_words()
    terms = glossary_terms()
    problems: list[str] = []

    # §10 は §2〜§8 の部分集合か（別名を作っていないか）
    for word in sorted(allowed - terms):
        problems.append(f"用語集 §10 の「{word}」が §2〜§8 の語に無い——別名になっている")

    sheets_maps, actions = _strings_of(ROOT / "ui" / "sheets.py")
    gui_maps, _ = _strings_of(ROOT / "ui" / "gui.py")
    checked = 0
    for label in sheets_maps.get("STATE_LABELS", []):
        checked += 1
        if label not in allowed:
            problems.append(f"状態の表示「{label}」が用語集 §10 に無い")
    for page in gui_maps.get("_PAGES", []):
        checked += 1
        if page not in allowed:
            problems.append(f"画面の名前「{page}」が用語集 §10 に無い")
    for action in actions:
        checked += 1
        if action not in allowed:
            problems.append(f"操作の表示「{action}」が用語集 §10 に無い")
    for label in _short_labels(ROOT / "ui" / "gui.py"):
        checked += 1
        if label not in allowed:
            problems.append(f"画面の術語「{label}」が用語集 §10 に無い")

    if problems:
        print("画面の語 lint: 赤")
        for problem in problems:
            print(f"  赤 {problem}")
        return 1
    print(
        f"画面の語 lint: 緑（{checked} の表示が用語集 §10 の {len(allowed)} 語と一致。"
        "出来事の名前と説明文は語ではなく文なので、この lint は見ていない）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
