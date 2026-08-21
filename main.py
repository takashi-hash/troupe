"""組み立ての根 — 全層を束ねる唯一の場所。

  uv run python main.py            画面を開く（輪と働き手も回る）
  uv run python main.py inject 運転  カスタムを注入する（人の操作。自動では走らない）

マネージャーの輪と働き手を周期で回し、画面を開く。
どちらも帳簿越しにしか触れ合わない（誰も直接話さない）。
"""

from __future__ import annotations

import sys
import threading
import time
from datetime import datetime, timezone
from typing import Mapping

from adapters.sqlite_ledger import SqliteLedger
from adapters.stub_llm import StubLlm
from adapters.sources import sources_of
from adapters.toml_custom import TomlCustom
from app.injection import inject
from app.actions import record_approval
from app.manager import confirm, create, dispatch, patrol, triage, verify
from app.worker import work
from domain.event import Event
from domain.participant import CapabilityDeclaration, Participant, announce
from domain.ports import LlmPort, SourcePort
from ui.gui import VIEWER, run

DB = "data/ledger.db"
TOPIC = "運転"  # いまの題材（custom/<題材>/）


# 機体が名乗る中身——**人が書く**。実態から作ってはいけない（作ると照合が空回りする）
DECLARED = CapabilityDeclaration(
    model_name="stub",
    sensitivity_ok=False,
    accepts=("週次の依存の棚卸し", "週次の検査の見張り", "週次の設計と実装の突合"),
    reachable_ports=("読み口/依存の一覧", "読み口/検査の結果", "読み口/設計文書"),
)


def _worker(ledger: SqliteLedger, llm: LlmPort, sources: Mapping[str, SourcePort]) -> Participant:
    """働き手を名乗らせて、帳簿に載せる。

    **申告は人が書き、実態は実物から取る**（教訓8——申告と実態のずれが最大の事故源）。
    2026-08-21 まで、実在しない業務ルールと口を申告し、その同じ文字列を「実態」として
    渡していた。申告と申告を突き合わせても照合にならない。
    いま実態として渡すのは、本当に読める源の鍵と、本当に居る LLM の名。

    名簿に載せるところまでが名乗り——載せないと、誰が働いているかを帳簿が知らない。
    """
    named = announce(
        Participant(participant_id="機体/w-01", kind="Agent", capability=DECLARED),
        frozenset({llm.name}),
        frozenset(sources),
    )
    if ledger.participants.get(named.participant_id) is None:  # 冪等——二度は載せない
        ledger.participants.put(
            named,
            [
                Event(
                    kind="Announced",
                    at=datetime.now(timezone.utc),
                    payload={"participant": named.participant_id, "model": named.capability.model_name},
                )
            ],
        )
    return named


def _turn(
    ledger: SqliteLedger, worker: Participant, llm: LlmPort, sources: Mapping[str, SourcePort]
) -> None:
    """1周 — マネージャーの輪と働き手を順に回す。全部が冪等なので、何度回しても同じ。

    1つの輪の失敗で他の輪を止めない。落ちた事実は帳簿に落とす（標準エラー出力に消さない）。
    """
    now = datetime.now(timezone.utc)
    rings = (
        ("create", lambda: create(ledger, now)),
        ("dispatch", lambda: dispatch(ledger, now)),
        ("patrol", lambda: patrol(ledger, now)),
        ("triage", lambda: triage(ledger, now)),
        ("work", lambda: work(ledger, llm, worker, now, sources)),
        ("verify", lambda: verify(ledger, now, assignee_id=VIEWER)),
        ("confirm", lambda: confirm(ledger, now)),
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
    llm = StubLlm()
    sources = sources_of(f"custom/{TOPIC}")
    worker = _worker(ledger, llm, sources)
    while True:
        _turn(ledger, worker, llm, sources)  # 輪ごとに捕まえているので、ここでは落ちない
        time.sleep(3)


def _act(action: str, job_id: str) -> str | None:
    """画面から来た人の操作を帳簿に書き込む。断ったら理由を返す（押して何も起きないのをやめる）"""
    if action != "承認":
        return f"「{action}」はまだできません"
    done = record_approval(SqliteLedger(DB), job_id, by=VIEWER, now=datetime.now(timezone.utc))
    if done:
        return None
    return "承認できませんでした（担当ではないか、もう承認済みです）"


def _inject(topic: str) -> None:
    """カスタムを注入する — 人の操作。誰が入れたかは出来事に残る"""
    touched = inject(
        SqliteLedger(DB),
        TomlCustom(f"custom/{topic}"),
        by=VIEWER,
        now=datetime.now(timezone.utc),
    )
    print(f"注入しました: {'、'.join(touched)}" if touched else "変わりはありません")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "inject":
        _inject(sys.argv[2])
        sys.exit(0)
    threading.Thread(target=_loop, daemon=True).start()
    sys.exit(run(SqliteLedger(DB), _act))
