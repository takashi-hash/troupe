"""時計の突合 — domain は時計を持たない。

設計: 設計/どう作るか §4「置いてはいけないもの: 時計・乱数・保存・画面・外の道具。
**「いま」は引数で受け取る**」。

依存は**注がれる**——domain が自分で時刻を取りに行った瞬間、
同じ入力で違う答えが出るようになり、検査の「何度でも同じ結果」が崩れる。
import-linter は `datetime` 型そのものは禁じられない（型は要る）ので、
**呼び出しの形**をここで突き合わせる。
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: domain に現れてはいけない呼び出し。時刻を「受け取る」のはよいが「取りに行く」のは赤。
時計を読む形 = re.compile(r"\.now\(|\.today\(|utcnow|time\.time\(|monotonic\(")


def test_domain_は時計を読みに行かない() -> None:
    違反: list[str] = []
    for path in sorted((ROOT / "domain").rglob("*.py")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if 時計を読む形.search(line):
                違反.append(f"{path.relative_to(ROOT)}:{i}: {line.strip()}")
    assert not 違反, "domain が時刻を取りに行っています（いまは引数で受け取る）:\n" + "\n".join(違反)
