"""カスタムの口の実装 — `custom/<題材>/` の TOML を読む。

欄の名は英語（設定ファイルの構造は道具の慣例に従う——読みかた 掟9）。
**中身が現場の言葉**で、土台の型（Board・Definition）への翻訳はここでやる。
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from domain.board import Board, Constitution
from domain.definition import Cadence, Definition, Version
from domain.job import Budget


class TomlCustom:
    """カスタムの口 — `custom/運転/` のような1つの題材のフォルダを読む"""

    def __init__(self, folder: str | Path) -> None:
        self._folder = Path(folder)

    def load(self) -> tuple[Board, tuple[Definition, ...]]:
        """読み込む — 方針と業務ルールを読む。凍結も有効化もされていない形で返す"""
        return self._board(), self._definitions()

    def _board(self) -> Board:
        data = _read(self._folder / "board.toml")
        constitutions = _rows(data, "constitutions")
        return Board(
            board_id=str(data["board_id"]),
            constitutions=tuple(
                Constitution(
                    number=int(str(c["number"])),
                    purpose=str(c["purpose"]),
                    non_goals=str(c["non_goals"]),
                    acceptance=str(c["acceptance"]),
                    vocabulary=str(c["vocabulary"]),
                )
                for c in constitutions
            ),
        )

    def _definitions(self) -> tuple[Definition, ...]:
        found: list[Definition] = []
        for path in sorted((self._folder / "rules").glob("*.toml")):
            data = _read(path)
            found.append(
                Definition(
                    name=str(data["name"]),
                    board_id=str(data["board_id"]),
                    versions=tuple(_version(v) for v in _rows(data, "versions")),
                )
            )
        return tuple(found)


def _version(data: dict[str, object]) -> Version:
    """1つの版を土台の型に翻訳する"""
    cadence: Cadence = "weekly" if str(data["cadence"]) == "weekly" else "monthly"
    return Version(
        number=int(str(data["number"])),
        instruction=str(data["instruction"]),
        acceptance=str(data["acceptance"]),
        cadence=cadence,
        deadline_days=int(str(data["deadline_days"])),
        budget=Budget(
            calls=int(str(data["budget_calls"])), seconds=int(str(data["budget_seconds"]))
        ),
        max_retries=int(str(data.get("max_retries", 3))),
        source_refs=_strings(data, "source_refs"),
        must_contain=_strings(data, "must_contain"),
        checkpoint_position=(
            str(data["checkpoint_position"]) if data.get("checkpoint_position") else None
        ),
        needs_apply=bool(data.get("needs_apply", False)),
    )


def _strings(data: dict[str, object], key: str) -> tuple[str, ...]:
    """文字列の並びを取り出す。無ければ空"""
    values = data.get(key, [])
    return tuple(str(v) for v in values) if isinstance(values, list) else ()


def _rows(data: dict[str, object], key: str) -> list[dict[str, object]]:
    """表の並びを取り出す。形が違えば、その場で分かるように落とす"""
    rows = data.get(key)
    if not isinstance(rows, list):
        raise ValueError(f"{key} が表の並びになっていない")
    return [row for row in rows if isinstance(row, dict)]


def _read(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        return tomllib.load(handle)
