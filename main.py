"""組み立ての根 — 全層を束ねる唯一の場所。

マネージャーの輪と働き手を周期で回し、画面を開く。
どちらも帳簿越しにしか触れ合わない（誰も直接話さない）。
"""

from __future__ import annotations

import sys
import threading
import time
from datetime import datetime, timezone

from adapters.sqlite_ledger import SqliteLedger
from adapters.stub_llm import StubLlm
from app.actions import record_approval
from app.manager import create, dispatch, patrol, triage, verify
from app.worker import work
from domain.event import Event
from domain.participant import CapabilityDeclaration, Participant, announce
from ui.gui import VIEWER, run

DB = "data/ledger.db"


def _worker() -> Participant:
    declared = CapabilityDeclaration(
        model_name="stub",
        sensitivity_ok=False,
        accepts=("週次バックアップ確認",),
        reachable_ports=("読み口/バックアップ先",),
    )
    participant = Participant(participant_id="機体/w-01", kind="Agent", capability=declared)
    return announce(participant, frozenset({"stub"}), frozenset({"読み口/バックアップ先"}))


def _turn(ledger: SqliteLedger, worker: Participant) -> None:
    """1周 — マネージャーの輪と働き手を順に回す。全部が冪等なので、何度回しても同じ。

    1つの輪の失敗で他の輪を止めない。落ちた事実は帳簿に落とす（標準エラー出力に消さない）。
    """
    now = datetime.now(timezone.utc)
    rings = (
        ("create", lambda: create(ledger, now)),
        ("dispatch", lambda: dispatch(ledger, now)),
        ("patrol", lambda: patrol(ledger, now)),
        ("triage", lambda: triage(ledger, now)),
        ("work", lambda: work(ledger, StubLlm(), worker, now)),
        ("verify", lambda: verify(ledger, now, assignee_id=VIEWER)),
    )
    for name, ring in rings:
        try:
            ring()
        except Exception as error:
            _record_ring_failure(ledger, name, error, now)


def _record_ring_failure(
    ledger: SqliteLedger, ring: str, error: Exception, now: datetime
) -> None:
    """輪が落ちた事実を帳簿に落とす。帳簿にも書けないときだけ、最後の砦として標準エラー出力へ"""
    try:
        ledger.events.append(
            [
                Event(
                    kind="FailureOccurred",
                    at=now,
                    payload={"輪": ring, "理由": f"{type(error).__name__}: {error}"},
                )
            ]
        )
    except Exception as second:  # 帳簿にも書けない——ここだけは消えるのを許す
        print(f"帳簿に書けない（{ring}）: {error} / {second}", file=sys.stderr)


def _loop() -> None:
    # 帳簿の接続はスレッドごとに持つ（1接続＝1参加者——設計/8_保存 §2）
    ledger = SqliteLedger(DB)
    worker = _worker()
    while True:
        _turn(ledger, worker)  # 輪ごとに捕まえているので、ここでは落ちない
        time.sleep(3)


def _act(action: str, job_id: str) -> str | None:
    """画面から来た人の操作を帳簿に書き込む。断ったら理由を返す（押して何も起きないのをやめる）"""
    if action != "承認":
        return f"「{action}」はまだできません"
    done = record_approval(SqliteLedger(DB), job_id, by=VIEWER, now=datetime.now(timezone.utc))
    if done:
        return None
    return "承認できませんでした（担当ではないか、もう承認済みです）"


if __name__ == "__main__":
    threading.Thread(target=_loop, daemon=True).start()
    sys.exit(run(SqliteLedger(DB), _act))
