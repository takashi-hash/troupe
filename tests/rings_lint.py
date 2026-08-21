"""輪の一覧 lint — 調停図と app/manager.py を突き合わせる（宣言に執行者を）。

2026-08-21、同じものを数える場所が4つあって、どれも違う数を言っていた:

| 数える場所 | 言っていた数 | 欠けていたもの |
|---|---|---|
| 調停図 §1 の見出し | 7 | —— |
| 調停図 §1 の図 | 6 | `verify`（`dispatch` は和名の節で描かれていた） |
| 調停図 §2 の表 | 6 | `verify` |
| app/manager.py の説明 | 6 | `confirm`（`triage` を未実装と書いていた） |
| app/manager.py の実物 | 6 | `surface` |

**数だけ直して中身を直さない**が繰り返し起きた形なので、数える場所を1つ（§2 の表）に決めて、
図・見出し・実装がそこと一致することを機械に確かめさせる。

あわせて surface の出口も見る——今日の枚が警告しか受け取っていないこと。
判定の材料が画面に渡っているかぎり、画面はいつでもまた判定を始められる。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIAGRAM = ROOT / "設計" / "5_出来事" / "調停図.md"
MANAGER = ROOT / "app" / "manager.py"

# 輪ではない公開の関数（理由を1行で言えるものだけ）
HELPERS = {"version_of": "輪ではなく、輪が使う引き"}


def declared() -> list[str]:
    """§2 の表が並べる輪——ここが正本"""
    rows = re.findall(r"^\| `([a-z_]+)` \|", DIAGRAM.read_text(encoding="utf-8"), re.MULTILINE)
    return rows


def implemented() -> set[str]:
    """app/manager.py の公開の関数（引きを除く）"""
    tree = ast.parse(MANAGER.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and not node.name.startswith("_")
        and node.name not in HELPERS
    }


def judgment_stays_out_of_the_screen() -> list[str]:
    """今日の枚は警告しか受け取らない——材料が無ければ判定しようがない（掟の執行者は型）。

    2026-08-21 まで `morning_sections(jobs, now, viewer)` で、画面が自分で
    「何が赤か」を決めていた。渡すものを警告だけに狭めたのがこの掟の中身なので、
    狭めたことを機械が見張る。
    """
    tree = ast.parse((ROOT / "ui" / "sheets.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "morning_sections":
            names = [arg.arg for arg in node.args.args]
            if names != ["alerts"]:
                return [
                    f"morning_sections が {names} を受け取っている——警告だけにする"
                    "（材料を渡すと、画面がまた判定できてしまう）"
                ]
            return []
    return ["ui/sheets.py に morning_sections が無い"]


def main() -> int:
    text = DIAGRAM.read_text(encoding="utf-8")
    rings = declared()
    problems: list[str] = []

    heading = re.search(r"^## 1\. (\d+)つの輪", text, re.MULTILINE)
    if heading is None:
        problems.append("調停図 §1 の見出しが「N つの輪」の形でない")
    elif int(heading.group(1)) != len(rings):
        problems.append(
            f"見出しは {heading.group(1)}つ、§2 の表は {len(rings)}つ——数える場所は表が正本"
        )

    # 図の「矢印」に居ることまで見る——節だけ描いて繋がない輪は、回っていない
    wired = "\n".join(l for l in text.split("## 2.")[0].splitlines() if "-->" in l)
    for ring in rings:
        if not re.search(rf"\b{ring}\b", wired):
            problems.append(f"{ring} が §1 の図で繋がっていない（表にあるのに回っていない）")

    problems += judgment_stays_out_of_the_screen()

    built = implemented()
    for ring in rings:
        if ring not in built:
            problems.append(f"{ring} が app/manager.py に無い——宣言だけの輪は実装ではない")
    for name in sorted(built - set(rings)):
        problems.append(f"{name} が調停図 §2 の表に無い——輪なら足す、輪でないなら HELPERS へ")

    if problems:
        print("輪の一覧 lint: 赤")
        for problem in problems:
            print(f"  赤 {problem}")
        return 1
    print(
        f"輪の一覧 lint: 緑（{len(rings)}つの輪が、見出し・図・表・実装で一致。"
        "今日の枚は警告しか受け取っていない）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
