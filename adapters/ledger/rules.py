"""業務ルールの帳簿 — `RuleRepository` の SQLite 実装。

設計: 設計/仕事が回る筋道.md §4、不変条件 I2。
**版の追加と出来事を同じトランザクションで積む**（I2）。版が減った姿は
書く前に前の版列と突き合わせて拒む——「版は積むだけ」。
"""

from __future__ import annotations

import json

from adapters.ledger.db import Ledger
from domain.aggregates.rule.rule import Rule
from domain.events.event import Event
from domain.value_objects.rule.rule_name import RuleName


class SqliteRules:
    def __init__(self, conn: Ledger) -> None:
        self._conn = conn
        self._seen: dict[str, int] = {}

    def load(self, name: RuleName) -> Rule | None:
        row = self._conn.execute(
            "SELECT revision, body FROM rules WHERE name = ?", (name.text,)
        ).fetchone()
        if row is None:
            return None
        self._seen[name.text] = int(row[0])
        return Rule.model_validate_json(row[1])

    def save(self, rule: Rule, events: tuple[Event, ...]) -> None:
        if not events:
            raise ValueError("出来事なしで版は書けません（I2）")
        cur = self._conn
        try:
            cur.execute("BEGIN IMMEDIATE")
            known = self._seen.get(rule.name.text)
            row = cur.execute(
                "SELECT revision, body FROM rules WHERE name = ?", (rule.name.text,)
            ).fetchone()
            if row is not None:
                if known != int(row[0]):
                    raise RuntimeError("帳簿が先に進んでいます。読み直してください")
                前の版列 = [v["number"] for v in json.loads(row[1])["versions"]]
                今の版列 = [v.number for v in rule.versions]
                if 今の版列[: len(前の版列)] != 前の版列:
                    raise ValueError("版が減っています（I2——版は積むだけ）")
                cur.execute(
                    "UPDATE rules SET revision = revision + 1, body = ? WHERE name = ?",
                    (rule.model_dump_json(), rule.name.text),
                )
            else:
                cur.execute(
                    "INSERT INTO rules(name, revision, body) VALUES (?, 1, ?)",
                    (rule.name.text, rule.model_dump_json()),
                )
            seq = cur.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM rule_events WHERE rule_name = ?",
                (rule.name.text,),
            ).fetchone()[0]
            for i, event in enumerate(events, start=1):
                cur.execute(
                    "INSERT INTO rule_events(rule_name, seq, name, at, by_kind, by_name, body)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        rule.name.text,
                        seq + i,
                        type(event).__name__,
                        event.at.isoformat(),
                        event.by.kind,
                        getattr(event.by, "name", None),
                        event.model_dump_json(),
                    ),
                )
            cur.execute("COMMIT")
        except BaseException:
            if cur.in_transaction:
                cur.execute("ROLLBACK")
            raise
        self._seen[rule.name.text] = (self._seen.get(rule.name.text) or 0) + 1
