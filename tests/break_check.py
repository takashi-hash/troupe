"""壊して赤を見る。

掟7 — 仕掛けは「壊して赤を見た」まで書いて完成。
前の一座は、壊しても緑のままの仕掛けが2つあった（失敗#10 仕掛けが嘘をついた）。

義務を1つずつ外して pytest を回し、**必ず赤になる**ことを確かめる。
赤にならなかった義務は、書いてあるだけで誰も守っていない。

    uv run python tests/break_check.py
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (どのファイル, 何という義務を, どう壊すか)
BREAKS: list[tuple[str, str, str, str]] = [
    ("domain/values.py", "空でない（共通）", 'if not text.strip():', "if False:"),
    ("domain/values.py", "仕事の識別子の前後の空白", "if self.text != self.text.strip():", "if False:"),
    ("domain/values.py", "受け持ちの人は人だけ", "person: Human", "person: Human | Agent"),
    ("domain/values.py", "期日は起点より後", "if self.at <= self.start:", "if False:"),
    ("domain/values.py", "確かめ期日は期日より後", "if self.at <= self.after:", "if False:"),
    ("domain/values.py", "使用上限は1以上", "if self.calls < 1 or self.seconds < 1:", "if False:"),
    ("domain/values.py", "使った量は0以上", "if self.calls < 0 or self.seconds < 0:", "if False:"),
    ("domain/values.py", "対象期間の形", "if not (_MONTHLY.match(self.text) or _WEEKLY.match(self.text)):", "if False:"),
    ("domain/values.py", "必ず含む語は空でない", "if not self.must_contain or any(not w.strip() for w in self.must_contain):", "if False:"),
    ("domain/values.py", "差し込みを開く", 'w.replace(PERIOD_SLOT, period.text)', "w"),
    ("domain/values.py", "作成元は版の番号で分かれる", 'f"rule:{rule.text}:v{version}:{period.text}"', 'f"rule:{rule.text}:{period.text}"'),
    ("domain/values.py", "確かめ期日は送るたびに進む", "at=self.at + cycle.span", "at=self.at"),
    ("domain/values.py", "上限で止まる", "self.calls <= budget.calls and self.seconds <= budget.seconds", "True"),
    ("domain/values.py", "版の番号は1以上", "if self.number < 1:", "if False:"),
    ("domain/values.py", "日数は1以上", "if self.days < 1:", "if False:"),
    ("domain/values.py", "書き換えられない", '"frozen": True', '"frozen": False'),
    ("domain/values.py", "知らない欄を拒む", '"extra": "forbid"', '"extra": "ignore"'),
]


def main() -> int:
    green = subprocess.run(["uv", "run", "pytest", "-q"], cwd=ROOT, capture_output=True)
    if green.returncode != 0:
        print("壊す前から赤です。先に緑にしてください。")
        print(green.stdout.decode()[-2000:])
        return 1

    lied: list[str] = []
    for rel, name, old, new in BREAKS:
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        if original.count(old) != 1:
            lied.append(f"{name} — 壊す場所が {original.count(old)} 箇所（1つでない）")
            continue
        try:
            path.write_text(original.replace(old, new), encoding="utf-8")
            run = subprocess.run(["uv", "run", "pytest", "-q"], cwd=ROOT, capture_output=True)
        finally:
            path.write_text(original, encoding="utf-8")
        mark = "赤" if run.returncode != 0 else "緑のまま"
        print(f"  {mark}  {name}")
        if run.returncode == 0:
            lied.append(f"{name} — 壊しても緑。この義務は誰も守っていない")

    print()
    if lied:
        print(f"仕掛けが嘘をついています（{len(lied)}件）:")
        for line in lied:
            print(f"  - {line}")
        return 1
    print(f"{len(BREAKS)}個の義務、全部が壊すと赤になりました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
