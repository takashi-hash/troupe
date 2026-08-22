"""壊して赤を見る。

掟7 — 仕掛けは「壊して赤を見た」まで書いて完成。
前の一座は、壊しても緑のままの仕掛けが2つあった（失敗#10 仕掛けが嘘をついた）。

**義務を1つずつ外して試験を回し、必ず赤になることを確かめる。**
赤にならなかった義務は、書いてあるだけで誰も守っていない。
テストを書いたのは値を書いた本人なので、盲点は共有されている——それを機械で暴く。

    uv run python tests/break_check.py

**壊しかたは手で並べない。** 並べると、新しい義務を足したとき並べ忘れる。
domain の中の**守り**をすべて自分で見つけて、1つずつ外す。
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "bin" / "python"

# 壊した版の .pyc を残さない。同じ長さへ書き換えると Python の無効化
# （mtime＋サイズ）をすり抜け、壊れたバイトコードが次のふつうの試験まで生き延びる。
ENV = os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}

#: domain の中の「守り」の見つけかた。(見出し, 見つける正規表現, 外しかた)
GUARDS: list[tuple[str, re.Pattern[str], str]] = [
    ("義務を投げる", re.compile(r"^(\s*)raise ValueError\(.*\)\s*$"), r"\1pass"),
    ("空でないと言う", re.compile(r"^(\s*)not_blank\(.*\)\s*$"), r"\1pass"),
    ("書き換えられない", re.compile(r"^(.*)frozen=True(.*)$"), r"\1frozen=False\2"),
    ("知らない欄を拒む", re.compile(r'^(.*)extra="forbid"(.*)$'), r'\1extra="ignore"\2'),
    ("3つ目を拒む", re.compile(r'^(.*), Field\(discriminator="kind"\)(.*)$'), r"\1\2"),
    (
        "同じ辞書の鍵になる",
        re.compile(r"^(\s*)return hash\(\(type\(self\).*\)\s*$"),
        r"\1return id(self)",
    ),
]


def _green() -> bool:
    return subprocess.run(
        [str(PY), "-m", "pytest", "-q", "-x"], cwd=ROOT, capture_output=True, env=ENV
    ).returncode == 0


def _guards() -> list[tuple[pathlib.Path, int, str, str]]:
    """domain の中の守りを、すべて自分で見つける。"""
    found: list[tuple[pathlib.Path, int, str, str]] = []
    for path in sorted((ROOT / "domain").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            # **1行に守りが2つ**あることがある（`ConfigDict(frozen=..., extra=...)`）。
            # 見つけた時点で打ち切ると、片方を一度も外さないまま緑で終わる。
            for label, pattern, replace in GUARDS:
                if pattern.match(line):
                    found.append((path, i, label, pattern.sub(replace, line)))
    return found


def main() -> int:
    if not _green():
        print("壊す前から赤です。先に緑にしてください。")
        return 1

    guards = _guards()
    print(f"domain の中に守りが {len(guards)} 個。1つずつ外します。\n")

    lied: list[str] = []
    last = ""
    for path, i, label, broken in guards:
        rel = path.relative_to(ROOT)
        if str(rel) != last:
            print(f"  {rel}")
            last = str(rel)
        original = path.read_text(encoding="utf-8")
        lines = original.splitlines(keepends=True)
        end = "\n" if lines[i].endswith("\n") else ""
        try:
            lines[i] = broken + end
            path.write_text("".join(lines), encoding="utf-8")
            green = _green()
        finally:
            path.write_text(original, encoding="utf-8")
            os.utime(path, (time.time() + 1, time.time() + 1))
        print(f"    {'緑のまま' if green else '赤    '}  {label}（{i + 1}行目）")
        if green:
            lied.append(f"{rel}:{i + 1} {label} — 外しても緑。この義務は誰も守っていない")

    print()
    if lied:
        print(f"仕掛けが嘘をついています（{len(lied)}件）:")
        for line in lied:
            print(f"  - {line}")
        return 1
    print(f"{len(guards)} 個の守り、全部が外すと赤になりました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
