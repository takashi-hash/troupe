"""LLM に問う（app）の壊しかた。設計/仕事が回る筋道.md §1「AI が始めるもの」。"""

from __future__ import annotations

from typing import Any

from app.ports.source_port import Quote, Unreadable
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.rule.source import Source as 源の型
from app.ports.work_reader import WorkMaterial
from app.services.agent.consult import consult
from app.services.refusal import Refusal
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import AwaitingAnswer, Failed, InProgress, Ready, Submitted
from domain.events.job.assessment_written import AssessmentWritten
from domain.events.job.job_failed import JobFailed
from domain.events.job.question_asked import QuestionAsked
from domain.events.job.result_submitted import ResultSubmitted
from domain.events.job.spent_increased import SpentIncreased
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.job.reply import Mark, Reply
from domain.value_objects.job.spent import Spent
from domain.value_objects.rule.source import Source
from tests.aggregates.job.conftest import make_job
from tests.app.services.conftest import 固定時計, 帳簿の偽物
from tests.app.services.agent.conftest import (
    LLMの偽物,
    働き手,
    源の偽物,
    根拠置き場の偽物,
    成果置き場の偽物,
    材料読みの偽物,
    見立て置き場の偽物,
    質問置き場の偽物,
)

# AI が承認を呼べないことは型が守っている——approve の by は Human で、Agent を渡す行は pyright が赤にする。

材料 = Quote(evidence=Evidence(quote="依存は42件、うち更新が来ているのは3件", source=源の型(location="file:custom/deps.txt")))
引用 = Quote(evidence=Evidence(quote="更新3件: a, b, c", source=Source(location="deps://prod")))


def _実行中の仕事(**over: object) -> tuple[帳簿の偽物, Job[Any]]:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手), **over)
    帳簿.jobs[仕事.id] = 仕事
    return 帳簿, 仕事


def _進める(
    帳簿: 帳簿の偽物,
    仕事: Job[Any],
    源: 源の偽物,
    llm: LLMの偽物,
    材料読み: 材料読みの偽物 | None = None,
) -> tuple[Refusal | None, 質問置き場の偽物, 成果置き場の偽物, 根拠置き場の偽物, 見立て置き場の偽物]:
    質問 = 質問置き場の偽物()
    成果 = 成果置き場の偽物()
    根拠 = 根拠置き場の偽物()
    見立て = 見立て置き場の偽物()
    断り = consult(
        帳簿, 材料読み or 材料読みの偽物(), 源, llm, 質問, 成果, 根拠, 見立て, 固定時計(), 仕事.id,
        by=働き手,
    )
    return 断り, 質問, 成果, 根拠, 見立て


def test_質問へ抜ける() -> None:
    """週Aの手4——足りない材料を尋ね、質問を積んで答え待ちへ。"""
    帳簿, 仕事 = _実行中の仕事()
    llm = LLMの偽物(Reply(mark=Mark.QUESTION, body="どの環境の依存を見ますか"))
    断り, 質問, _, _, _ = _進める(帳簿, 仕事, 源の偽物(材料), llm)
    assert 断り is None
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, AwaitingAnswer) and 後.state.question_at == "q://1"
    積まれた = 質問.get("q://1")
    assert 積まれた is not None and 積まれた[0].body == "どの環境の依存を見ますか"
    assert 積まれた[0].to == 仕事.owner  # 相手は AI が選ばない——受け持ちの人
    assert [type(e) for e in 帳簿.events] == [SpentIncreased, QuestionAsked]
    assert 後.spent == Spent(calls=1, seconds=5)


def test_成果と根拠を積む() -> None:
    """週Aの手6——成果を積み、源をもう一度読んで引用が取れれば根拠も積んで出す。"""
    帳簿, 仕事 = _実行中の仕事()
    llm = LLMの偽物(Reply(mark=Mark.RESULT, body="2026-W34 の依存は42件、更新3件"))
    断り, _, 成果, 根拠, _ = _進める(帳簿, 仕事, 源の偽物(材料, 引用), llm)
    assert 断り is None
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Submitted)
    assert 後.result_at == "result://1" and 後.evidence_at == "evidence://1"
    積まれた成果 = 成果.get("result://1")
    assert 積まれた成果 is not None and "2026-W34" in 積まれた成果.body
    assert 根拠.get("evidence://1") == 引用.evidence
    assert [type(e) for e in 帳簿.events] == [SpentIncreased, ResultSubmitted]


