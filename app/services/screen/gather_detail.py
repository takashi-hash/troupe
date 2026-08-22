"""詳細を集める — この仕事は誰が・いつ・何を・どうした？

設計: 設計/人に見えるもの.md §1「詳細」・§2「詳細」の欄・仕事が回る筋道 §4。

**判定するのは仕様。集めて渡すだけ。帳簿に書かない。**
成果と根拠は**仕事の在りかが指す1つ**（今日の材料から）。
出来事の全部と、質問・回答・見立ての本文はそのまま——縮めない。
状態の名と出来事の名は**用語集の語**に写してから渡す（画面で言い換えない）。
"""

from __future__ import annotations

from pydantic import ValidationError

from app.dto.detail_view import DetailView
from app.dto.event_row import EventRow
from app.ports.clock_port import ClockPort
from app.ports.detail_reader import DetailReader
from app.ports.today_reader import TodayReader
from domain.aggregates.job.life import STATE_WORDS
from domain.events.event import EVENT_WORDS
from domain.services.allowed import allowed
from domain.value_objects.job.job_id import JobId
from domain.value_objects.people.actor import ACTOR_WORDS
from domain.value_objects.people.human import Human

_状態の語 = {ident: word for word, ident in STATE_WORDS.items()}
_出来事の語 = {ident: word for word, ident in EVENT_WORDS.items()}
_起こす者の語 = {ident: word for word, ident in ACTOR_WORDS.items()}


def gather_detail(
    today: TodayReader,
    details: DetailReader,
    clock: ClockPort,
    viewer: str,
    id: str,
) -> DetailView | None:
    """1件の詳細。無ければ None。読むだけ——帳簿に書かない。"""
    try:
        鍵, 人 = JobId(text=id), Human(name=viewer)
    except ValidationError:
        return None
    material = today.read(鍵)
    if material is None:
        return None
    actions = allowed(material, 人, clock.now())
    d = details.read(鍵)
    events = tuple(
        EventRow(
            at=at,
            by=by_name if by_name else _起こす者の語.get(by_kind, by_kind),
            what=_出来事の語.get(name, name),
        )
        for at, by_kind, by_name, name in d.events
    )
    return DetailView(
        id=material.id.text,
        instruction=material.instruction.text,
        state_name=_状態の語[material.state_name],
        due=material.due.at.isoformat()[:16].replace("T", " "),
        assignee_name=material.assignee_name,
        result_body=material.result_body,
        evidence_quote=material.evidence_quote,
        recheck_at=(
            material.recheck_at.isoformat()[:16].replace("T", " ")
            if material.recheck_at is not None
            else None
        ),
        questions=d.questions,
        assessments=tuple((a.finding, a.reason) for a in material.assessments),
        actions=actions,
        events=events,
    )
