"""壊して赤を見る。

掟7 — 仕掛けは「壊して赤を見た」まで書いて完成。
前の一座は、壊しても緑のままの仕掛けが2つあった（失敗#10 仕掛けが嘘をついた）。

義務を1つずつ外して pytest を回し、**必ず赤になる**ことを確かめる。
赤にならなかった義務は、書いてあるだけで誰も守っていない。

    uv run python tests/break_check.py
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import time

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
    ("domain/values.py", "書き換えられない", 'frozen=True', 'frozen=False'),
    ("domain/values.py", "知らない欄を拒む", 'extra="forbid"', 'extra="ignore"'),
    # 禁止状態（型が作らせない）
    ("domain/lifecycle.py", "実行中は担当を必ず持つ", "    assignee: Assignee\n\n\nclass AwaitingAnswer", "    assignee: Assignee | None = None\n\n\nclass AwaitingAnswer"),
    ("domain/lifecycle.py", "承認済みは承認を必ず持つ", "    approval: Approval\n\n\nclass Failed", "    approval: Approval | None = None\n\n\nclass Failed"),
    ("domain/lifecycle.py", "承認待ちの担当は受け持ちの人", "    assignee: Owner", "    assignee: Owner | Agent"),
    ("domain/lifecycle.py", "着手できるは承認を持てない", 'name: Literal["Ready"] = "Ready"', 'name: Literal["Ready"] = "Ready"\n    approval: Approval | None = None'),
    ("domain/lifecycle.py", "打ち切りは理由を必ず持つ", "    by: Human\n    reason: str", "    by: Human\n    reason: str = \"\""),
    # 突合（設計の表と実物が一致しているか）— **コード側を壊す**
    ("domain/lifecycle.py", "遷移表から1行落とす", '("Cleared", "Finished", "confirm", ("JobFinished",), "時計"),', ""),
    ("domain/lifecycle.py", "遷移の出来事を差し替える", '("AwaitingApproval", "Cleared", "approve", ("Approved",), "人")', '("AwaitingApproval", "Cleared", "approve", ("JobFinished",), "人")'),
    ("domain/lifecycle.py", "人しか起こせない操作を AI に渡す", '    "承認": "approve",\n', ""),
    ("domain/lifecycle.py", "人しか起こせない操作を1つ増やす", '    "打ち切り": "abandon",\n', '    "打ち切り": "abandon",\n    "着手": "start",\n'),
    ("domain/events.py", "出来事を1つ落とす", "class RecheckDatePushed(Event):", "class _RecheckDatePushed(Event):"),
    ("domain/events.py", "遷移表の外に4つ目を許す", '{"DueDatePassed", "SpentIncreased", "AssessmentWritten"}', '{"DueDatePassed", "SpentIncreased", "AssessmentWritten", "JobFinished"}'),
    # 突合が**設計を読んでいる**ことの証明——設計の .md を壊すと赤になるか
    ("設計/仕事とは何か.md", "設計の遷移表を1行変える", "| 承認待ち | 承認済み | 承認する `approve` | `Approved` | **人**（受け持ちの人） |", "| 承認待ち | 承認済み | 承認する `approve` | `Approved` | 時計 |"),
    ("設計/仕事とは何か.md", "設計の状態を1つ消す", "| **打ち切られた** `Abandoned` |", "| 打ち切られた |"),
    ("設計/仕事が回る筋道.md", "設計の出来事を1つ消す", "| 確かめ期日が先へ送られた | 新しい確かめ期日 | `RecheckDatePushed` |\n", ""),
]


# 壊した版の .pyc を残さない。`"forbid"` と `"ignore"` のように**同じ長さ**へ
# 書き換えると、Python の無効化（mtime＋サイズ）をすり抜けて、
# 壊れたバイトコードが次のふつうの試験まで生き延びる。実際に一度そうなった。
ENV = os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}


def _pytest() -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["uv", "run", "pytest", "-q"], cwd=ROOT, capture_output=True, env=ENV)


def main() -> int:
    green = _pytest()
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
            run = _pytest()
        finally:
            path.write_text(original, encoding="utf-8")
            os.utime(path, (time.time() + 1, time.time() + 1))  # 念のため mtime を進める
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
