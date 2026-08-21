"""働き手と、検証・見回りの輪のテスト — 偽の LLM で全遷移を決定的に回す。

設計/9_働き手/働き手とLLM.md §6 の表を1行=1テストで写す。
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from adapters.sqlite_ledger import SqliteLedger
from app.human import record_approval
from app.manager import confirm, create, dispatch, patrol, triage, verify, surface
from app.worker import work
from domain.board import Board, Constitution, freeze
from domain.definition import Definition, Version
from domain.event import Event
from domain.job import Budget, CannotTake, Job, Ready, Verifying, take
from domain.verification import Blocked, Passed, check
from domain.participant import CapabilityDeclaration, MismatchedDeclaration, Participant, announce
from tests.fake_llm import BrokenSource, FakeLlm, FakeSource

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
SOURCES = {"読み口/検査の結果": FakeSource()}
ASSIGNEE = "人/座長"
GOOD_BODY = "検査は緑でした（2026-08-21 実施・72件）。"


def capability(sensitivity_ok: bool = True, ports: tuple[str, ...] = ("読み口/検査の結果",)):
    return CapabilityDeclaration(
        model_name="qwen3:8b",
        sensitivity_ok=sensitivity_ok,
        accepts=("週次の検査の見張り",),
        reachable_ports=ports,
    )


def worker(verified: bool = True, **kwargs) -> Participant:
    return Participant(
        participant_id="機体/w-01", kind="Agent", capability=capability(**kwargs), verified=verified
    )


def seed(
    ledger: SqliteLedger,
    checkpoint: str | None = "座長の承認",
    must=("2026-",),
    budget: Budget = Budget(calls=20, seconds=600),
    max_retries: int = 3,
    needs_apply: bool = False,
) -> None:
    definition = Definition(
        name="週次の検査の見張り",
        board_id="ボード/運転",
        versions=(
            Version(
                number=1,
                instruction="検査が緑かを確かめ、赤があれば何が壊れたかを書く",
                acceptance="検査の結果が引用されている",
                cadence="weekly",
                deadline_days=2,
                budget=budget,
                max_retries=max_retries,
                source_refs=("読み口/検査の結果",),
                must_contain=must,
                checkpoint_position=checkpoint,
                needs_apply=needs_apply,
            ),
        ),
        enacted=1,
    )
    ledger.definitions.put(
        definition,
        [Event(kind="VersionAppended", at=NOW), Event(kind="DefinitionEnacted", at=NOW)],
    )
    board = Board(
        board_id="ボード/運転",
        constitutions=(
            Constitution(
                number=1,
                purpose="Ichiza 自身の運転を回す",
                non_goals="診療の中身には触れない",
                acceptance="根拠で閉じられること",
                vocabulary="リポジトリ・依存・バックアップ先",
            ),
        ),
    )
    ledger.boards.put(
        freeze(board, 1),
        [Event(kind="ConstitutionAppended", at=NOW), Event(kind="ConstitutionFrozen", at=NOW)],
    )
    create(ledger, NOW)
    dispatch(ledger, NOW)


@pytest.fixture
def ledger(tmp_path: Path) -> SqliteLedger:
    return SqliteLedger(tmp_path / "ledger.db")


def test_announce_rejects_mismatched_declaration() -> None:
    """申告と実態がずれていたら名乗れない（教訓8）"""
    with pytest.raises(MismatchedDeclaration):
        announce(worker(verified=False), frozenset({"別のモデル"}), frozenset({"読み口/検査の結果"}))
    with pytest.raises(MismatchedDeclaration):
        announce(worker(verified=False), frozenset({"qwen3:8b"}), frozenset())


def test_announce_marks_verified() -> None:
    """照合を通ったら名乗れる"""
    named = announce(worker(verified=False), frozenset({"qwen3:8b"}), frozenset({"読み口/検査の結果"}))
    assert named.verified is True


def test_unverified_cannot_take(ledger: SqliteLedger) -> None:
    """照合を通っていない参加者は着手できない"""
    seed(ledger)
    assert work(ledger, FakeLlm(GOOD_BODY), worker(verified=False), NOW, SOURCES) is None


def test_out_of_reach_source_cannot_be_taken(ledger: SqliteLedger) -> None:
    """手が届かない源を指すタスクは着手できない"""
    seed(ledger)
    assert work(ledger, FakeLlm(GOOD_BODY), worker(ports=("読み口/別のもの",)), NOW, SOURCES) is None


def test_sensitive_briefing_needs_declared_capability(ledger: SqliteLedger) -> None:
    """機微の印がある作業情報は、機微可の申告がある者だけが着手できる"""
    seed(ledger)
    (job_id,) = ledger.jobs.find_by_state("Ready")
    got = ledger.jobs.get(job_id)
    assert got is not None
    job, _ = got
    state = job.state
    assert isinstance(state, Ready)
    sensitive_job = job.model_copy(
        update={
            "state": state.model_copy(
                update={"briefing": state.briefing.model_copy(update={"sensitive": True})}
            )
        }
    )
    with pytest.raises(CannotTake):
        take(sensitive_job, worker(sensitivity_ok=False), NOW)


def test_work_takes_and_submits(ledger: SqliteLedger) -> None:
    """働くと、札を取り、成果物を置いて検証中まで進む"""
    seed(ledger)
    llm = FakeLlm(GOOD_BODY)
    job_id = work(ledger, llm, worker(), NOW, SOURCES)
    assert job_id is not None
    got = ledger.jobs.get(job_id)
    assert got is not None
    verifying = got[0].state
    assert isinstance(verifying, Verifying)
    artifact = ledger.artifacts.get(verifying.artifact_ref)
    assert artifact is not None and artifact.body == GOOD_BODY
    assert "このボードの言葉" in llm.prompts[0]  # 方針の言葉が注入されている


def test_prompt_is_pure(ledger: SqliteLedger) -> None:
    """同じ作業情報からは同じプロンプト（純粋関数）"""
    seed(ledger)
    first = FakeLlm(GOOD_BODY)
    work(ledger, first, worker(), NOW, SOURCES)
    ledger2 = SqliteLedger(":memory:")
    seed(ledger2)
    second = FakeLlm(GOOD_BODY)
    work(ledger2, second, worker(), NOW, SOURCES)
    assert first.prompts[0] == second.prompts[0]


def test_check_blocks_missing_words() -> None:
    """チェックは必ず含む語が無ければ止める（止める力を持つ）"""
    assert isinstance(check("日付がありません", ("2026-",)), Blocked)
    assert isinstance(check(GOOD_BODY, ("2026-",)), Passed)
    assert isinstance(check("   ", ()), Blocked)


def test_verify_sends_to_checkpoint(ledger: SqliteLedger) -> None:
    """チェックが通り、承認待ちの位置があれば承認待ちへ"""
    seed(ledger)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    (job_id,) = verify(ledger, NOW, ASSIGNEE)
    got = ledger.jobs.get(job_id)
    assert got is not None
    checkpoint = got[0].state
    assert checkpoint.kind == "Checkpoint"
    assert getattr(checkpoint, "assignee_id") == ASSIGNEE


def test_verify_without_checkpoint_goes_confirmed(ledger: SqliteLedger) -> None:
    """承認待ちの位置が無ければ承認済みへ直行する"""
    seed(ledger, checkpoint=None)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    (job_id,) = verify(ledger, NOW, ASSIGNEE)
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "Confirmed"


def test_blocked_artifact_returns_to_ready(ledger: SqliteLedger) -> None:
    """チェックが止めたら未着手へ戻り、理由が出来事に残る"""
    seed(ledger)
    work(ledger, FakeLlm("日付を書き忘れました"), worker(), NOW, SOURCES)
    (job_id,) = verify(ledger, NOW, ASSIGNEE)
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "Ready"
    rows = ledger._con.execute("SELECT COUNT(*) FROM events WHERE kind='CheckBlocked'").fetchone()
    assert rows[0] == 1


def test_patrol_returns_expired_lease(ledger: SqliteLedger) -> None:
    """期限の切れた札は見回りが切り、タスクは未着手へ戻る（I4「消えない」）"""
    seed(ledger)
    llm = FakeLlm()  # 応答を返さない＝働き手が落ちた体
    (job_id,) = ledger.jobs.find_by_state("Ready")
    got = ledger.jobs.get(job_id)
    assert got is not None
    job, rev = got
    running = take(job, worker(), NOW)
    ledger.jobs.put(running, rev, [Event(kind="LeaseTaken", at=NOW, job_id=job_id)])
    assert patrol(ledger, NOW) == []  # まだ切れていない
    assert patrol(ledger, NOW + timedelta(hours=1)) == [job_id]
    got2 = ledger.jobs.get(job_id)
    assert got2 is not None and got2[0].state.kind == "Ready"
    assert llm.prompts == []


def test_approve_only_by_assignee(ledger: SqliteLedger) -> None:
    """承認できるのは担当した人だけ——押した事実は出来事に残る（I2）"""
    seed(ledger)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    (job_id,) = verify(ledger, NOW, ASSIGNEE)
    assert record_approval(ledger, job_id, by="人/事務", now=NOW) is False
    assert record_approval(ledger, job_id, by=ASSIGNEE, now=NOW) is True
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "Confirmed"
    rows = ledger._con.execute(
        "SELECT COUNT(*) FROM events WHERE kind='CheckpointApproved'"
    ).fetchone()
    assert rows[0] == 1


def test_budget_stops_the_worker(ledger: SqliteLedger) -> None:
    """使用上限を使い切っていたら LLM を呼ばずに内容エラーへ落とす（自動で使い続けない）"""
    seed(ledger, budget=Budget(calls=0, seconds=600))
    llm = FakeLlm(GOOD_BODY)
    job_id = work(ledger, llm, worker(), NOW, SOURCES)
    assert job_id is not None
    assert llm.prompts == []  # 一度も話しかけていない
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "ContentFailure"
    rows = ledger._con.execute(
        "SELECT COUNT(*) FROM events WHERE kind='BudgetExceeded'"
    ).fetchone()
    assert rows[0] == 1


class BrokenLlm:
    """落ちる LLM の口 — 本物が落ちたときの体（接続断・タイムアウト）"""

    def __init__(self) -> None:
        self.calls = 0

    @property
    def name(self) -> str:
        return "broken"

    def chat(self, prompt: str) -> str:
        self.calls += 1
        raise ConnectionError("LLM に繋がらない")


def test_worker_falls_into_environment_failure(ledger: SqliteLedger) -> None:
    """LLM が落ちても例外は外へ逃げず、環境エラーとして帳簿に残る（握りつぶさない）"""
    seed(ledger)
    job_id = work(ledger, BrokenLlm(), worker(), NOW, SOURCES)
    assert job_id is not None
    got = ledger.jobs.get(job_id)
    assert got is not None
    state = got[0].state
    assert state.kind == "EnvironmentFailure"
    assert "LLM に繋がらない" in getattr(state, "reason")
    rows = ledger._con.execute(
        "SELECT COUNT(*) FROM events WHERE kind='FailureOccurred'"
    ).fetchone()
    assert rows[0] == 1


def test_triage_retries_then_gives_up(ledger: SqliteLedger) -> None:
    """環境エラーは再試行され、尽きたら内容エラーで人へ（永久に繰り返さない）"""
    seed(ledger, max_retries=2)
    broken = BrokenLlm()
    for _ in range(5):  # 何周回しても、いつか止まる
        work(ledger, broken, worker(), NOW, SOURCES)
        triage(ledger, NOW)
    (job_id,) = ledger.jobs.find_by_state("ContentFailure")
    got = ledger.jobs.get(job_id)
    assert got is not None
    assert "再試行が尽きた" in getattr(got[0].state, "reason")
    assert broken.calls == 3  # 最初の1回＋再試行2回で打ち止め
    retried = ledger._con.execute(
        "SELECT COUNT(*) FROM events WHERE kind='Retried'"
    ).fetchone()
    assert retried[0] == 2


def test_environment_failure_keeps_briefing(ledger: SqliteLedger) -> None:
    """環境エラーは作業情報を持って帰る——だから未着手へ戻れる"""
    seed(ledger)
    job_id = work(ledger, BrokenLlm(), worker(), NOW, SOURCES)
    assert job_id is not None
    triage(ledger, NOW)
    got = ledger.jobs.get(job_id)
    assert got is not None
    state = got[0].state
    assert isinstance(state, Ready)
    assert state.briefing.definition_ref == "業務ルール/週次の検査の見張り/1"


# ---- 源を読む・証拠・完了（段4） ----


def test_worker_reads_sources_into_the_prompt(ledger: SqliteLedger) -> None:
    """働き手は源を読み、読んだ中身を材料としてプロンプトに入れる"""
    seed(ledger)
    source = FakeSource("検査は緑でした（72件）")
    llm = FakeLlm(GOOD_BODY)
    work(ledger, llm, worker(), NOW, {"読み口/検査の結果": source})
    assert source.reads == 1
    assert "源から読んだもの" in llm.prompts[0]
    assert "72件" in llm.prompts[0]


def test_unreadable_source_falls_into_environment_failure(ledger: SqliteLedger) -> None:
    """源が読めなければ環境エラー——例外を外へ逃がさない（握りつぶさない）"""
    seed(ledger)
    job_id = work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, {"読み口/検査の結果": BrokenSource()})
    assert job_id is not None
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "EnvironmentFailure"
    assert "源が読めない" in getattr(got[0].state, "reason")


def test_unconnected_source_falls_into_environment_failure(ledger: SqliteLedger) -> None:
    """読み口が繋がっていなければ環境エラー——黙って読まずに進まない"""
    seed(ledger)
    job_id = work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, {})
    assert job_id is not None
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "EnvironmentFailure"


def test_evidence_is_placed_with_quote_and_fingerprint(ledger: SqliteLedger) -> None:
    """証拠は引用と指紋を持つ——何をどこから読んだかが残る（I5）"""
    seed(ledger)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    evidence = ledger.evidences.get("証拠/成果物/週次の検査の見張り/2026-W34")
    assert evidence is not None
    assert evidence.readings[0].source_ref == "読み口/検査の結果"
    assert "72件" in evidence.readings[0].quote
    assert len(evidence.fingerprint) == 16


def test_confirm_closes_with_evidence(ledger: SqliteLedger) -> None:
    """確かめる輪が、証拠を照合してタスクを完了にする（閉じるのはマネージャー）"""
    seed(ledger)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    (job_id,) = verify(ledger, NOW, ASSIGNEE)
    record_approval(ledger, job_id, by=ASSIGNEE, now=NOW)
    assert confirm(ledger, NOW) == [job_id]
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "ClosedWithEvidence"
    rows = ledger._con.execute("SELECT COUNT(*) FROM events WHERE kind='JobClosed'").fetchone()
    assert rows[0] == 1


def test_apply_cannot_be_skipped(ledger: SqliteLedger) -> None:
    """適用が要る業務ルールのタスクは、承認済みから直には閉じられない"""
    seed(ledger, needs_apply=True)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    (job_id,) = verify(ledger, NOW, ASSIGNEE)
    record_approval(ledger, job_id, by=ASSIGNEE, now=NOW)
    assert confirm(ledger, NOW) == []  # 閉じない
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "Confirmed"


def test_close_without_evidence_needs_a_recheck_deadline() -> None:
    """読み口の無いタスクは自己申告＋確かめの期限でしか閉じられない"""
    from domain.job import CannotClose, close

    job = job_at_confirmed()
    with pytest.raises(CannotClose):
        close(job, evidence_ref=None, needs_apply=False, recheck_deadline=None)
    closed = close(job, None, False, recheck_deadline=NOW + timedelta(days=7))
    assert closed.state.kind == "ClosedBySelfReport"


def job_at_confirmed() -> Job:
    """承認済みのタスクを1つ作る（閉じる門を確かめるため）"""
    from domain.job import Confirmed, Core, FromDefinition

    return Job(
        core=Core(
            job_id="タスク-x",
            origin=FromDefinition(definition_name="週次の検査の見張り", version=1, period="2026-W34"),
            board_id="ボード/運転",
            ready_at=NOW,
            deadline=NOW + timedelta(days=3),
            budget=Budget(calls=20, seconds=600),
        ),
        state=Confirmed(artifact_ref="成果物/x"),
    )


def test_confirm_waits_for_evidence(ledger: SqliteLedger) -> None:
    """証拠がまだ無ければ閉じない——人の報告は待たない（証拠で閉じる）"""
    seed(ledger)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    (job_id,) = verify(ledger, NOW, ASSIGNEE)
    record_approval(ledger, job_id, by=ASSIGNEE, now=NOW)
    ledger._con.execute("DELETE FROM evidences") if False else None
    # 証拠を消す（積むだけの列なので、消せるのはテストの中の抜け道だけ）
    ledger._con.executescript("DROP TRIGGER evidences_no_delete; DELETE FROM evidences;")
    assert confirm(ledger, NOW) == []
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "Confirmed"


def test_verify_refuses_a_job_it_cannot_judge(ledger: SqliteLedger) -> None:
    """裁く版が引けないタスクは合格にしない——空の基準で通すと、承認まで飛ばしてしまう。

    これが CheckpointBypassed を作る道: version が引けないと must_contain は空、checkpoint_position も
    None になり、検証中→承認済みへ一直線に進む。型はこの道を禁じられない（承認が要るかを
    知っているのは状態ではなく版だから）。**帳簿は道具より長生きする**ので、コードの守りだけ
    では足りない——ここでは業務ルールの行が無い帳簿（復元・移行のあと）を作って確かめる。
    """
    seed(ledger)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    (job_id,) = [j.core.job_id for j in ledger.all_jobs()]
    ledger.connection.execute("DELETE FROM definitions")  # 帳簿から業務ルールが消えた
    assert verify(ledger, NOW, ASSIGNEE) == []
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "Verifying"  # 止まったまま、surface が赤で並べる


def test_surface_judges_by_the_birth_version_not_by_what_is_enacted(
    ledger: SqliteLedger,
) -> None:
    """有効でない業務ルールから生まれたタスクでも、版は引ける——**生まれた版で裁かれる**。

    有効なものだけで引くと、有効化を解いた業務ルールのタスクが一斉に
    「版が引けない」赤になる（狼少年を作る）。

    有効化を解く道はまだ無い（出来事の種が無い——ドメインモデル §11 未決#11）ので、
    ここでは帳簿に直接その形を書いて確かめる。帳簿は道具より長生きするので、
    「いまのコードが書かない形」も帳簿には現れうる。
    """
    seed(ledger)
    work(ledger, FakeLlm(GOOD_BODY), worker(), NOW, SOURCES)
    known = ledger.definitions.get("週次の検査の見張り")
    assert known is not None
    ledger.connection.execute(
        "UPDATE definitions SET state=? WHERE id=?",
        (known.model_copy(update={"enacted": None}).model_dump_json(), known.name),
    )
    assert ledger.enacted_definitions() == ()
    assert len(ledger.all_definitions()) == 1
    assert surface(ledger, NOW, ASSIGNEE) == ()  # 赤くならない
