"""置き場 lint — 層割当て表 §5「構成要素の置き場と執行者」の執行者。

この表は「執行者を書け」と言う表なので、**自分の執行者を持っていないと嘘になる**。
確かめるのは2つ:

1. **表が名指す執行者が実在するか**——`tests/…` と書いておいて無い、を赤にする。
   逆向きも見る: `tests/` の lint が全部この表のどこかに現れるか（表に載らない
   執行者は、次に誰かが消したとき誰も気づかない）
2. **DomainService が集約の数を超えていないか**——超えたら、置き場に迷ったものを
   そこへ捨てている合図（集約が痩せ、サービスが太る）

DomainService の見分けは形で決める: **引数に集約が2つ以上出てきて、返り値が
そのどれでもない**関数。1つしか出てこないならその集約の引きであり、
返り値がそれならその集約の中の話。どちらでもないから「持ち主のない規則」になる。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "設計" / "7_配置" / "層割当て表.md"
AGGREGATES = ROOT / "設計" / "4_集約" / "集約境界図.md"

# 集約とその部品。ここに載る型が引数に何種類出るかで、持ち主の有無を測る
AGGREGATE_TYPES = {
    "Job",
    "Definition",
    "Version",
    "Board",
    "Constitution",
    "Participant",
    "Proposal",
    "SourceRegistration",
}


def section_five() -> str:
    """層割当て表 §5 の本文"""
    text = TABLE.read_text(encoding="utf-8")
    start = text.index("## 5. 構成要素の置き場と執行者")
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def aggregate_count() -> int:
    """集約境界図 §3 が並べる集約の数——数える場所は1つ"""
    text = AGGREGATES.read_text(encoding="utf-8")
    start = text.index("## 3. 各 Aggregate の中身")
    end = text.find("\n## ", start + 1)
    return len(re.findall(r"^\| \*\*[A-Za-z]+\*\*", text[start:end], re.MULTILINE))


def domain_services() -> list[str]:
    """持ち主のない規則——引数に集約が2つ以上、返り値はそのどれでもない"""
    found: list[str] = []
    for path in sorted((ROOT / "domain").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            params = " ".join(
                ast.unparse(arg.annotation) for arg in node.args.args if arg.annotation
            )
            returns = ast.unparse(node.returns) if node.returns else ""
            mentioned = {t for t in AGGREGATE_TYPES if re.search(rf"\b{t}\b", params)}
            if len(mentioned) >= 2 and not any(
                re.search(rf"\b{t}\b", returns) for t in mentioned
            ):
                found.append(f"{path.name}:{node.name}")
    return found


def main() -> int:
    body = section_five()
    problems: list[str] = []

    named = {m for m in re.findall(r"`(tests/[A-Za-z_]+\.py)`", body)}
    for name in sorted(named):
        if not (ROOT / name).exists():
            problems.append(f"表が名指す執行者 {name} が無い")

    for path in sorted((ROOT / "tests").glob("*_lint.py")):
        if f"`tests/{path.name}`" not in body:
            problems.append(f"tests/{path.name} が表に載っていない——消えても誰も気づかない")

    services = domain_services()
    limit = aggregate_count()
    if len(services) > limit:
        problems.append(
            f"DomainService が {len(services)} で集約 {limit} を超えた: {services}"
            "——置き場に迷ったものを捨てていないか。主語になれる集約を先に探す"
        )

    if problems:
        print("置き場 lint: 赤")
        for problem in problems:
            print(f"  赤 {problem}")
        return 1
    print(
        f"置き場 lint: 緑（表が名指す執行者 {len(named)} 個は実在し、"
        f"tests の lint は全部表に載っている。DomainService {len(services)} ≦ 集約 {limit}）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