def test_引用が取れなければ根拠なしで出す() -> None:
    """1回目は読めたのに、根拠の取り直しで源が閉じた——それでも成果は出る。"""
    帳簿, 仕事 = _実行中の仕事()
    llm = LLMの偽物(Reply(mark=Mark.RESULT, body="2026-W34 の依存は42件、更新3件"))
    断り, _, _, 根拠, _ = _進める(帳簿, 仕事, 源の偽物(材料, Unreadable(reason="源が閉じた")), llm)
    assert 断り is None
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Submitted) and 後.evidence_at is None
    assert not 根拠.rows


def test_源が読めなければ落ちる() -> None:
    """落ちた中身＝読めなかった理由。LLM には届かない。"""
    帳簿, 仕事 = _実行中の仕事()
    llm = LLMの偽物(Reply(mark=Mark.RESULT, body="2026-W34 の依存は42件"))
    断り, _, _, _, _ = _進める(帳簿, 仕事, 源の偽物(Unreadable(reason="源に接続できませんでした")), llm)
    assert 断り is None
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Failed) and 後.state.fallen == "源に接続できませんでした"
    assert not llm.received
    assert [type(e) for e in 帳簿.events] == [JobFailed]


def test_上限で止まったら使い切りへ落ちる() -> None:
    """I14——積む前に止まり、使用上限に達したことを残して失敗したへ。"""
    帳簿, 仕事 = _実行中の仕事(spent=Spent(calls=20, seconds=0))  # 上限は calls=20
    llm = LLMの偽物(Reply(mark=Mark.RESULT, body="2026-W34 の依存は42件"))
    断り, _, _, _, _ = _進める(帳簿, 仕事, 源の偽物(材料), llm)
    assert 断り is None
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, Failed) and 後.state.fallen == "使用上限に達した"
    assert 後.spent == Spent(calls=20, seconds=0)  # 積まれていない
    assert [type(e) for e in 帳簿.events] == [JobFailed]


def test_成果と名乗っても語が欠ければ見立てへ() -> None:
    """振り分けの判断は仕様がした——ここは運ぶだけ。状態は実行中のまま。"""
    帳簿, 仕事 = _実行中の仕事()
    llm = LLMの偽物(Reply(mark=Mark.RESULT, body="依存は42件でした"))  # 「2026-W34」が欠けている
    断り, _, 成果, _, 見立て = _進める(帳簿, 仕事, 源の偽物(材料), llm)
    assert 断り is None
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, InProgress)
    assert not 成果.rows
    (行,) = 見立て.rows
    assert 行[0] == 仕事.id and 行[1].finding == "依存は42件でした"
    assert [type(e) for e in 帳簿.events] == [SpentIncreased, AssessmentWritten]


def test_実行中でなければ断りに変わる() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    llm = LLMの偽物(Reply(mark=Mark.QUESTION, body="どの環境ですか"))
    断り, _, _, _, _ = _進める(帳簿, 仕事, 源の偽物(材料), llm)
    assert 断り is not None and "実行中ではありません" in 断り.reason
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events


def test_無い仕事は断りに変わる() -> None:
    帳簿, 仕事 = _実行中の仕事()
    del 帳簿.jobs[仕事.id]
    llm = LLMの偽物(Reply(mark=Mark.QUESTION, body="どの環境ですか"))
    断り, _, _, _, _ = _進める(帳簿, 仕事, 源の偽物(材料), llm)
    assert 断り is not None and not 帳簿.events


def test_別のAIの名乗りは断られる() -> None:
    """I13 — 姿を変えられるのは自分が担当の仕事だけ。名乗り＝担当を検める。"""
    from domain.value_objects.people.agent import Agent

    帳簿, 仕事 = _実行中の仕事()
    llm = LLMの偽物(Reply(mark=Mark.QUESTION, body="呼ばれないはず"))
    断り = consult(
        帳簿, 材料読みの偽物(), 源の偽物(材料), llm, 質問置き場の偽物(), 成果置き場の偽物(),
        根拠置き場の偽物(), 見立て置き場の偽物(), 固定時計(), 仕事.id, by=Agent(name="二号"),
    )
    assert 断り is not None and "担当ではありません" in 断り.reason
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events  # 一生に傷をつけない
