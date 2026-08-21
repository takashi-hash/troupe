"""出来事の名前 lint — 用語集 §12 とコードの EventKind が一致しているかを見張る。

出来事カタログに在る名前がコードに無ければ書けないし、コードにあって用語集に無ければ
勝手訳になる。用語集が正本（読みかた 掟9）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def glossary_kinds() -> list[str]:
    """用語集 §12 の識別子を順に読む"""
    section = (ROOT / "設計" / "1_言葉" / "用語集.md").read_text(encoding="utf-8").split("## 12.")[1]
    kinds: list[str] = []
    for line in section.splitlines():
        matched = re.match(r"^\|\s*([^|]+?)\s*\|\s*([A-Za-z]+)\s*\|", line)
        if matched and matched.group(2) != "識別子":
            kinds.append(matched.group(2))
    return kinds


def code_kinds() -> list[str]:
    """domain/event.py の EventKind に並ぶ名前を読む"""
    text = (ROOT / "domain" / "event.py").read_text(encoding="utf-8")
    body = text.split("EventKind = Literal[")[1].split("]")[0]
    return re.findall(r'"([A-Za-z]+)"', body)


def main() -> int:
    in_glossary, in_code = glossary_kinds(), code_kinds()
    missing = [k for k in in_glossary if k not in in_code]
    extra = [k for k in in_code if k not in in_glossary]
    if missing or extra:
        print("出来事の名前 lint: 赤")
        for kind in missing:
            print(f"  赤 用語集 §12 の「{kind}」が domain/event.py の EventKind に無い")
        for kind in extra:
            print(f"  赤 EventKind の「{kind}」が用語集 §12 に無い——先に用語集へ")
        return 1
    print(f"出来事の名前 lint: 緑（{len(in_code)} 種が用語集 §12 と一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
