"""構造の名前 lint — 掟9 の執行者（名前の置き場の3つ目の線）。

版に入っているパスのうち、**動く仕組みの構造**は英語でなければならない。
和名が許されるのは2つだけ:

1. 人が読む文書の置き場（`設計/`。掟2）
2. どれを指すかの名（`custom/運転/`・`rules/週次の検査の見張り.toml`）——
   ボードIDや業務ルールの名と同じで、**中身であって構造ではない**

この lint が要る理由: 掟9 のこの一文は一度、書き直しのときに落ちた。
文が消えても検査が残れば、次に破ったとき赤くなる（宣言に執行者を）。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 和名でよい場所（理由つき。ここに足すときは掟9 を読み直すこと）
DOCUMENT_FOLDER = "設計/"  # 掟2: 人が読む文書の置き場
DATA_FOLDERS = ("custom/",)  # どれを指すかの名（題材・業務ルールの名）が並ぶ


def tracked_paths() -> list[str]:
    """版に入っているパスたち"""
    # -z（NUL 区切り）で読む——既定では git が和名をエスケープして返し、
    # ASCII に見えてしまう（この lint が一度、赤くならない偽の執行者になった）
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True
    )
    return [p for p in out.stdout.decode("utf-8").split("\0") if p]


def offending(path: str) -> str | None:
    """構造の名前として和名を使っているところを返す。無ければ None"""
    if path.startswith(DOCUMENT_FOLDER):
        return None  # 人が読む文書の置き場
    parts = path.split("/")
    if path.startswith(DATA_FOLDERS):
        # custom/<題材>/rules/<業務ルールの名>.toml —— 1つ目と最後はデータの名
        structure = parts[2:-1] if len(parts) > 2 else []
    else:
        structure = parts
    for part in structure:
        if not part.isascii():
            return part
    return None


def main() -> int:
    problems = [
        f"{path} の「{part}」——構造の名前は英語（掟9）"
        for path in tracked_paths()
        if (part := offending(path)) is not None
    ]
    if problems:
        print("構造の名前 lint: 赤")
        for problem in problems:
            print(f"  赤 {problem}")
        return 1
    total = len(tracked_paths())
    print(
        f"構造の名前 lint: 緑（版に入っている {total} のパス。"
        "和名でよいのは 設計/ と、custom/ の題材・業務ルールの名だけ）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
