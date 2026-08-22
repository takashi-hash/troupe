"""状態と遷移の仕掛け。

設計: 設計/仕事とは何か.md §6・設計/仕事が回る筋道.md §5。

種類は2つ（設計/どう作るか §6）:
  **突合** — 設計の表と実物が一致しているか。**設計とコードが離れないための唯一の仕掛け。**
  **型**   — 禁止状態が書けない。
"""

from __future__ import annotations

import pathlib
import re

import pytest
from pydantic import TypeAdapter, ValidationError

from domain import events as ev
from domain.lifecycle import (
    HUMAN_ONLY,
    HUMAN_ONLY_BY_WORD,
    STATE_NAMES,
    TERMINAL,
    TRANSITIONS,
    Abandoned,
    AwaitingAnswer,
    AwaitingApproval,
    Cleared,
    Created,
    Failed,
    Finished,
    FinishedPendingRecheck,
    InProgress,
    Ready,
    State,
    Submitted,
)
from domain.values import Agent, Approval, Human, Owner
from tests.test_values import ALICE, T0

設計 = pathlib.Path(__file__).resolve().parent.parent / "設計"

# 誰がの欄に出る呼びかたを、`Actor` の3つへ寄せる。
# 「担当」「取ろうとする AI」は、実行中の担当＝AI なので AI（設計 §6 の start の行）。
ACTORS = {"人": "人", "時計": "時計", "AI": "AI", "担当": "AI", "取ろうとする AI": "AI"}


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _plain(cell: str) -> str:
    """太字と、後ろの括弧書きを落として、素の語にする。"""
    return re.sub(r"（[^）]*）\s*$", "", cell.replace("**", "")).strip()


def _state(cell: str) -> str:
    """状態の欄を識別子へ。**「終わった（確かめ待ち）」は括弧ごと1つの状態名**——
    括弧書きを先に落とすと「終わった」に化ける。突合がそれを見つけた。"""
    bare = cell.replace("**", "").strip()
    return STATE_NAMES[bare] if bare in STATE_NAMES else STATE_NAMES[_plain(cell)]


def _section(doc: str, start: str, end: str) -> str:
    return doc.split(start, 1)[1].split(end, 1)[0]


def _design_transitions() -> set[tuple[str | None, str, str, tuple[str, ...], str]]:
    doc = (設計 / "仕事とは何か.md").read_text(encoding="utf-8")
    rows: set[tuple[str | None, str, str, tuple[str, ...], str]] = set()
    for line in _section(doc, "### 遷移", "### 姿は変わるが").splitlines():
        cells = _cells(line)
        if len(cells) != 5 or cells[0] in ("から", "---") or set(cells[0]) <= {"-"}:
            continue
        frm = None if "無い" in cells[0] else _state(cells[0])
        op = re.findall(r"`([a-z_]+)`", cells[2])
        assert len(op) == 1, f"操作が1つでない行: {line}"
        rows.add(
            (
                frm,
                _state(cells[1]),
                op[0],
                tuple(re.findall(r"`([A-Z][A-Za-z]+)`", cells[3])),
                ACTORS[_plain(cells[4])],
            )
        )
    return rows


# ── 突合 — 設計の表と実物が一致しているか ────────────────────


def test_遷移表が設計と1行ずつ一致する() -> None:
    実物 = {(t.frm, t.to, t.operation, t.events, t.actor) for t in TRANSITIONS}
    設計側 = _design_transitions()
    assert 設計側, "設計から遷移が1行も読めませんでした"
    assert 実物 == 設計側, (
        f"設計にあってコードに無い: {sorted(設計側 - 実物)}\n"
        f"コードにあって設計に無い: {sorted(実物 - 設計側)}"
    )


def test_状態の一覧が設計と一致する() -> None:
    doc = (設計 / "仕事とは何か.md").read_text(encoding="utf-8")
    設計側 = set(re.findall(r"\*\*[^*]+\*\* `([A-Z][A-Za-z]+)`", _section(doc, "### 状態", "### 遷移")))
    assert 設計側 == set(STATE_NAMES.values())


def test_出来事の一覧が設計と一致する() -> None:
    doc = (設計 / "仕事が回る筋道.md").read_text(encoding="utf-8")
    設計側 = {
        _cells(line)[2].strip("`")
        for line in _section(doc, "## 5. ドメインイベント", "## 6").splitlines()
        if len(_cells(line)) == 3 and _cells(line)[2].startswith("`")
    }
    実物 = {
        n
        for n, o in vars(ev).items()
        if isinstance(o, type) and issubclass(o, ev.Event) and o is not ev.Event
    }
    assert 設計側 == 実物, f"設計だけ: {設計側 - 実物}／コードだけ: {実物 - 設計側}"


def test_遷移表の外で刻めるのは3つだけ() -> None:
    """設計 §6 — 例外は3つだけ。4つ目を遷移表の外で刻めたら赤。"""
    表の中 = {e for t in TRANSITIONS for e in t.events}
    表の外 = {
        n
        for n, o in vars(ev).items()
        if isinstance(o, type) and issubclass(o, ev.Event) and o is not ev.Event
    } - 表の中
    仕事以外 = {"RuleVersionAdded", "RuleActivated"}  # 業務ルールの集約の出来事
    はみ出し = 表の外 - 仕事以外 - set(ev.OUTSIDE_TRANSITIONS)
    assert not はみ出し, f"遷移表にも例外3つにも無い出来事: {はみ出し}"

    doc = (設計 / "仕事とは何か.md").read_text(encoding="utf-8")
    行 = next(ln for ln in doc.splitlines() if "例外は3つだけ" in ln)
    assert set(re.findall(r"`([A-Z][A-Za-z]+)`", 行)) == set(ev.OUTSIDE_TRANSITIONS)


