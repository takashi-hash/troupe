"""組み立ての根。層に属さない。**具体を注ぐのはここだけ。**

設計: 設計/どう作るか §5。

帳簿は手元の SQLite（data/ichiza.db）かクラウドの Cloud SQL（`--dsn`）、
LLM は手元の Ollama かクラウドの Gemini（`--llm`）、
源はファイル、題材は custom/ のフォルダ。注ぎ先はすべて宣言（Protocol）——中身は誰も知らない。

窓は `window`（今日・予定・履歴・検索——詳細は行から開く）。CLI は同じ入り口を文字で呼ぶ——
画面から渡るのは文字だけ、という決まりを引数がそのまま守る。

    uv run python main.py window --viewer 座長    窓（今日・予定・履歴・検索）
    uv run python main.py tick                    時計のひと回り
    uv run python main.py agent --name 一号       AI のひと回り（着手→LLM に問う→巡回）
    uv run python main.py today --viewer 座長     今日を文字で
    uv run python main.py rule-add --name 週次の依存の棚卸し --by 座長
    uv run python main.py rule-activate --name 週次の依存の棚卸し --version 1 --by 座長
    uv run python main.py rule-deactivate --name 週次の依存の棚卸し --by 座長
    uv run python main.py act approve --id J-1 --by 座長
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from adapters.acl.llm import GeminiGuide, GeminiLlm, OllamaLlm, SilentGuide
from adapters.acl.source import EmrSource, FileSource, Sources
from adapters.clock import SystemClock
from adapters.emr import (
    EmrDrafts,
    EmrVisits,
    PostgresPatients,
    PostgresPatterns,
    PostgresRoute,
    PostgresSchedule,
    PostgresVisit,
)
from adapters.ids import UuidIds
from adapters.ledger.db import open_cloud_ledger, open_ledger
from adapters.ledger.jobs import SqliteJobs
from adapters.ledger.reading import (
    SqliteActiveRules,
    SqliteDeliveredMarks,
    SqliteDetail,
    SqliteHistory,
    SqliteJobStates,
    SqliteOrigins,
    SqliteOverdueMarks,
    SqliteRuleLines,
    SqliteSearch,
    SqliteToday,
    SqliteWork,
)
from adapters.ledger.rules import SqliteRules
from adapters.ledger.stores import (
    SqliteAssessments,
    SqliteEvidence,
    SqliteQuestions,
    SqliteResults,
)
from adapters.topic import FolderTopic
from app.dto.detail_view import DetailView
from app.dto.history_row import HistoryRow
from app.dto.patient_row import PatientRow
from app.dto.pattern_row import PatternRow
from app.dto.route_stop import RouteStop
from app.dto.visit_view import VisitView
from app.dto.patient_view import PatientView
from app.dto.row_filter import RowFilter
from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from app.dto.today_row import TodayRow
from app.dto.version_form import VersionForm
from app.ports.llm_port import LlmPort
from app.services.agent.consult import consult
from app.services.agent.patrol import patrol
from app.services.agent.start import start
from app.services.clock.audit import audit
from app.services.clock.confirm import confirm
from app.services.clock.create import create
from app.services.clock.deliver_drafts import deliver_drafts
from app.services.clock.hand_out import hand_out
from app.services.clock.mark_overdue import mark_overdue
from app.services.clock.plan_visits import plan_visits
from app.services.clock.return_timed_out import return_timed_out
from app.services.clock.run_check import run_check
from app.services.clock.sort_failures import sort_failures
from app.services.human.abandon import abandon
from app.services.human.activate import activate
from app.services.human.add_version import add_version, add_version_from_fields
from app.services.human.add_pattern import add_pattern
from app.services.human.answer import answer
from app.services.human.cancel_visit import cancel_visit
from app.services.human.end_pattern import end_pattern
from app.services.human.sign_note import sign_note
from app.services.human.deactivate import deactivate
from app.services.human.approve import approve
from app.services.human.request import request_from_fields
from app.services.human.send_back import send_back
from app.services.screen.gather_detail import gather_detail
from app.services.screen.gather_history import gather_history
from app.services.screen.gather_patterns import gather_patterns
from app.services.screen.gather_route import gather_route
from app.services.screen.gather_patient import gather_patient
from app.services.screen.gather_patients import gather_patients
from app.services.screen.gather_schedule import gather_schedule, gather_upcoming
from app.services.screen.gather_search import gather_search
from app.services.screen.gather_visit import gather_visit
from app.services.screen.ask_guide import ask_guide
from app.services.screen.gather_today import gather_today
from domain.value_objects.job.job_id import JobId
from domain.value_objects.people.agent import Agent
from ui.web import 手
from ui.words import 状態, 操作, 語


class Ichiza:
    """一座 — 注いだ口の束。"""

    def __init__(
        self,
        root: Path,
        model: str,
        llm: str = "ollama",
        dsn: str | None = None,
        emr_dsn: str | None = None,
    ) -> None:
        # 在りかが渡ればクラウドの帳簿、無ければ手元の帳簿。**呼ぶ側は口しか知らない。**
        self.conn = (
            open_cloud_ledger(dsn) if dsn else open_ledger(root / "data" / "ichiza.db")
        )
        self.jobs = SqliteJobs(self.conn)
        self.rules = SqliteRules(self.conn)
        self.results = SqliteResults(self.conn)
        self.evidences = SqliteEvidence(self.conn)
        self.questions = SqliteQuestions(self.conn)
        self.assessments = SqliteAssessments(self.conn)
        self.states = SqliteJobStates(self.conn)
        self.origins = SqliteOrigins(self.conn)
        self.active = SqliteActiveRules(self.conn)
        self.work = SqliteWork(self.conn)
        self.today = SqliteToday(self.conn)
        self.details = SqliteDetail(self.conn)
        self.rule_lines = SqliteRuleLines(self.conn)
        self.overdue_marks = SqliteOverdueMarks(self.conn)
        self.delivered_marks = SqliteDeliveredMarks(self.conn)
        self.history = SqliteHistory(self.conn)
        self.search_hits = SqliteSearch(self.conn)
        self.clock = SystemClock()
        self.ids = UuidIds()
        # 源は形で選ばれる——file: は書類、db: は診療録。**中は形を知らない**
        self.source = Sources(FileSource(root), EmrSource(emr_dsn))
        self.patients = PostgresPatients(emr_dsn)
        self.drafts = EmrDrafts(emr_dsn)
        self.patterns_port = PostgresPatterns(emr_dsn)
        self.schedule_port = PostgresSchedule(emr_dsn)
        self.route = PostgresRoute(emr_dsn)
        self.visits_port = EmrVisits(emr_dsn)
        self.visit_view = PostgresVisit(emr_dsn)
        self.topics = FolderTopic(root / "custom")
        self.llm = _llm(llm, model)
        # 案内は仕事の外の一呼び——書く道具を持たない(設計 §4 GuidePort)
        self.guide = GeminiGuide(model or _MODELS["gemini"]) if llm == "gemini" else SilentGuide()


#: LLM の道具の既定のモデル。**どちらも同じ口**——選ぶのはここだけ。
_MODELS = {"ollama": "gpt-oss:20b", "gemini": "gemini-3.5-flash"}


def _llm(kind: str, model: str | None) -> LlmPort:
    """LLM の道具を選ぶ。**呼ぶ側は口しか知らない**——設計 §4 の腐敗防止層。"""
    if kind not in _MODELS:
        raise SystemExit(f"LLM の道具は {'・'.join(_MODELS)} のどれかです: {kind}")
    chosen = model or _MODELS[kind]
    return GeminiLlm(model=chosen) if kind == "gemini" else OllamaLlm(model=chosen)

def _手(za: Ichiza, viewer: str) -> 手:
    """手を組む。**器が2つでも、手を組む場所は1つ。**

    設計/どう作るか §5——器は `shell`（机の窓）と `web`（web の窓）。
    どちらも同じ手を受け取る。手の中身（app のどの操作を呼ぶか）は画面が知らない。
    """

    def 読む() -> tuple[TodayRow, ...]:
        return gather_today(za.today, za.clock, viewer)

    def 押す(what: str, id: str, text: str) -> str | None:
        if what == "answer":
            断り = answer(za.jobs, za.questions, za.clock, id, viewer, text)
        elif what == "approve":
            断り = approve(za.jobs, za.clock, id, viewer)
        elif what == "send_back":
            断り = send_back(za.jobs, za.clock, id, viewer, text)
        elif what == "abandon":
            断り = abandon(za.jobs, za.clock, id, viewer, text)
        else:
            return f"Unknown action: {what}"
        return None if 断り is None else 断り.reason

    def 詳細(id: str) -> DetailView | None:
        return gather_detail(za.today, za.details, za.clock, viewer, id)

    def 予定を読む() -> tuple[ScheduleRow, ...]:
        return gather_schedule(za.rule_lines, za.active, za.origins, za.clock)

    def 決まりを押す(
        what: str, name: str, version: int, fields: dict[str, str]
    ) -> str | None:
        if what == "add_version":
            断り = add_version_from_fields(
                za.rules, za.topics, za.clock, name, viewer, fields
            )
        elif what == "activate":
            断り = activate(za.rules, za.clock, name, version, viewer)
        elif what == "deactivate":
            断り = deactivate(za.rules, za.clock, name, viewer)
        else:
            return f"Unknown action: {what}"
        return None if 断り is None else 断り.reason

    def 履歴を読む() -> tuple[HistoryRow, ...]:
        return gather_history(za.history)

    def 検索する(filter: RowFilter) -> tuple[SearchRow, ...]:
        return gather_search(za.search_hits, filter)

    def 頼む(body: str, fields: dict[str, str]) -> str | None:
        断り = request_from_fields(za.jobs, za.ids, za.clock, viewer, body, fields)
        return None if 断り is None else 断り.reason

    def 来ている仕事を読む() -> tuple[SearchRow, ...]:
        return gather_upcoming(za.today)

    def 患者たちを読む() -> tuple[PatientRow, ...]:
        return gather_patients(za.patients)

    def 患者を読む(code: str) -> PatientView | None:
        return gather_patient(za.patients, code)

    def 取り決めを読む() -> tuple[PatternRow, ...]:
        return gather_patterns(za.patterns_port)

    def 取り決めを押す(what: str, fields: dict[str, str]) -> str | None:
        if what == "add_pattern":
            断り = add_pattern(
                za.patterns_port,
                fields.get("patient", ""), fields.get("weekday", ""),
                fields.get("clinician", ""), fields.get("purpose", ""),
                fields.get("start", ""), fields.get("every_weeks", "1"),
                by=viewer,
            )
        elif what == "end_pattern":
            断り = end_pattern(za.patterns_port, za.clock, fields.get("id", ""), by=viewer)
        else:
            return f"Unknown action: {what}"
        return None if 断り is None else 断り.reason

    def 今日() -> str:
        # 事業所の暦は Asia/Tokyo。ここ（組み立ての根）で1度だけ決める——器は尋ねるだけ
        from datetime import timedelta, timezone

        return za.clock.now().astimezone(timezone(timedelta(hours=9))).date().isoformat()

    def 訪問を読む(id: str) -> VisitView | None:
        return gather_visit(za.visit_view, id)

    def 訪問を押す(what: str, fields: dict[str, str]) -> str | None:
        if what == "sign_note":
            断り = sign_note(
                za.visits_port,
                fields.get("id", ""), fields.get("signer", ""),
                fields.get("s", ""), fields.get("o", ""),
                fields.get("a", ""), fields.get("p", ""),
                fields.get("draft_id", ""), by=viewer,
            )
        elif what == "cancel_visit":
            断り = cancel_visit(za.visits_port, fields.get("id", ""), fields.get("reason", ""), by=viewer)
        else:
            return f"Unknown action: {what}"
        return None if 断り is None else 断り.reason

    def 道順を読む(
        day: str,
    ) -> tuple[tuple[float, float] | None, dict[str, tuple[RouteStop, ...]]]:
        return gather_route(za.route, day)

    def 案内(
        question: str, digest: str, history: tuple[tuple[str, str], ...]
    ) -> str:
        return ask_guide(za.guide, question, digest, history)

    return 手(
        fetch=読む,
        act=押す,
        detail=詳細,
        schedule_fetch=予定を読む,
        schedule_act=決まりを押す,
        history_fetch=履歴を読む,
        search=検索する,
        request=頼む,
        upcoming=来ている仕事を読む,
        patients=患者たちを読む,
        patient=患者を読む,
        patterns=取り決めを読む,
        pattern_act=取り決めを押す,
        visit=訪問を読む,
        visit_act=訪問を押す,
        route=道順を読む,
        today=今日,
        guide=案内,
        close=za.conn.close,
    )


def _tick(za: Ichiza) -> None:
    """時計のひと回り。誰も呼ばなくても回るものを、順に。"""
    planned = plan_visits(za.schedule_port)
    if planned:
        print(f"plan_visits: {len(planned)} visits ({', '.join(planned[:3])}…)"
              if len(planned) > 3 else f"plan_visits: {', '.join(planned)}")
    made = create(za.jobs, za.rules, za.active, za.origins, za.ids, za.clock)
    handed = hand_out(za.jobs, za.states, za.clock)
    returned = return_timed_out(za.jobs, za.states, za.clock)
    checked = run_check(za.jobs, za.states, za.results, za.clock)
    sorted_ = sort_failures(za.jobs, za.states, za.clock)
    confirmed = confirm(za.jobs, za.states, za.source, za.evidences, za.clock)
    overdue = mark_overdue(za.jobs, za.states, za.overdue_marks, za.clock)
    delivered = deliver_drafts(
        za.jobs, za.states, za.results, za.delivered_marks, za.drafts, za.clock
    )
    欠け = audit(za.active, za.origins, za.clock)
    for 名前, 版, 期間 in 欠け:
        print(f"! I8 active rule with no job — {名前.text} v{版} {期間.text}")
    # 出すのは §1 の操作の識別子そのまま——ログもまた読む人のもの
    for 名, 列 in (
        ("create", made),
        ("hand_out", handed),
        ("return_timed_out", returned),
        ("run_check", checked),
        ("sort_failures", sorted_),
        ("confirm", confirmed),
        ("mark_overdue", overdue),
        ("deliver_drafts", delivered),
    ):
        if 列:
            print(f"{名}: {', '.join(j.text for j in 列)}")


def _agent(za: Ichiza, name: str) -> None:
    """AI のひと回り——引き金は AI 自身。着手して進め、人の手が要る仕事に見立てを書く。"""
    ai = Agent(name=name)
    took = start(za.jobs, za.states, za.clock, by=ai)
    if isinstance(took, JobId):
        print(f"start: {took.text}")
        outcome = consult(
            za.jobs,
            za.work,
            za.source,
            za.llm,
            za.questions,
            za.results,
            za.evidences,
            za.assessments,
            za.clock,
            took,
            by=ai,
        )
        print(
            f"consult: {took.text}"
            if outcome is None
            else f"refused: {outcome.reason}"
        )
    visited = patrol(
        za.jobs, za.states, za.work, za.assessments, za.llm, za.clock, by=ai
    )
    if visited:
        print(f"assess: {', '.join(j.text for j in visited)}")


def _today(za: Ichiza, viewer: str) -> None:
    rows = gather_today(za.today, za.clock, viewer)
    if not rows:
        print("Nothing needs your judgment today.")
        return
    for r in rows:
        見出し = r.rule or r.request_head or ""
        print(
            f"[{r.id}] {見出し} {r.period or ''}  "
            f"{状態(r.state_name)}  {語('期日')} {r.due}"
        )
        print(f"  {語('やること')}: {r.instruction}")
        for 欄, 中身 in (
            ("質問", r.question_body),
            ("回答", r.answer_body),
            ("成果", r.result_body),
            ("根拠", r.evidence_quote),
        ):
            if 中身:
                print(f"  {語(欄)}: {中身}")
        for 見立て, 理由 in r.assessments:
            print(f"  {語('見立て')}: {見立て} ({理由})")
        print(f"  can press: {', '.join(操作(a) for a in r.actions)}")


def main() -> None:
    p = argparse.ArgumentParser(prog="ichiza", description="一座 — 判断は人間")
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument(
        "--llm",
        choices=sorted(_MODELS),
        default=os.environ.get("ICHIZA_LLM", "ollama"),
        help="LLM の道具。手元は ollama、クラウドは gemini",
    )
    p.add_argument("--model", default=None, help="既定は道具ごと（--llm を見る）")
    p.add_argument(
        "--dsn",
        default=os.environ.get("ICHIZA_LEDGER_DSN"),
        help="クラウドの帳簿の在りか。無ければ手元の data/ichiza.db",
    )
    p.add_argument(
        "--emr-dsn",
        default=os.environ.get("ICHIZA_EMR_DSN"),
        help="診療録（EMR）の在りか。無ければ db: の源は読めない",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tick")
    a = sub.add_parser("agent")
    a.add_argument("--name", default="一号")
    t = sub.add_parser("today")
    t.add_argument("--viewer", required=True)
    w = sub.add_parser("window")
    w.add_argument("--viewer", required=True)
    sv = sub.add_parser("serve")
    sv.add_argument("--viewer", required=True)
    ra = sub.add_parser("rule-add")
    ra.add_argument("--name", required=True)
    ra.add_argument("--by", required=True)
    rc = sub.add_parser("rule-activate")
    rc.add_argument("--name", required=True)
    rc.add_argument("--version", type=int, required=True)
    rc.add_argument("--by", required=True)
    rd = sub.add_parser("rule-deactivate")
    rd.add_argument("--name", required=True)
    rd.add_argument("--by", required=True)
    act = sub.add_parser("act")
    act.add_argument("what", choices=["approve", "send-back", "answer", "abandon"])
    act.add_argument("--id", required=True)
    act.add_argument("--by", required=True)
    act.add_argument("--text", default="", help="差し戻し・打ち切りの理由／回答の中身")
    args = p.parse_args()

    (args.root / "data").mkdir(exist_ok=True)
    za = Ichiza(args.root, args.model, args.llm, args.dsn, args.emr_dsn)

    if args.cmd == "window":
        # Qt は窓のときだけ読み込む——脈に起動コストを載せない。
        # 窓には手だけを注ぐ——画面は手の中身を知らない。
        from ui.shell import run

        h = _手(za, args.viewer)
        raise SystemExit(
            run(
                h.fetch,
                h.act,
                h.detail,
                h.schedule_fetch,
                h.schedule_act,
                h.history_fetch,
                h.search,
                h.request,
                h.upcoming,
            )  # type: ignore[arg-type]
        )

    if args.cmd == "serve":
        # web の器。**手は1回ごとに開いて閉じる**——器が帳簿を跨いで持たない。
        import uvicorn

        from ui.web import make_app

        def 開く() -> 手:
            return _手(
                Ichiza(args.root, args.model, args.llm, args.dsn, args.emr_dsn),
                args.viewer,
            )

        za.conn.close()  # 立てるだけの接続は持たない
        uvicorn.run(
            make_app(開く, args.viewer, os.environ.get("ICHIZA_MAPS_KEY")),
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "8080")),
        )
        return

    if args.cmd == "tick":
        _tick(za)
    elif args.cmd == "agent":
        _agent(za, args.name)
    elif args.cmd == "today":
        _today(za, args.viewer)
    elif args.cmd == "rule-add":
        断り = add_version(za.rules, za.topics, za.clock, args.name, args.by, VersionForm())
        print("add_version: ok" if 断り is None else f"refused: {断り.reason}")
    elif args.cmd == "rule-activate":
        断り = activate(za.rules, za.clock, args.name, args.version, args.by)
        print("activate: ok" if 断り is None else f"refused: {断り.reason}")
    elif args.cmd == "rule-deactivate":
        断り = deactivate(za.rules, za.clock, args.name, args.by)
        print("deactivate: ok" if 断り is None else f"refused: {断り.reason}")
    elif args.cmd == "act":
        if args.what == "approve":
            断り = approve(za.jobs, za.clock, args.id, args.by)
        elif args.what == "send-back":
            断り = send_back(za.jobs, za.clock, args.id, args.by, args.text)
        elif args.what == "answer":
            断り = answer(za.jobs, za.questions, za.clock, args.id, args.by, args.text)
        else:
            断り = abandon(za.jobs, za.clock, args.id, args.by, args.text)
        print(f"{args.what}: ok" if 断り is None else f"refused: {断り.reason}")
    za.conn.close()


if __name__ == "__main__":
    main()
