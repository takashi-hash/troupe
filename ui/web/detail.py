from __future__ import annotations
from app.dto.detail_view import DetailView
from html import escape
from ui.web.frame import _押せること
from ui.web.frame import _欄
from ui.web.frame import _状態
from ui.words import 出来事
from ui.words import 語
from ui.words import 起こす者

def _詳細(view: DetailView | None) -> str:
    if view is None:
        return "<p class='empty'>No such job.</p>"
    問答 = "\n".join(f"Q: {q}\nA: {a or '(not yet)'}" for q, a in view.questions)
    見立て = "\n".join(f"{本文}（{理由}）" for 本文, 理由 in view.assessments)
    出来事の列 = "".join(
        f"<tr><td>{escape(e.at)}</td><td>{escape(起こす者(e.by))}</td><td>{escape(出来事(e.what))}</td></tr>"
        for e in view.events
    )
    return (
        f"<div class='row'><div class='head'>"
        f"<span class='title'>{escape(view.instruction)}</span>{_状態(view.state_name)}"
        f"<span class='id'>{escape(view.id)}</span></div>"
        + _欄(
            [
                (語("期日"), view.due),
                (語("担当"), view.assignee_name),
                (語("成果"), view.result_body),
                (語("根拠"), view.evidence_quote),
                (語("確かめ期日"), view.recheck_at),
                (f'{語("質問")} / {語("回答")}', 問答),
                (語("見立て"), 見立て),
            ]
        )
        + _押せること(view.actions, view.id, f"/detail?id={view.id}")
        + "</div>"
        + "<div class='wrap'><table><tr><th>When</th><th>Who</th><th>What happened</th></tr>"
        + 出来事の列
        + "</table></div>"
    )


