"""突合 — 設計の遷移表と、操作の型注釈を1行ずつ照合する。

正本は設計（設計/仕事とは何か.md §6）。実物は署名——
**「から」が引数の型、「へ」が返りの型、出来事が返りのタプル、誰がが引数の型**。
遷移表をコードに書き写さない（掟3——数える場所は正本を1つ）。

誰がの照合は「人か、人でないか」だけを見る。人しか起こせない操作（I7）は
署名に `Human`（か、人を運ぶ値）が必ず居て、それ以外の操作には居ない。
AI と時計の区別は署名に出ないことがある（担当は状態が持つ・時計は引数に取らない）ので、
そこは操作ごとのテストが出来事の `by` で確かめる。
"""

from __future__ import annotations

import importlib
import inspect
import pathlib
import re
import types
import typing
from typing import get_args, get_origin, get_overloads, get_type_hints

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import STATE_WORDS
from domain.value_objects.job.answer import Answer
from domain.value_objects.job.request import Request
from domain.value_objects.job.send_back import SendBack
from domain.value_objects.people.human import Human

ROOT = pathlib.Path(__file__).resolve().parent.parent
設計 = ROOT / "設計"
操作の棚 = ROOT / "domain" / "aggregates" / "job"

#: 人を運ぶ型。署名にこれが居たら、その操作は人が起こす。
人を運ぶ = (Human, SendBack, Answer, Request)

#: 遷移表の外で状態を変えずに刻む操作（設計 §6「例外は3つだけ」の隣人）。
例外の操作 = {"assess", "spend", "mark_overdue"}


# ---------- 設計側 ----------


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _plain(cell: str) -> str:
    return re.sub(r"（[^）]*）\s*$", "", cell.replace("**", "")).strip()


def _state(cell: str) -> str:
    bare = cell.replace("**", "").strip()
    return STATE_WORDS[bare] if bare in STATE_WORDS else STATE_WORDS[_plain(cell)]


行 = tuple[str | None, str, str, tuple[str, ...], str]


def 設計の行() -> set[行]:
    doc = (設計 / "仕事とは何か.md").read_text(encoding="utf-8")
    body = doc.split("### 遷移", 1)[1].split("### 姿は変わるが", 1)[0]
    rows: set[行] = set()
    for line in body.splitlines():
        cells = _cells(line)
        if len(cells) != 5 or cells[0] in ("から", "---") or set(cells[0]) <= {"-"}:
            continue
        frm = None if "無い" in cells[0] else _state(cells[0])
        op = re.findall(r"`([a-z_]+)`", cells[2])
        assert len(op) == 1, f"操作が1つでない行: {line}"
        events = tuple(re.findall(r"`([A-Z][A-Za-z]+)`", cells[3]))
        actor = "人" if _plain(cells[4]) == "人" else "人でない"
        rows.add((frm, _state(cells[1]), op[0], events, actor))
    assert rows, "設計から遷移が1行も読めませんでした"
    return rows


# ---------- 実物側 ----------


def _union(tp: object) -> tuple[object, ...]:
    if get_origin(tp) in (types.UnionType, typing.Union):
        return get_args(tp)
    return (tp,)


def _job_state(tp: object) -> str | None:
    # pydantic の generic は実クラスを作るので、typing 側と pydantic 側の両方を見る
    meta = getattr(tp, "__pydantic_generic_metadata__", None)
    if meta and meta["origin"] is Job:
        (arg,) = meta["args"]
        return getattr(arg, "__name__", str(arg))
    if get_origin(tp) is Job:
        (arg,) = get_args(tp)
        return getattr(arg, "__name__", str(arg))
    return None


def _操作の名() -> list[str]:
    return sorted(
        p.stem for p in 操作の棚.glob("*.py") if p.stem not in ("__init__", "job", "life")
    )


def _署名の行(op: str) -> set[行]:
    mod = importlib.import_module(f"domain.aggregates.job.{op}")
    fn = getattr(mod, op)
    rows: set[行] = set()
    for sig in get_overloads(fn) or [fn]:
        hints = get_type_hints(sig)
        params = list(inspect.signature(sig).parameters)
        froms = {
            st
            for tp in _union(hints.get(params[0]))
            if (st := _job_state(tp)) is not None
        } or {None}
        actor = (
            "人"
            if any(
                t in 人を運ぶ for name in params for t in _union(hints.get(name))
            )
            else "人でない"
        )
        for alt in _union(hints["return"]):
            if alt is type(None):
                continue
            if get_origin(alt) is tuple:
                args = get_args(alt)
                to = _job_state(args[0])
                events = tuple(getattr(a, "__name__", "?") for a in args[1:])
                assert to is not None and events, f"{op} の返りが（次の姿, 出来事…）の対でない"
                for frm in froms:
                    rows.add((frm, to, op, events, actor))
    return rows


# ---------- 突合 ----------


def test_遷移表と操作の署名が1行ずつ一致する() -> None:
    実物: set[行] = set()
    for op in _操作の名():
        if op in 例外の操作:
            continue
        実物 |= _署名の行(op)
    設計側 = 設計の行()
    assert 実物 == 設計側, (
        f"設計にあって署名に無い: {sorted(設計側 - 実物, key=str)}\n"
        f"署名にあって設計に無い: {sorted(実物 - 設計側, key=str)}"
    )


def test_遷移表の外で刻める操作は3つの例外だけ() -> None:
    """設計 §6 — 例外は3つだけ。操作は状態を変えず、その出来事しか刻まない。"""
    doc = (設計 / "仕事とは何か.md").read_text(encoding="utf-8")
    例外行 = next(ln for ln in doc.splitlines() if "例外は3つだけ" in ln)
    許された出来事 = set(re.findall(r"`([A-Z][A-Za-z]+)`", 例外行))
    表の外 = set(_操作の名()) - {op for (_, _, op, _, _) in 設計の行()}
    assert 表の外 == 例外の操作, f"遷移表にも例外にも無い操作: {表の外 ^ 例外の操作}"
    for op in 例外の操作:
        for frm, to, _, events, _ in _署名の行(op):
            assert frm == to, f"{op} が状態を変えている（{frm}→{to}）"
            assert set(events) <= 許された出来事, f"{op} が {events} を刻んでいる"


def test_人しか起こせない出来事は_by_の型が人() -> None:
    """太字（人が主語）が型になっているか。人だけが残す出来事は AI や時計を運べない。"""
    誰が: dict[str, set[str]] = {}
    for _, _, _, events, actor in 設計の行():
        for ev in events:
            誰が.setdefault(ev, set()).add(actor)
    import domain.events.job as 出来事の棚

    for ev, actors in 誰が.items():
        if actors != {"人"}:
            continue
        mod = importlib.import_module(
            "domain.events.job." + re.sub(r"(?<!^)([A-Z])", r"_\1", ev).lower()
        )
        assert get_type_hints(getattr(mod, ev))["by"] is Human, (
            f"{ev} は人しか残さないのに、by の型が Human でない"
        )
