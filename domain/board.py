"""ボード — 帳簿の区画。1つの方針を持つ。

方針が Human に freeze されるまで、下流の Job は dispatch されない（Gate）。
方針の「言葉」が現場の言葉の注入口（入れ子の要）。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

_frozen_config = ConfigDict(frozen=True, extra="forbid")


class Constitution(BaseModel):
    """方針 — ボードの土台。目的・非目標・受け入れ基準・言葉。積むだけで消えない"""

    model_config = _frozen_config
    number: int
    purpose: str  # 目的
    non_goals: str  # 非目標
    acceptance: str  # 受け入れ基準
    vocabulary: str  # 言葉（現場の言葉——注入されるもの）


class Board(BaseModel):
    """ボード — frozen が None のあいだ Gate は閉じている（dispatch されない）"""

    model_config = _frozen_config
    board_id: str
    constitutions: tuple[Constitution, ...]
    frozen: int | None = None  # freeze されている方針の number。するのは Human だけ


class CannotFreeze(Exception):
    """凍結できない — 存在しない方針は freeze できない"""


def freeze(board: Board, number: int) -> Board:
    """凍結する — Human だけの行為。誰が freeze したかは ConstitutionFrozen の Event が持つ"""
    if not any(c.number == number for c in board.constitutions):
        raise CannotFreeze(f"方針 {number} は {board.board_id} に無い")
    return board.model_copy(update={"frozen": number})


def board_required_events(old: Board | None, new: Board) -> frozenset[str]:
    """ボードの必須出来事 — 書き込みの変化から必須 Event を導く（ボードの門）"""
    from domain.definition import AppendOnlyViolation

    old_constitutions: tuple[Constitution, ...] = old.constitutions if old else ()
    if new.constitutions[: len(old_constitutions)] != old_constitutions:
        raise AppendOnlyViolation(f"{new.board_id}: 方針は積むだけ——減らせない・書き換えられない")
    if new.frozen is not None and not any(c.number == new.frozen for c in new.constitutions):
        raise CannotFreeze(f"{new.board_id}: 方針 {new.frozen} は無い")
    required: set[str] = set()
    if len(new.constitutions) > len(old_constitutions):
        required.add("ConstitutionAppended")
    old_frozen = old.frozen if old else None
    if old_frozen != new.frozen:
        required.add("ConstitutionFrozen" if new.frozen is not None else "ConstitutionUnfrozen")
    return frozenset(required)


def gate_open(board: Board) -> bool:
    """関門が開いているか — 方針が人に凍結されるまで、下流のタスクは配られない（不変条件）"""
    return board.frozen is not None


def constitution_ref(board: Board) -> str:
    """方針の参照 — 凍結された方針を指す。参照の形式はドメインが持つ（外で組み立てない）"""
    if board.frozen is None:
        raise CannotFreeze(f"{board.board_id}: 凍結されていない方針は参照できない")
    return f"{board.board_id}/方針/{board.frozen}"
