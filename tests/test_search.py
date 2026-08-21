"""検索のテスト — 例が仕様。「この条件なら、このタスクが出る／出ない」。

キーはモデルの欄と1対1（設計/10_画面 §4）。
"""

from datetime import datetime, timedelta, timezone

from domain.job import (
    Briefing,
    Budget,
    Checkpoint,
    Core,
    Created,
    FromDefinition,
    Job,
    Ready,
)
from domain.search import SearchCriteria, assignee_of, matches
from ui.sheets import search_options, search_sections, state_kind_of_label

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)


def briefing() -> Briefing:
    return Briefing(
        definition_ref="業務ルール/週次の検査の見張り/1",
        source_refs=(),
        material_refs=(),
        artifact_slot="成果物/週次の検査の見張り/2026-W34",
        acceptance_ref="業務ルール/週次の検査の見張り/1#受け入れ基準",
        budget=Budget(calls=20, seconds=600),
        constitution_ref="ボード/運転/方針/1",
    )


def job(name: str = "週次の検査の見張り", period: str = "2026-W34", state=None, days: int = 2) -> Job:
    return Job(
        core=Core(
            job_id=f"タスク-{name}-{period}",
            origin=FromDefinition(definition_name=name, version=1, period=period),
            board_id="ボード/運転",
            ready_at=NOW,
            deadline=NOW + timedelta(days=days),
            budget=Budget(calls=20, seconds=600),
        ),
        state=state or Created(),
    )


def test_empty_criteria_matches_everything() -> None:
    """条件が空なら、すべてのタスクが合う"""
    assert matches(job(), SearchCriteria()) is True


def test_keyword_hits_definition_name() -> None:
    """キーワードは業務ルールの名に当たる"""
    assert matches(job(), SearchCriteria(keyword="検査")) is True
    assert matches(job(), SearchCriteria(keyword="棚卸し")) is False


def test_keyword_hits_artifact_body() -> None:
    """キーワードは成果物の中身にも当たる——完了したタスクを中身から探せる"""
    assert matches(job(), SearchCriteria(keyword="72件"), body="検査は緑（72件）") is True
    assert matches(job(), SearchCriteria(keyword="72件"), body="") is False


def test_state_filter() -> None:
    """状態で絞れる（画面の表示から状態の種を引く）"""
    waiting = job(state=Checkpoint(artifact_ref="成果物/x", position="座長の承認", assignee_id="人/座長"))
    kind = state_kind_of_label("承認待ち")
    assert matches(waiting, SearchCriteria(state_kind=kind)) is True
    assert matches(job(), SearchCriteria(state_kind=kind)) is False


def test_assignee_filter() -> None:
    """担当で絞れる——担当は承認待ちの担当者か、札の持ち主"""
    mine = job(state=Checkpoint(artifact_ref="成果物/x", position="座長の承認", assignee_id="人/座長"))
    assert assignee_of(mine) == "人/座長"
    assert matches(mine, SearchCriteria(assignee="人/座長")) is True
    assert matches(mine, SearchCriteria(assignee="人/事務")) is False


def test_deadline_range() -> None:
    """期限の範囲で絞れる"""
    soon = job(days=1)
    later = job(period="2026-W40", days=30)
    criteria = SearchCriteria(deadline_to=(NOW + timedelta(days=7)).date())
    assert matches(soon, criteria) is True
    assert matches(later, criteria) is False


def test_options_are_derived_not_hardcoded() -> None:
    """絞り込みの選択肢は帳簿から導く——新しい業務ルールが増えたら勝手に追いつく"""
    jobs = (job("週次の検査の見張り"), job("週次の依存の棚卸し", "2026-W34"))
    states, definitions, assignees = search_options(jobs)
    assert definitions == ["週次の依存の棚卸し", "週次の検査の見張り"]
    assert "承認待ち" in states  # 状態は状態モデルから
    assert assignees == []  # 誰も担当していない


def test_search_finds_closed_jobs() -> None:
    """検索は完了したタスクにも届く——「今日」や「予定」から落ちたものを拾えるのが検索の役目"""
    from domain.job import ClosedWithEvidence

    closed = job(state=ClosedWithEvidence(evidence_ref="証拠/x"))
    sections = search_sections((closed,), SearchCriteria(keyword="検査"), {})
    assert len(sections) == 1
    assert sections[0].rows[0].kind_label == "完了"


def test_no_match_returns_nothing() -> None:
    """合うものが無ければ、空のまま（作り話をしない）"""
    assert search_sections((job(),), SearchCriteria(keyword="ありえない語"), {}) == []


# ---- 絞り込み（予定・履歴に付く。検索と同じキー） ----


def test_outlook_filter_narrows_by_definition() -> None:
    """予定は業務ルールで絞れる——検索と同じキーを使う"""
    from ui.sheets import outlook_sections

    backup = job("週次の検査の見張り")
    stock = job("週次の依存の棚卸し")
    all_rows = outlook_sections((backup, stock), (), frozenset(), NOW)
    narrowed = outlook_sections(
        (backup, stock), (), frozenset(), NOW, SearchCriteria(definition_name="週次の依存の棚卸し")
    )
    assert sum(len(s.rows) for s in all_rows) == 2
    titles = [r.title for s in narrowed for r in s.rows]
    assert titles == ["週次の依存の棚卸し"]


def test_outlook_filter_hides_prospects_when_narrowing_by_state() -> None:
    """状態で絞ったら予定（まだ作成されていないもの）は出さない——状態を持たないから"""
    from domain.definition import Definition, Version
    from ui.sheets import outlook_sections

    definition = Definition(
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
    with_prospects = outlook_sections((), (definition,), frozenset(), NOW)
    narrowed = outlook_sections(
        (), (definition,), frozenset(), NOW, SearchCriteria(state_kind="Checkpoint")
    )
    assert sum(len(s.rows) for s in with_prospects) > 0
    assert narrowed == []


def test_history_filter_keeps_only_matching_jobs() -> None:
    """履歴はタスクの欄で絞れる——合うタスクの出来事だけが残る"""
    from domain.event import Event
    from ui.sheets import history_sections

    backup = job("週次の検査の見張り")
    stock = job("週次の依存の棚卸し")
    events = (
        Event(kind="JobCreated", at=NOW, job_id=backup.core.job_id),
        Event(kind="JobCreated", at=NOW, job_id=stock.core.job_id),
    )
    known = {backup.core.job_id: backup, stock.core.job_id: stock}
    narrowed = history_sections(
        events, SearchCriteria(definition_name="週次の検査の見張り"), known
    )
    rows = [r for s in narrowed for r in s.rows]
    assert len(rows) == 1
    assert rows[0].job_id == backup.core.job_id


def test_no_filter_shows_everything() -> None:
    """絞り込みを掛けていなければ（すべて）、そのままの枚が出る"""
    from domain.event import Event
    from ui.sheets import history_sections

    events = (Event(kind="ConstitutionFrozen", at=NOW),)  # タスクに紐づかない出来事
    assert sum(len(s.rows) for s in history_sections(events)) == 1