def test_人しか起こせない操作が公理の5つと一致する() -> None:
    """I7 — 公理の執行者。**日本語の正本は設計の公理の1行だけ**（掟3）。"""
    doc = (設計 / "仕事とは何か.md").read_text(encoding="utf-8")
    公理 = next(ln for ln in doc.splitlines() if "しか起こせない" in ln)
    設計側 = set(公理.split("の5つは")[0].replace("**", "").strip().split("・"))
    assert 設計側 == set(HUMAN_ONLY_BY_WORD), (
        f"設計だけ: {設計側 - set(HUMAN_ONLY_BY_WORD)}／"
        f"コードだけ: {set(HUMAN_ONLY_BY_WORD) - 設計側}"
    )


def test_人しか起こせない操作は遷移表でも人() -> None:
    """両向きに見る。片向きだけだと、一覧から `approve` を抜いても緑のままだった。"""
    人の操作 = {t.operation for t in TRANSITIONS if t.actor == "人"}
    for op in HUMAN_ONLY - {"activate"}:  # `activate` は業務ルールの集約の操作
        assert op in 人の操作, f"{op} が遷移表で人になっていない"
    for t in TRANSITIONS:
        if t.operation in HUMAN_ONLY:
            assert t.actor == "人", f"{t.operation} を {t.actor} が起こせてしまう"


def test_終点から出る遷移が無い() -> None:
    assert TERMINAL == {"Finished", "Abandoned"}
    assert not [t for t in TRANSITIONS if t.frm in TERMINAL]


def test_どの状態にも入る道がある() -> None:
    届く = {t.to for t in TRANSITIONS}
    assert 届く == set(STATE_NAMES.values()) - {"Created"} | {"Created"}


# ── 型 — 禁止状態が書けない（設計 §7）─────────────────────


def _approval() -> Approval:
    return Approval(by=ALICE, at=T0)


def test_承認なしの承認済みが書けない() -> None:
    with pytest.raises(ValidationError):
        Cleared()  # type: ignore[call-arg]


def test_担当の無い実行中が書けない() -> None:
    with pytest.raises(ValidationError):
        InProgress()  # type: ignore[call-arg]


def test_質問の無い答え待ちが書けない() -> None:
    with pytest.raises(ValidationError):
        AwaitingAnswer(assignee=Agent(name="一号"))  # type: ignore[call-arg]


def test_承認を持ったまま着手できるへ戻れない() -> None:
    with pytest.raises(ValidationError):
        Ready(approval=_approval())  # type: ignore[call-arg]


def test_受け持ちの人以外は承認待ちを持てない() -> None:
    """I6 — 承認できるのは受け持ちの人だけ。担当の型が `Owner`。"""
    AwaitingApproval(assignee=Owner(person=ALICE))
    with pytest.raises(ValidationError):
        AwaitingApproval(assignee=Agent(name="一号"))  # type: ignore[arg-type]


def test_確かめ待ちは根拠の在りかの欄を持たない() -> None:
    """設計 §6 — 終わった（確かめ待ち）は根拠の在りかを持ってはいけない。"""
    assert "evidence_at" not in FinishedPendingRecheck.model_fields
    assert "recheck" in FinishedPendingRecheck.model_fields


def test_急ぎの印がどの状態にも無い() -> None:
    """設計 §7 — そういう欄が無い。急ぎは「期日が今日」で表す。"""
    for state in (Created, Ready, InProgress, AwaitingAnswer, Submitted,
                  AwaitingApproval, Cleared, Failed, FinishedPendingRecheck,
                  Finished, Abandoned):
        assert not {"urgent", "priority", "急ぎ"} & set(state.model_fields)


def test_落ちた中身の無い失敗が書けない() -> None:
    with pytest.raises(ValidationError):
        Failed()  # type: ignore[call-arg]


def test_理由の無い打ち切りが書けない() -> None:
    with pytest.raises(ValidationError):
        Abandoned(by=ALICE)  # type: ignore[call-arg]


def test_状態は素の文字列から作れない() -> None:
    ta = TypeAdapter(State)
    assert ta.validate_python(Ready()) == Ready()
    with pytest.raises(ValidationError):
        ta.validate_python("実行中")
    with pytest.raises(ValidationError):
        ta.validate_python({"name": "存在しない状態"})


def test_終わったは承認を必ず持つ() -> None:
    Finished(approval=_approval())
    with pytest.raises(ValidationError):
        Finished()  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Submitted()  # type: ignore[call-arg]


def test_打ち切った人は人だけ() -> None:
    Abandoned(by=Human(name="座長"), reason="源が直らない")
    with pytest.raises(ValidationError):
        Abandoned(by=Agent(name="一号"), reason="源が直らない")  # type: ignore[arg-type]
