"""人の操作 — 画面と手元から来る、人間だけの行為。

**ここが「人に何ができるか」の一覧**。判断は人間（公理）なので、この置き場に
在るものだけが人の意思で動く。輪（app/manager.py）は誰も呼ばなくても回るが、
ここは人が押したときだけ動く——それが唯一の違いで、そのために置き場を分けている。

ここを通る操作は必ず出来事に残り、誰がいつ押したかが辿れる。
"""

from __future__ import annotations

from datetime import datetime

from domain.board import Board, freeze
from domain.definition import Definition, enact
from domain.event import Event
from domain.job import CannotApprove, approve
from domain.ports import CustomPort, LedgerPort


def record_approval(ledger: LedgerPort, job_id: str, by: str, now: datetime) -> bool:
    """承認を記録する — 人が押した承認を帳簿に書き込む。担当した人でなければ偽"""
    got = ledger.jobs.get(job_id)
    if got is None:
        return False
    job, rev = got
    try:
        approved = approve(job, by=by, at=now)
    except CannotApprove:
        return False
    return ledger.jobs.put(
        approved,
        rev,
        [Event(kind="CheckpointApproved", at=now, job_id=job_id, payload={"by": by})],
    )


def inject(ledger: LedgerPort, custom: CustomPort, by: str, now: datetime) -> list[str]:
    """注入する — 読み込んだ方針と業務ルールを帳簿へ。入れた／変えたものの名を返す"""
    board, definitions = custom.load()
    touched: list[str] = []
    if _inject_board(ledger, board, by, now):
        touched.append(board.board_id)
    for definition in definitions:
        if _inject_definition(ledger, definition, by, now):
            touched.append(definition.name)
    return touched


def _inject_board(ledger: LedgerPort, board: Board, by: str, now: datetime) -> bool:
    """方針を入れて凍結する。既に同じところまで入っていれば何もしない"""
    known = ledger.boards.get(board.board_id)
    latest = board.constitutions[-1].number
    if known is not None and known.frozen == latest:
        return False
    events: list[Event] = []
    if known is None or len(known.constitutions) < len(board.constitutions):
        events.append(
            Event(kind="ConstitutionAppended", at=now, payload={"board": board.board_id})
        )
    events.append(
        Event(kind="ConstitutionFrozen", at=now, payload={"board": board.board_id, "by": by})
    )
    ledger.boards.put(freeze(board, latest), events)
    return True


def _inject_definition(
    ledger: LedgerPort, definition: Definition, by: str, now: datetime
) -> bool:
    """業務ルールを積んで有効化する。版は積むだけ——増えた版だけを積む"""
    known = ledger.definitions.get(definition.name)
    latest = definition.versions[-1].number
    if known is not None and known.enacted == latest and len(known.versions) == len(
        definition.versions
    ):
        return False
    events: list[Event] = []
    if known is None or len(known.versions) < len(definition.versions):
        events.append(
            Event(kind="VersionAppended", at=now, payload={"name": definition.name})
        )
    events.append(
        Event(
            kind="DefinitionEnacted",
            at=now,
            payload={"name": definition.name, "version": latest, "by": by},
        )
    )
    ledger.definitions.put(enact(definition, latest), events)
    return True
