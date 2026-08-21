"""源の口の実装 — 読むだけ。書き口とは別物として隔離する。

土台が持つのは**読み方の型**（ファイル・コマンド）だけ。
**どの源をどう読むかの対応表はカスタムのデータ**（`custom/<題材>/sources.toml`）——
土台は「検査の結果」も「依存の一覧」も知らない。
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

MAX_QUOTE = 4000  # 引用は人が読める長さで切る（後から確かめられればよい）


class FileSource:
    """ファイルの源 — 1つのファイル、またはフォルダの中の名前たちを読む"""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def read(self) -> str:
        """源を読む — 読めなければ例外（働き手が環境エラーに落とす）"""
        if self._path.is_dir():
            names = sorted(p.name for p in self._path.rglob("*") if p.is_file())
            return "\n".join(names)[:MAX_QUOTE]
        return self._path.read_text(encoding="utf-8")[:MAX_QUOTE]


class CommandSource:
    """コマンドの源 — 走らせて、その出力を読む（検査の結果など）"""

    def __init__(self, command: str, timeout: int = 300) -> None:
        self._command = command
        self._timeout = timeout

    def read(self) -> str:
        """源を読む — 走らせて出力を返す。時間切れや失敗も、そのまま読んだ中身にする"""
        done = subprocess.run(
            self._command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=self._timeout,
            cwd=Path(__file__).resolve().parent.parent,
        )
        head = f"（終了コード {done.returncode}）\n"
        return (head + done.stdout + done.stderr)[-MAX_QUOTE:]


def sources_of(folder: str | Path) -> dict[str, FileSource | CommandSource]:
    """源の対応表を読む — カスタムのデータから、源の参照と読み方の対を作る"""
    path = Path(folder) / "sources.toml"
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    found: dict[str, FileSource | CommandSource] = {}
    rows = data.get("sources", [])
    if not isinstance(rows, list):
        return found
    for row in rows:
        if not isinstance(row, dict):
            continue
        ref = str(row["ref"])
        if str(row["kind"]) == "command":
            found[ref] = CommandSource(str(row["command"]))
        else:
            found[ref] = FileSource(str(row["path"]))
    return found
