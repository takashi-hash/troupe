"""組み立ての根。層に属さない。**具体を注ぐのはここだけ。**

設計: 設計/どう作るか §5。

帳簿は SQLite（data/ichiza.db）、LLM はローカル（Ollama）、源はファイル、
題材は custom/ のフォルダ。注ぎ先はすべて宣言（Protocol）——中身は誰も知らない。

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
from pathlib import Path

from adapters.acl.llm import OllamaLlm
from adapters.acl.source import FileSource
from adapters.clock import SystemClock
from adapters.ids import UuidIds
from adapters.ledger.db import open_ledger
from adapters.ledger.jobs import SqliteJobs
from adapters.ledger.reading import (
    SqliteActiveRules,
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
from app.dto.version_form import VersionForm
from app.services.agent.consult import consult
from app.services.agent.patrol import patrol
from app.services.agent.start import start
from app.services.clock.audit import audit
from app.services.clock.confirm import confirm
from app.services.clock.create import create
from app.services.clock.hand_out import hand_out
from app.services.clock.mark_overdue import mark_overdue
from app.services.clock.return_timed_out import return_timed_out
from app.services.clock.run_check import run_check
from app.services.clock.sort_failures import sort_failures
from app.services.human.abandon import abandon
from app.services.human.activate import activate
from app.services.human.add_version import add_version, add_version_from_fields
from app.services.human.answer import answer
from app.services.human.deactivate import deactivate
from app.services.human.approve import approve
from app.services.human.request import request_from_fields
from app.services.human.send_back import send_back
from app.services.screen.gather_detail import gather_detail
from app.services.screen.gather_history import gather_history
from app.services.screen.gather_schedule import gather_schedule
from app.services.screen.gather_search import gather_search
from app.services.screen.gather_today import gather_today
from domain.value_objects.job.job_id import JobId
from domain.value_objects.people.agent import Agent


class Ichiza:
    """一座 — 注いだ口の束。"""

    def __init__(self, root: Path, model: str) -> None:
        self.conn = open_ledger(root / "data" / "ichiza.db")
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
        self.history = SqliteHistory(self.conn)
        self.search_hits = SqliteSearch(self.conn)
        self.clock = SystemClock()
        self.ids = UuidIds()
        self.source = FileSource(root)
        self.topics = FolderTopic(root / "custom")
        self.llm = OllamaLlm(model=model)


def _tick(za: Ichiza) -> None:
    """時計のひと回り。誰も呼ばなくても回るものを、順に。"""
    made = create(za.jobs, za.rules, za.active, za.origins, za.ids, za.clock)
    handed = hand_out(za.jobs, za.states, za.clock)
    returned = return_timed_out(za.jobs, za.states, za.clock)
    checked = run_check(za.jobs, za.states, za.results, za.clock)
    sorted_ = sort_failures(za.jobs, za.states, za.clock)
    confirmed = confirm(za.jobs, za.states, za.source, za.evidences, za.clock)
    overdue = mark_overdue(za.jobs, za.states, za.overdue_marks, za.clock)
    欠け = audit(za.active, za.origins, za.clock)
    for 名前, 版, 期間 in 欠け:
        print(f"⚠ I8: 有効なのに仕事が無い — {名前.text} 版{版} {期間.text}")
    for 名, 列 in (
        ("作った", made),
        ("配った", handed),
        ("時間切れ", returned),
        ("検査した", checked),
        ("仕分けた", sorted_),
        ("確かめた", confirmed),
        ("期日切れ", overdue),
    ):
        if 列:
            print(f"{名}: {'、'.join(j.text for j in 列)}")


def _agent(za: Ichiza, name: str) -> None:
    """AI のひと回り——引き金は AI 自身。着手して進め、人の手が要る仕事に見立てを書く。"""
    ai = Agent(name=name)
    took = start(za.jobs, za.states, za.clock, by=ai)
    if isinstance(took, JobId):
        print(f"着手した: {took.text}")
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
        )
        print(f"進めた: {took.text}" if outcome is None else f"断り: {outcome.reason}")
    visited = patrol(
        za.jobs, za.states, za.work, za.assessments, za.llm, za.clock, by=ai
    )
    if visited:
        print(f"見立てを書いた: {'、'.join(j.text for j in visited)}")


def _today(za: Ichiza, viewer: str) -> None:
    rows = gather_today(za.today, za.clock, viewer)
    if not rows:
        print("今日は空です")
        return
    for r in rows:
        見出し = r.rule or r.request_head or ""
        print(f"[{r.id}] {見出し} {r.period or ''}  {r.state_name}  期日 {r.due}")
        print(f"  やること: {r.instruction}")
        if r.question_body:
            print(f"  質問: {r.question_body}")
        if r.result_body:
            print(f"  成果: {r.result_body}")
        if r.evidence_quote:
            print(f"  根拠: {r.evidence_quote}")
        for 見立て, 理由 in r.assessments:
            print(f"  見立て: {見立て}（{理由}）")
        print(f"  押せる: {'、'.join(r.actions)}")


def main() -> None:
    p = argparse.ArgumentParser(prog="ichiza", description="一座 — 判断は人間")
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--model", default="gpt-oss:20b")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tick")
    a = sub.add_parser("agent")
    a.add_argument("--name", default="一号")
    t = sub.add_parser("today")
    t.add_argument("--viewer", required=True)
    w = sub.add_parser("window")
    w.add_argument("--viewer", required=True)
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
    za = Ichiza(args.root, args.model)

    if args.cmd == "window":
        # Qt は窓のときだけ読み込む——launchd の脈に起動コストを載せない。
        # 窓には手だけを注ぐ——画面は手の中身を知らない。
        from app.dto.row_filter import RowFilter
        from ui.shell import run

        def 読む() -> tuple[object, ...]:
            return gather_today(za.today, za.clock, args.viewer)

        def 押す(what: str, id: str, text: str) -> str | None:
            if what == "answer":
                断り = answer(za.jobs, za.questions, za.clock, id, args.viewer, text)
            elif what == "approve":
                断り = approve(za.jobs, za.clock, id, args.viewer)
            elif what == "send_back":
                断り = send_back(za.jobs, za.clock, id, args.viewer, text)
            elif what == "abandon":
                断り = abandon(za.jobs, za.clock, id, args.viewer, text)
            else:
                return f"知らない操作です: {what}"
            return None if 断り is None else 断り.reason

        def 詳細(id: str) -> object | None:
            return gather_detail(za.today, za.details, za.clock, args.viewer, id)

        def 予定を読む() -> tuple[object, ...]:
            return gather_schedule(za.rule_lines, za.active, za.origins, za.clock)

        def 決まりを押す(what: str, name: str, version: int, fields: dict[str, str]) -> str | None:
            if what == "add_version":
                断り = add_version_from_fields(za.rules, za.topics, za.clock, name, args.viewer, fields)
            elif what == "activate":
                断り = activate(za.rules, za.clock, name, version, args.viewer)
            elif what == "deactivate":
                断り = deactivate(za.rules, za.clock, name, args.viewer)
            else:
                return f"知らない操作です: {what}"
            return None if 断り is None else 断り.reason

        def 履歴を読む() -> tuple[object, ...]:
            return gather_history(za.history)

        def 検索する(filter: RowFilter) -> tuple[object, ...]:
            return gather_search(za.search_hits, filter)

        def 頼む(body: str, fields: dict[str, str]) -> str | None:
            断り = request_from_fields(za.jobs, za.ids, za.clock, args.viewer, body, fields)
            return None if 断り is None else 断り.reason

        raise SystemExit(
            run(読む, 押す, 詳細, 予定を読む, 決まりを押す, 履歴を読む, 検索する, 頼む)  # type: ignore[arg-type]
        )

    if args.cmd == "tick":
        _tick(za)
    elif args.cmd == "agent":
        _agent(za, args.name)
    elif args.cmd == "today":
        _today(za, args.viewer)
    elif args.cmd == "rule-add":
        断り = add_version(za.rules, za.topics, za.clock, args.name, args.by, VersionForm())
        print("積んだ" if 断り is None else f"断り: {断り.reason}")
    elif args.cmd == "rule-activate":
        断り = activate(za.rules, za.clock, args.name, args.version, args.by)
        print("有効にした" if 断り is None else f"断り: {断り.reason}")
    elif args.cmd == "rule-deactivate":
        断り = deactivate(za.rules, za.clock, args.name, args.by)
        print("止めた" if 断り is None else f"断り: {断り.reason}")
    elif args.cmd == "act":
        if args.what == "approve":
            断り = approve(za.jobs, za.clock, args.id, args.by)
        elif args.what == "send-back":
            断り = send_back(za.jobs, za.clock, args.id, args.by, args.text)
        elif args.what == "answer":
            断り = answer(za.jobs, za.questions, za.clock, args.id, args.by, args.text)
        else:
            断り = abandon(za.jobs, za.clock, args.id, args.by, args.text)
        print("できた" if 断り is None else f"断り: {断り.reason}")
    za.conn.close()


if __name__ == "__main__":
    main()
