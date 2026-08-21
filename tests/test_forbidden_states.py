"""禁止状態のテスト — 設計/6_型/禁止状態一覧.md の行を、そのままテストにする（例が仕様）。

どれも「注意書き」ではなく「書けない」ことの確認——pydantic が実行時に弾く。
docstring の1行目が禁止状態一覧の行。
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from domain.job import (
    AttemptRecord,
    Briefing,
    Budget,
    Core,
    FromDefinition,
    IrreversibleApply,
    Job,
    Lease,
    Ready,
    ReversibleApply,
    Running,
    ClosedWithEvidence,
)

NOW = datetime(2026, 8, 21, 9, 0)


def briefing_example() -> Briefing:
    return Briefing(
        definition_ref="業務ルール/週次の検査の見張り/3",
        source_refs=("読み口/git",),
        material_refs=(),
        artifact_slot="成果物/週次の検査の見張り/2026-W34",
        acceptance_ref="業務ルール/週次の検査の見張り/3#受け入れ基準",
        budget=Budget(calls=50, seconds=3600),
        constitution_ref="ボード/運転/方針/1",
    )


def core_example() -> Core:
    return Core(
        job_id="タスク-001",
        origin=FromDefinition(definition_name="週次の検査の見張り", version=3, period="2026-W34"),
        board_id="ボード/運転",
        ready_at=NOW,
        deadline=NOW + timedelta(days=9),
        budget=Budget(calls=50, seconds=3600),
    )


def test_irreversible_apply_without_approval() -> None:
    """承認待ちなしの不可逆反映は作れない——承認の記録が型の材料"""
    with pytest.raises(ValidationError):
        IrreversibleApply.model_validate(
            {"actor": "機体-A", "at": NOW, "attempt": AttemptRecord(actor="機体-A", at=NOW)}
        )


def test_apply_without_attempt() -> None:
    """試みの記録なしの反映は作れない——反映の二相の前半が必ず要る"""
    with pytest.raises(ValidationError):
        ReversibleApply.model_validate({"actor": "機体-A", "at": NOW})


def test_no_urgent_flag() -> None:
    """緊急フラグはどこにも書けない——急ぎは2つの時刻で表す"""
    with pytest.raises(ValidationError):
        Core.model_validate({**core_example().model_dump(), "緊急": True})


def test_ready_cannot_hold_lease() -> None:
    """札を持つ未着手は書けない——札は実行中だけが持つ"""
    with pytest.raises(ValidationError):
        Ready.model_validate(
            {"briefing": briefing_example(), "lease": Lease(holder="機体-A", expires_at=NOW)}
        )


def test_ready_requires_briefing() -> None:
    """作業情報の無い未着手は書けない——作業情報の無いタスクは機体に配れない"""
    with pytest.raises(ValidationError):
        Ready.model_validate({})


def test_job_requires_origin() -> None:
    """作成元の無いタスクは書けない——作成元は突合の冪等の鍵"""
    data = core_example().model_dump()
    del data["origin"]
    with pytest.raises(ValidationError):
        Core.model_validate(data)


def test_running_requires_lease() -> None:
    """札を持たない実行中は書けない"""
    with pytest.raises(ValidationError):
        Running.model_validate({"briefing": briefing_example(), "retries_left": 3})


def test_closing_requires_evidence() -> None:
    """証拠なしの「証拠で閉じた」は書けない——完了は証拠で閉じる"""
    with pytest.raises(ValidationError):
        ClosedWithEvidence.model_validate({})


def test_applied_requires_record() -> None:
    """AttemptRecord なしの Applied は書けない——反映の記録が試みを必ず持つ"""
    from domain.job import Applied

    with pytest.raises(ValidationError):
        Applied.model_validate({"artifact_ref": "成果物/x"})


def test_check_cannot_return_and_review_cannot_block() -> None:
    """チェックに差し戻しは無く、レビューに止める力は無い——結果は別の型で混ざらない"""
    from pydantic import TypeAdapter

    from domain.job import CheckResult, ReviewResult

    with pytest.raises(ValidationError):
        TypeAdapter(CheckResult).validate_python({"kind": "Returned", "reason": "x"})
    with pytest.raises(ValidationError):
        TypeAdapter(ReviewResult).validate_python({"kind": "Blocked", "reason": "x"})


def test_valid_job_can_be_built() -> None:
    """禁止を殺した型が、正しいタスクまで殺していないことの確かめ"""
    job = Job(core=core_example(), state=Ready(briefing=briefing_example()))
    assert job.core.origin.kind == "FromDefinition"
