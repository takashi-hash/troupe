"""4枚の導出のテスト — 例が仕様。「このデータなら、この行が載る／載らない」。"""

from datetime import datetime, timedelta, timezone

from domain.definition import Definition, Version
from domain.event import Event
from domain.job import (
    Briefing,
    Budget,
    Checkpoint,
    Core,
    Created,
    FromDefinition,
    Job,
    origin_key,
)
from ui.sheets import job_sheet, morning_count, morning_sections, outlook_sections

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)


def core_example(deadline: datetime) -> Core:
    return Core(
        job_id="タスク-x",
        origin=FromDefinition(definition_name="週次の検査の見張り", version=1, period="2026-W34"),
        board_id="ボード/運転",
        ready_at=NOW,
        deadline=deadline,
        budget=Budget(calls=20, seconds=600),
    )


def definition_example() -> Definition:
    return Definition(
        name="週次の検査の見張り",
        board_id="ボード/運転",
        versions=(
            Version(
                number=1,
                instruction="やること",
                acceptance="良しの条件",
                cadence="weekly",
                deadline_days=2,
                budget=Budget(calls=20, seconds=600),
            ),
        ),
        enacted=1,
    )


def test_morning_shows_due_today_but_not_future() -> None:
    """「今日」は期限が今日のものだけ——先の予定は載せない（載せると赤が埋もれる）"""
    due_today = Job(core=core_example(NOW), state=Created())
    sections = morning_sections((due_today,), NOW, viewer="人/座長")
    assert morning_count(sections) == 1
    assert sections[0].label.startswith("期限")

    due_future = Job(core=core_example(NOW + timedelta(days=5)), state=Created())
    assert morning_sections((due_future,), NOW, viewer="人/座長") == []


def test_morning_approve_button_only_for_assignee() -> None:
    """「承認」ボタンが出るのは担当した人にだけ——担当外にはボタンが無い"""
    job = Job(
        core=core_example(NOW + timedelta(days=1)),
        state=Checkpoint(artifact_ref="成果物/x", position="座長の承認待ち", assignee_id="人/座長"),
    )
    mine = morning_sections((job,), NOW, viewer="人/座長")
    others = morning_sections((job,), NOW, viewer="人/事務")
    assert mine[0].rows[0].action == "承認"
    assert others[0].rows[0].action is None


def test_outlook_shows_standing_job_and_next_week_prospect() -> None:
    """「予定」には、作成済みのタスクと、まだ作成されていない来週の予定が載る（今週の予定は出ない）"""
    job = Job(core=core_example(NOW + timedelta(days=2)), state=Created())
    key = origin_key(job.core.origin)
    assert key is not None
    sections = outlook_sections((job,), (definition_example(),), frozenset({key}), NOW)
    all_rows = [row for section in sections for row in section.rows]
    assert any(row.title == "週次の検査の見張り" and not row.dashed for row in all_rows)
    prospects = [row for row in all_rows if row.dashed]
    assert len(prospects) == 1
    assert prospects[0].meta == "2026-W35"


def test_job_sheet_timeline_marks_red_events() -> None:
    """「詳細」には経緯が順に載り、止め・差し戻し・エラーは赤い"""
    job = Job(core=core_example(NOW + timedelta(days=2)), state=Created())
    events = (
        Event(kind="JobCreated", at=NOW, job_id="タスク-x"),
        Event(kind="ReviewReturned", at=NOW + timedelta(minutes=5), job_id="タスク-x"),
    )
    sheet = job_sheet(job, events)
    assert sheet.timeline[0][1] == "タスクを作成"
    assert sheet.timeline[0][2] is False
    assert sheet.timeline[1][1] == "レビュー差し戻し"
    assert sheet.timeline[1][2] is True
    assert ("期限", (NOW + timedelta(days=2)).date().isoformat()) in sheet.facts
