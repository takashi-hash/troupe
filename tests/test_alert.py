"""警告の判定のテスト — 例が仕様。domain/alert.py の表の1行が1つのテスト。

判定は1箇所しかないので、ここが「今日、何が人に見えるか」の全部。
"""

from datetime import datetime, timedelta, timezone

from domain.alert import alerts_for
from domain.job import (
    AwaitingAnswer,
    Briefing,
    Budget,
    Checkpoint,
    ClosedBySelfReport,
    ClosedWithEvidence,
    ContentFailure,
    Core,
    Created,
    EnvironmentFailure,
    FromDefinition,
    Job,
)

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
VIEWER = "人/座長"


def core_example(deadline: datetime, job_id: str = "タスク-x") -> Core:
    return Core(
        job_id=job_id,
        origin=FromDefinition(definition_name="週次の検査の見張り", version=1, period="2026-W34"),
        board_id="ボード/運転",
        ready_at=NOW,
        deadline=deadline,
        budget=Budget(calls=20, seconds=600),
    )


def briefing_example() -> Briefing:
    return Briefing(
        definition_ref="業務ルール/週次の検査の見張り@1",
        source_refs=(),
        material_refs=(),
        artifact_slot="成果物/週次の検査の見張り/2026-W34",
        acceptance_ref="業務ルール/週次の検査の見張り@1#受け入れ基準",
        budget=Budget(calls=20, seconds=600),
        constitution_ref="ボード/運転/方針/1",
    )


def job_with(state: object, days: int = 3, job_id: str = "タスク-x") -> Job:
    """期限を先に置いたタスク——期限の警告に紛れないようにしてから、状態だけを見る"""
    return Job(core=core_example(NOW + timedelta(days=days), job_id), state=state)  # type: ignore[arg-type]


def test_content_failure_is_red() -> None:
    """内容エラーは要対応（赤）——再試行が尽きた・成果の質。人の判断が要る"""
    alerts = alerts_for((job_with(ContentFailure(reason="受け入れ基準を満たさない")),), NOW, VIEWER)
    assert [a.kind for a in alerts] == ["Red"]
    assert alerts[0].detail == "受け入れ基準を満たさない"


def test_environment_failure_is_not_shown() -> None:
    """環境エラーは「今日」に出さない——再試行の最中で、人が今できることが無い（狼少年を作らない）"""
    failing = job_with(
        EnvironmentFailure(
            retries_left=2, return_to="Ready", briefing=briefing_example(), reason="源が読めない"
        )
    )
    assert alerts_for((failing,), NOW, VIEWER) == ()


def test_checkpoint_is_actionable_only_for_assignee() -> None:
    """承認待ちは担当の本人だけが押せる（判断は人間——他人の判断を代わりに押させない）"""
    job = job_with(Checkpoint(artifact_ref="成果物/x", position="座長の承認待ち", assignee_id=VIEWER))
    assert alerts_for((job,), NOW, VIEWER)[0].actionable is True
    assert alerts_for((job,), NOW, "人/事務")[0].actionable is False


def test_awaiting_answer_is_actionable_only_for_addressee() -> None:
    """回答待ちは宛先の本人だけが押せる。判断ではなく、材料の欠けを埋める問い"""
    job = job_with(
        AwaitingAnswer(briefing=briefing_example(), question="どの環境ですか", addressee_id=VIEWER)
    )
    assert alerts_for((job,), NOW, VIEWER)[0].detail == "どの環境ですか"
    assert alerts_for((job,), NOW, "人/事務")[0].actionable is False


def test_self_report_waits_for_the_recheck_deadline() -> None:
    """自己申告は確かめの期限が来てから出る——期限前に出しても、まだ確かめようがない"""
    before = job_with(ClosedBySelfReport(recheck_deadline=NOW + timedelta(days=1)))
    after = job_with(ClosedBySelfReport(recheck_deadline=NOW - timedelta(days=1)))
    assert alerts_for((before,), NOW, VIEWER) == ()
    assert [a.kind for a in alerts_for((after,), NOW, VIEWER)] == ["SelfReport"]


def test_closed_with_evidence_is_not_shown() -> None:
    """証拠で完了したタスクは出ない——済んでいる"""
    done = job_with(ClosedWithEvidence(evidence_ref="証拠/x"), days=-5)
    assert alerts_for((done,), NOW, VIEWER) == ()


def test_deadline_today_is_shown_but_not_the_future() -> None:
    """期限が今日・過ぎていれば出る。先の予定は「今日」に載せない"""
    today = Job(core=core_example(NOW), state=Created())
    future = Job(core=core_example(NOW + timedelta(days=5)), state=Created())
    assert [a.kind for a in alerts_for((today,), NOW, VIEWER)] == ["Deadline"]
    assert alerts_for((future,), NOW, VIEWER) == ()


def test_one_job_raises_one_alert() -> None:
    """1つのタスクに出る警告は1つだけ——承認待ちで期限も今日なら、承認待ちだけ（赤を埋もれさせない）"""
    job = Job(
        core=core_example(NOW),
        state=Checkpoint(artifact_ref="成果物/x", position="座長の承認待ち", assignee_id=VIEWER),
    )
    assert [a.kind for a in alerts_for((job,), NOW, VIEWER)] == ["Checkpoint"]


def test_the_same_alert_is_never_listed_twice() -> None:
    """同じ警告は二度並ばない（警告の鍵で1件）——二度並べた警告は読まれなくなる"""
    job = job_with(ContentFailure(reason="受け入れ基準を満たさない"))
    assert len(alerts_for((job, job), NOW, VIEWER)) == 1


def test_strong_alerts_come_first() -> None:
    """並びは強い順——要対応・承認待ち・回答待ち・自己申告・期限"""
    red = job_with(ContentFailure(reason="だめ"), job_id="タスク-赤")
    checkpoint = job_with(
        Checkpoint(artifact_ref="成果物/x", position="承認待ち", assignee_id=VIEWER),
        job_id="タスク-承認",
    )
    due = Job(core=core_example(NOW, "タスク-期限"), state=Created())
    order = [a.kind for a in alerts_for((due, checkpoint, red), NOW, VIEWER)]
    assert order == ["Red", "Checkpoint", "Deadline"]
