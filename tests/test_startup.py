"""起動のテスト — 組み立ての根（main.py）に手が届いていなかったところ。

2026-08-21 まで main.py は型検査にも入っておらず、テストも1つも無かった。
その死角で、実在しない業務ルールと口を申告し、**その同じ文字列を「実態」として渡す**
という照合が置かれていた（申告と申告の突き合わせ——照合になっていない）。
"""

from datetime import datetime, timezone

import pytest

import main
from adapters.sqlite_ledger import SqliteLedger
from adapters.sources import sources_of
from adapters.stub_llm import StubLlm
from domain.participant import MismatchedDeclaration

TOPIC = "運転"


class OtherLlm:
    """別の LLM — 申告と違う実態の体"""

    @property
    def name(self) -> str:
        return "other"

    def chat(self, prompt: str) -> str:
        return ""


@pytest.fixture()
def ledger(tmp_path) -> SqliteLedger:
    return SqliteLedger(str(tmp_path / "ledger.db"))


def test_announcing_puts_the_worker_on_the_roster(ledger: SqliteLedger) -> None:
    """名乗ると名簿に載る——載せないと、誰が働いているかを帳簿が知らない"""
    worker = main._worker(ledger, StubLlm(), sources_of(f"custom/{TOPIC}"))
    assert worker.verified is True
    assert ledger.participants.get(worker.participant_id) is not None
    assert [e.kind for e in ledger.recent_events() if e.kind == "Announced"] == ["Announced"]


def test_announcing_twice_adds_one_entry(ledger: SqliteLedger) -> None:
    """二度名乗っても名簿は1件（起動し直しが怖くない——I8 の土台）"""
    sources = sources_of(f"custom/{TOPIC}")
    main._worker(ledger, StubLlm(), sources)
    main._worker(ledger, StubLlm(), sources)
    assert len([e for e in ledger.recent_events() if e.kind == "Announced"]) == 1


def test_a_port_that_is_not_really_there_cannot_be_announced(ledger: SqliteLedger) -> None:
    """申告した口に手が届かなければ名乗れない——申告と実態のずれは起動で止める（教訓8）"""
    sources = sources_of(f"custom/{TOPIC}")
    fewer = {key: sources[key] for key in list(sources)[:2]}
    with pytest.raises(MismatchedDeclaration):
        main._worker(ledger, StubLlm(), fewer)


def test_a_model_that_is_not_really_there_cannot_be_announced(ledger: SqliteLedger) -> None:
    """申告した LLM が実態に無ければ名乗れない"""
    with pytest.raises(MismatchedDeclaration):
        main._worker(ledger, OtherLlm(), sources_of(f"custom/{TOPIC}"))


def test_the_declaration_is_written_by_hand_not_derived(ledger: SqliteLedger) -> None:
    """申告は実態から作らない——作ると必ず一致し、照合が空回りする。

    ここが破れているかは「実態を減らすと名乗れなくなるか」で分かる。
    上の2つが赤くならなくなったら、申告が実態から作られている。
    """
    sources = sources_of(f"custom/{TOPIC}")
    assert set(main.DECLARED.reachable_ports) == set(sources)  # いまは一致している
    assert main._worker(ledger, StubLlm(), sources).verified is True
    with pytest.raises(MismatchedDeclaration):  # 実態だけ減らすと破れる
        main._worker(ledger, StubLlm(), {})


def test_the_turn_survives_a_ring_that_falls(ledger: SqliteLedger) -> None:
    """1つの輪が落ちても他の輪は回り、落ちた事実は帳簿に残る（標準エラー出力に消さない）"""
    sources = sources_of(f"custom/{TOPIC}")
    worker = main._worker(ledger, StubLlm(), sources)
    broken = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
    main._record_ring_failure(ledger, "create", RuntimeError("帳簿が塞がっている"), broken)
    failures = [e for e in ledger.recent_events() if e.kind == "FailureOccurred"]
    assert failures and failures[0].payload["輪"] == "create"
    assert worker.verified is True
