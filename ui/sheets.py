"""読む4枚の導出 — 純粋関数。(Aggregate たち, Event 列) → 画面の節と行。保存しない。

画面に出す言葉は用語集 §10 の語だけ（読みかた 掟10）。
見た目の設計は 設計/10_画面/デザイン案.dc.html が正本。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from domain.definition import Definition, current_period
from domain.event import Event
from domain.alert import Alert
from domain.job import FromDefinition, Job, origin_key
from domain.search import SearchCriteria, assignee_of, definition_of, matches

# 表示名の正本は用語集（§4・§12）。ここは写し——画面の語 lint が §10 と突き合わせる
STATE_LABELS = {
    "Created": "作成済み",
    "Ready": "未着手",
    "Running": "実行中",
    "AwaitingAnswer": "回答待ち",
    "Verifying": "検証中",
    "Checkpoint": "承認待ち",
    "Confirmed": "承認済み",
    "ApplyAttempt": "反映中",
    "Applied": "反映済み",
    "ClosedWithEvidence": "完了",
    "ClosedBySelfReport": "完了",
    "EnvironmentFailure": "エラー",
    "ContentFailure": "エラー",
}
EVENT_LABELS = {
    "JobCreated": "タスクを作成",
    "JobDispatched": "着手できる状態に",
    "LeaseTaken": "着手",
    "LeaseReleased": "担当を解除",
    "LeaseExpired": "担当が時間切れ",
    "ProgressLogged": "進捗を記録",
    "JobSubmitted": "成果物を提出",
    "CheckPassed": "チェック合格",
    "CheckBlocked": "チェック不合格",
    "ReviewPassed": "レビュー合格",
    "ReviewReturned": "レビュー差し戻し",
    "CheckpointReached": "承認待ちに",
    "CheckpointApproved": "承認",
    "JobConfirmed": "承認済みに",
    "JobClosed": "完了",
    "FailureOccurred": "エラー発生",
    "Retried": "再試行",
    "BudgetExceeded": "使用上限を超過",
    "VersionAppended": "バージョンを追加",
    "DefinitionEnacted": "業務ルールを有効化",
    "ConstitutionAppended": "方針を追加",
    "ConstitutionFrozen": "方針を凍結",
    "InstructionTranscribed": "指示からタスクを作成",
    "UtteranceLogged": "メッセージを記録",
    "DiscrepancyFound": "不一致を検出",
    "AgentDown": "担当AIが停止",
    "AgentRecovered": "担当AIが復帰",
}
RED_EVENTS = {"CheckBlocked", "ReviewReturned", "FailureOccurred", "CheckpointBypassed"}
WEEKDAYS = ("月", "火", "水", "木", "金", "土", "日")


@dataclass(frozen=True)
class Row:
    """画面の1行（カード）"""

    title: str
    meta: str = ""
    kind_label: str = ""
    job_id: str | None = None
    red: bool = False
    dashed: bool = False
    action: str | None = None  # 「承認」「回答」——操作できる場所（青）


@dataclass(frozen=True)
class Section:
    """見出しつきの節"""

    label: str
    note: str = ""
    red: bool = False
    rows: tuple[Row, ...] = field(default_factory=tuple)


def _name_of(job: Job) -> str:
    if isinstance(job.core.origin, FromDefinition):
        return job.core.origin.definition_name
    return job.core.job_id


def _period_of(job: Job) -> str:
    if isinstance(job.core.origin, FromDefinition):
        return job.core.origin.period
    return "—"


def _date_label(when: datetime, now: datetime) -> str:
    label = f"{when.month:02d}/{when.day:02d}（{WEEKDAYS[when.weekday()]}）"
    if when.date() == now.date():
        label += " 今日"
    return label


# ---- 今日（MorningSheet） ----


SECTION_LABELS: dict[str, tuple[str, str]] = {
    "Red": ("要対応", "解消されるまで残ります"),
    "Checkpoint": ("承認待ち", "承認できるのは担当者だけです"),
    "AwaitingAnswer": ("回答待ち", "判断ではなく、不足している情報の確認です"),
    "SelfReport": ("自己申告", "証拠が無いまま完了にしました。確かめの期限が来ています"),
    "Deadline": ("期限", "今日が期限のタスク"),
}
ACTION_WORDS = {"Checkpoint": "承認", "AwaitingAnswer": "回答"}


def morning_sections(alerts: tuple[Alert, ...]) -> list[Section]:
    """今日の節 — 警告を並べるだけ。**何が赤かはここで決めない**（判定は surface の1箇所）。

    タスクを受け取らないので、判定しようにも材料が無い——型が掟の執行者。
    """
    sections: list[Section] = []
    for kind, (label, note) in SECTION_LABELS.items():
        rows = tuple(
            Row(
                title=alert.title,
                meta=_alert_meta(alert),
                kind_label=label,
                job_id=alert.job_id,
                red=alert.kind == "Red",
                action=ACTION_WORDS.get(alert.kind) if alert.actionable else None,
            )
            for alert in alerts
            if alert.kind == kind
        )
        if rows:
            sections.append(
                Section(f"{label} {len(rows)}件", note, red=kind == "Red", rows=rows)
            )
    return sections


def _alert_meta(alert: Alert) -> str:
    """1行の脇に出す一言——期限と、種ごとの手がかり"""
    parts = [f"期限 {alert.deadline.date().isoformat()}"]
    if alert.kind == "SelfReport":
        parts = [f"確かめの期限 {alert.detail}"]
    elif alert.detail:
        parts.append(alert.detail)
    elif alert.kind == "Deadline":
        parts.append(STATE_LABELS.get(alert.state_kind, alert.state_kind))
    return " ・ ".join(parts)


def morning_count(sections: list[Section]) -> int:
    """今日の件数 — 今日の枚に出ている行の数（見出しの脇に出す）"""
    return sum(len(section.rows) for section in sections)


# ---- 予定（Outlook） ----


def _next_time(cadence: str, now: datetime) -> datetime:
    if cadence == "weekly":
        return now + timedelta(weeks=1)
    return (now.replace(day=1) + timedelta(days=32)).replace(day=1)


def outlook_sections(
    jobs: tuple[Job, ...],
    definitions: tuple[Definition, ...],
    keys: frozenset[str],
    now: datetime,
    criteria: SearchCriteria | None = None,
) -> list[Section]:
    """予定の節 — 実線は作成済みのタスク。点線は業務ルールから予測される、まだ作成されていないタスク。

    絞り込みは検索と同じキー（枚ごとに別の絞り方を作らない）。
    """
    narrowed = criteria or SearchCriteria()
    shown = [job for job in jobs if matches(job, narrowed)]
    by_date: dict[str, list[Row]] = {}
    for job in sorted(shown, key=lambda j: j.core.deadline):
        label = _date_label(job.core.deadline, now)
        state = job.state.kind
        by_date.setdefault(label, []).append(
            Row(
                title=_name_of(job),
                meta=STATE_LABELS.get(state, state),
                job_id=job.core.job_id,
                red=state in ("EnvironmentFailure", "ContentFailure"),
            )
        )
    sections = [Section(label, rows=tuple(rows)) for label, rows in by_date.items()]

    prospect_rows: list[Row] = []
    narrowing = narrowed != SearchCriteria()
    for definition in definitions:
        if narrowing and narrowed.definition_name not in ("", definition.name):
            continue  # 業務ルールで絞っているなら、その業務ルールの予定だけ
        if narrowing and (narrowed.state_kind or narrowed.assignee or narrowed.keyword):
            continue  # まだ作成されていないものに、状態も担当も中身も無い
        if definition.enacted is None:
            continue
        version = next(v for v in definition.versions if v.number == definition.enacted)
        for when in (now, _next_time(version.cadence, now)):
            period = current_period(version.cadence, when)
            origin = FromDefinition(
                definition_name=definition.name, version=version.number, period=period
            )
            key = origin_key(origin)
            if key is not None and key not in keys:
                prospect_rows.append(
                    Row(title=f"{definition.name}（予定）", meta=period, dashed=True)
                )
    if prospect_rows:
        sections.append(
            Section("この先", "業務ルールから予測しています。まだ作成されていません", rows=tuple(prospect_rows))
        )
    return sections


# ---- 履歴（History） ----


def history_sections(
    events: tuple[Event, ...],
    criteria: SearchCriteria | None = None,
    jobs_by_id: dict[str, Job] | None = None,
) -> list[Section]:
    """履歴の節 — これまでの操作と結果。どの行からも詳細へ辿れる。

    絞り込みは検索と同じキー——タスクの欄で絞るので、そのタスクの出来事だけが残る。
    """
    narrowed = criteria or SearchCriteria()
    known = jobs_by_id or {}
    if narrowed != SearchCriteria():
        allowed = {job_id for job_id, job in known.items() if matches(job, narrowed)}
        events = tuple(
            e for e in events
            if (e.job_id in allowed)
            or (e.job_id is None and not narrowed.keyword and not narrowed.state_kind
                and not narrowed.definition_name and not narrowed.assignee)
        )
    by_date: dict[str, list[Row]] = {}
    for event in events:
        local = event.at.astimezone()
        label = f"{local.month:02d}/{local.day:02d}（{WEEKDAYS[local.weekday()]}）"
        by_date.setdefault(label, []).append(
            Row(
                title=EVENT_LABELS.get(event.kind, event.kind),
                meta=local.strftime("%H:%M") + (f" ・ {event.job_id}" if event.job_id else ""),
                job_id=event.job_id,
                red=event.kind in RED_EVENTS,
            )
        )
    return [Section(label, rows=tuple(rows)) for label, rows in by_date.items()]


# ---- 詳細（JobSheet） ----


@dataclass(frozen=True)
class JobSheet:
    """詳細 — 誰が・いつ・何を・どうした（I5 を画面にしたもの）"""

    job_id: str
    title: str
    state_label: str
    facts: tuple[tuple[str, str], ...]
    artifacts: tuple[str, ...]
    timeline: tuple[tuple[str, str, bool], ...]  # (時刻, 出来事, 赤か)


def job_sheet(job: Job, events: tuple[Event, ...]) -> JobSheet:
    """詳細を作る — 1つのタスクの、誰が・いつ・何を・どうしたを組み立てる"""
    origin = job.core.origin
    if isinstance(origin, FromDefinition):
        origin_text = f"業務ルール「{origin.definition_name}」v{origin.version} / {origin.period}"
    else:
        origin_text = origin.kind
    facts: list[tuple[str, str]] = [
        ("作成元", origin_text),
        ("期限", job.core.deadline.date().isoformat()),
        ("使用使用上限", f"{job.core.budget.calls}回 ・ {job.core.budget.seconds}秒"),
    ]
    briefing = getattr(job.state, "briefing", None)
    if briefing is not None:
        facts.append(("作業情報", f"{briefing.definition_ref} ・ {briefing.constitution_ref}"))
    artifacts: list[str] = []
    slot = getattr(briefing, "artifact_slot", None)
    if slot:
        artifacts.append(f"保存先 {slot}")
    artifact_ref = getattr(job.state, "artifact_ref", None)
    if artifact_ref:
        artifacts.append(str(artifact_ref))
    timeline = tuple(
        (
            event.at.astimezone().strftime("%H:%M"),
            EVENT_LABELS.get(event.kind, event.kind),
            event.kind in RED_EVENTS,
        )
        for event in events
    )
    return JobSheet(
        job_id=job.core.job_id,
        title=_name_of(job),
        state_label=STATE_LABELS.get(job.state.kind, job.state.kind),
        facts=tuple(facts),
        artifacts=tuple(artifacts),
        timeline=timeline,
    )


# ---- 検索（SearchSheet） ----


def search_options(jobs: tuple[Job, ...]) -> tuple[list[str], list[str], list[str]]:
    """検索の選択肢を導く（予定と履歴の絞り込みも同じキー）— 手書きの一覧にしない（名指しの一覧より、宣言から導く）。

    状態は状態モデルから、業務ルールと担当は帳簿のタスクから。
    新しい状態や業務ルールが増えたら、選択肢が勝手に追いつく。
    """
    states = [STATE_LABELS[kind] for kind in dict.fromkeys(STATE_LABELS)]
    definitions = sorted({d for d in (definition_of(job) for job in jobs) if d})
    assignees = sorted({a for a in (assignee_of(job) for job in jobs) if a})
    return states, definitions, assignees


def state_kind_of_label(label: str) -> str:
    """画面の状態の表示から、状態の種を引く（表示と種の対応は1箇所）"""
    for kind, shown in STATE_LABELS.items():
        if shown == label:
            return kind
    return ""


def search_sections(
    jobs: tuple[Job, ...], criteria: SearchCriteria, bodies: dict[str, str]
) -> list[Section]:
    """検索の節 — 完了も含めたすべてのタスクから、条件に合うものを並べる"""
    found = [
        job for job in jobs if matches(job, criteria, bodies.get(job.core.job_id, ""))
    ]
    rows = tuple(
        Row(
            title=_name_of(job),
            meta=" ・ ".join(
                filter(
                    None,
                    [
                        _period_of(job),
                        f"期限 {job.core.deadline.date().isoformat()}",
                        f"担当 {assignee_of(job)}" if assignee_of(job) else "",
                    ],
                )
            ),
            kind_label=STATE_LABELS.get(job.state.kind, job.state.kind),
            job_id=job.core.job_id,
            red=job.state.kind in ("EnvironmentFailure", "ContentFailure"),
        )
        for job in sorted(found, key=lambda j: j.core.deadline, reverse=True)
    )
    if not rows:
        return []
    return [Section(f"{len(rows)}件", "完了したタスクも含めて探しています", rows=rows)]
