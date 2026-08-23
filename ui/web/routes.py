from __future__ import annotations
from app.dto.row_filter import RowFilter
from collections.abc import Callable
from typing import Any
from ui.web.activity import _履歴
from ui.web.agreements import _取り決めたち
from ui.web.automations import _予定
from ui.web.billing import _会計, _提出ファイル, _請求書
from ui.web.day import _道順
from ui.web.fees import _点数表
from ui.web.detail import _詳細
from ui.web.frame import _頁
from ui.web.guide import _リンク, _写し, _案内, 往復を読む
from ui.web.hands import 手
from ui.web.hands import 手を開く
from ui.web.how import _説明
from ui.web.inbox import _今日
from ui.web.inbox import _帯
from ui.web.patients import _患者
from ui.web.patients import _患者たち
from ui.web.search import _検索
from ui.web.visit import _訪問
from urllib.parse import quote

def make_app(
    開く: 手を開く,
    viewer: str,
    maps_key: str | None = None,
    notice: str | None = None,
) -> Any:
    """web の器を組む。**手は1回ごとに開いて閉じる。**

    返すのは ASGI のアプリ——立てるのは main.py（**注ぐのはそこだけ**）。
    """
    from fastapi import FastAPI, Form
    from fastapi.responses import HTMLResponse, RedirectResponse

    app = FastAPI(title="Troupe", docs_url=None, redoc_url=None)

    def 見せる(見出し: str, 描く: Callable[[手], str], 断り: str | None = None) -> HTMLResponse:
        手たち = 開く()
        try:
            return HTMLResponse(_頁(見出し, 描く(手たち), viewer, 断り, notice))
        finally:
            手たち.close()

    @app.get("/", response_class=HTMLResponse)
    def _根() -> Any:
        return RedirectResponse("/day")

    # 古い道は新しい道へ——貼られたリンクを死なせない
    @app.get("/today")
    def _旧today() -> Any:
        return RedirectResponse("/inbox", status_code=303)

    @app.get("/route")
    def _旧route(day: str | None = None) -> Any:
        return RedirectResponse(f"/day?day={day}" if day else "/day", status_code=303)

    @app.get("/schedule")
    def _旧schedule() -> Any:
        return RedirectResponse("/automations", status_code=303)

    @app.get("/history")
    def _旧history() -> Any:
        return RedirectResponse("/activity", status_code=303)

    @app.get("/patterns")
    def _旧patterns() -> Any:
        return RedirectResponse("/agreements", status_code=303)

    @app.get("/alive")
    def _生きているか() -> dict[str, str]:
        """器が生きているかだけ。**帳簿は開かない**——脈ではない。

        （`/healthz` は載せる先の入口に取られるので使わない。）
        """
        return {"status": "ok"}

    @app.get("/inbox", response_class=HTMLResponse)
    def _今日の頁(refused: str | None = None) -> HTMLResponse:
        def 描く(h: 手) -> str:
            rows = h.fetch()
            return _帯(rows, len(h.upcoming())) + _今日(rows)

        return 見せる("inbox", 描く, refused)

    @app.get("/detail", response_class=HTMLResponse)
    def _詳細の頁(id: str, refused: str | None = None) -> HTMLResponse:
        return 見せる("inbox", lambda h: _詳細(h.detail(id)), refused)

    @app.get("/automations", response_class=HTMLResponse)
    def _予定の頁() -> HTMLResponse:
        副題 = ("<p class='page-sub'>Troupe's own work schedule — AI routines and their runs."
                " Patient visits live in <a href='/day'>My Day</a>.</p>")
        return 見せる("automations", lambda h: 副題 + _予定(h.schedule_fetch(), h.upcoming()))

    @app.get("/activity", response_class=HTMLResponse)
    def _履歴の頁(page: int = 0) -> HTMLResponse:
        頁 = max(page, 0)
        return 見せる(
            "activity", lambda h: _履歴(h.history_fetch(頁), 頁, total=h.history_count())
        )

    @app.get("/day", response_class=HTMLResponse)
    def _道順の頁(
        day: str | None = None, who: str | None = None, signed: str | None = None
    ) -> HTMLResponse:
        from datetime import date

        def 描く(h: 手) -> str:
            対象 = day or h.today()
            try:
                date.fromisoformat(対象)
            except ValueError:
                対象 = h.today()  # 壊れた日付は今日に倒す——500 は出さない
            拠点, 道順ごと = h.route(対象)
            return _道順(対象, 道順ごと, 拠点, maps_key, who, signed)

        return 見せる("day", 描く)

    @app.get("/agreements", response_class=HTMLResponse)
    def _取り決めの頁(refused: str | None = None, added: str | None = None) -> HTMLResponse:
        return 見せる("agreements", lambda h: _取り決めたち(h.patterns(), added), refused)

    @app.post("/patterns/act")
    def _取り決めを押す(
        what: str = Form(...),
        id: str = Form(""),
        patient: str = Form(""),
        weekday: str = Form(""),
        every_weeks: str = Form("1"),
        clinician: str = Form(""),
        purpose: str = Form(""),
        start: str = Form(""),
    ) -> Any:
        手たち = 開く()
        try:
            断り = 手たち.pattern_act(
                what,
                {"id": id, "patient": patient, "weekday": weekday,
                 "every_weeks": every_weeks,
                 "clinician": clinician, "purpose": purpose, "start": start},
            )
        finally:
            手たち.close()
        if 断り is None:
            戻り = ("/agreements?added=" + quote("Agreement added — visits will appear shortly")
                    if what == "add_pattern" else "/agreements")
        else:
            戻り = f"/agreements?refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/visit", response_class=HTMLResponse)
    def _訪問の頁(id: str, refused: str | None = None) -> HTMLResponse:
        return 見せる("day", lambda h: _訪問(h.visit(id), refused, h.fees()), refused)

    @app.post("/visit/act")
    def _訪問を押す(
        what: str = Form(...),
        id: str = Form(...),
        signer: str = Form(""),
        s: str = Form(""),
        o: str = Form(""),
        a: str = Form(""),
        p: str = Form(""),
        draft_id: str = Form(""),
        reason: str = Form(""),
        code: str = Form(""),
        qty: str = Form("1"),
    ) -> Any:
        手たち = 開く()
        try:
            断り = 手たち.visit_act(
                what,
                {"id": id, "signer": signer, "s": s, "o": o, "a": a, "p": p,
                 "draft_id": draft_id, "reason": reason, "code": code, "qty": qty},
            )
        finally:
            手たち.close()
        if 断り is None:
            if what == "sign_note":
                戻り = f"/day?signed={quote('Visit ' + id)}"
            elif what in ("add_service", "remove_service"):
                戻り = f"/visit?id={quote(id)}"  # 記帳は訪問の頁に戻る
            else:
                戻り = "/day"
        else:
            戻り = f"/visit?id={quote(id)}&refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/fees", response_class=HTMLResponse)
    def _点数表の頁() -> HTMLResponse:
        return 見せる("fees", lambda h: _点数表(h.fees()))

    @app.get("/billing", response_class=HTMLResponse)
    def _会計の頁(
        month: str | None = None,
        view: str | None = None,
        invoice: str | None = None,
        refused: str | None = None,
        done: str | None = None,
    ) -> HTMLResponse:
        def 描く(h: 手) -> str:
            from datetime import date as _date

            today_month = h.today()[:7]
            対象 = today_month
            if month:
                try:
                    _date.fromisoformat(month + "-01")  # 壊れた月は今月に倒す——500 は出さない
                    対象 = month
                except ValueError:
                    pass
            views = h.billing(対象)
            if view == "file":
                return _提出ファイル(views, 対象)
            if invoice:
                v = next((x for x in views if x.patient == invoice), None)
                if v is not None:
                    return _請求書(v, 対象)
            return _会計(views, 対象, today_month, refused, done)

        return 見せる("billing", 描く)

    @app.post("/billing/act")
    def _会計を押す(
        what: str = Form(...),
        id: str = Form(""),
        action: str = Form(""),
        reason: str = Form(""),
        patient: str = Form(""),
        month: str = Form(""),
    ) -> Any:
        手たち = 開く()
        try:
            断り = 手たち.billing_act(
                what,
                {"id": id, "action": action, "reason": reason,
                 "patient": patient, "month": month},
            )
        finally:
            手たち.close()
        if 断り is None:
            伝え = ("Claim confirmed — it is now immutable"
                    if what == "confirm_claim" else "Ruled — the totals moved with it")
            戻り = f"/billing?month={quote(month)}&done={quote(伝え)}"
        else:
            戻り = f"/billing?month={quote(month)}&refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/guide", response_class=HTMLResponse)
    def _案内の頁() -> HTMLResponse:
        return 見せる("guide", lambda h: _案内("", "", ()))

    @app.post("/guide", response_class=HTMLResponse)
    def _案内に問う(question: str = Form(""), history: str = Form("[]")) -> HTMLResponse:
        往復 = 往復を読む(history)

        def 描く(h: 手) -> str:
            answer = h.guide(question, _写し(h), 往復) if question.strip() else ""
            return _案内(question.strip(), answer, 往復)

        return 見せる("guide", 描く)

    # 案内の律速 — 公開の窓で Gemini を溶かさない(器1つあたり: 最短2秒間隔・日400問)
    案内の息 = {"last": 0.0, "day": "", "n": 0}

    @app.post("/guide/turn")
    def _案内の一手(
        question: str = Form(""), history: str = Form(""), path: str = Form("")
    ) -> Any:
        from time import monotonic

        from fastapi.responses import JSONResponse

        往復 = 往復を読む(history)
        手たち = 開く()
        try:
            today = 手たち.today()
            if 案内の息["day"] != today:
                案内の息["day"], 案内の息["n"] = today, 0
            if monotonic() - float(案内の息["last"]) < 2.0 or int(案内の息["n"]) >= 400:
                answer = "The guide is catching its breath — ask again in a moment."
            elif not question.strip():
                answer = ""
            else:
                案内の息["last"], 案内の息["n"] = monotonic(), int(案内の息["n"]) + 1
                answer = 手たち.guide(question, _写し(手たち, path), 往復)
        finally:
            手たち.close()
        return JSONResponse({"answer_html": _リンク(answer), "answer_text": answer})

    @app.get("/how", response_class=HTMLResponse)
    def _説明の頁() -> HTMLResponse:
        return 見せる("how", lambda h: _説明())

    @app.get("/patients", response_class=HTMLResponse)
    def _患者たちの頁() -> HTMLResponse:
        return 見せる("patients", lambda h: _患者たち(h.patients(), h.today()))

    @app.get("/patient", response_class=HTMLResponse)
    def _患者の頁(code: str) -> HTMLResponse:
        return 見せる("patients", lambda h: _患者(h.patient(code)))

    @app.get("/search", response_class=HTMLResponse)
    def _検索の頁(
        keyword: str = "", state: str = "", rule: str = "", assignee: str = ""
    ) -> HTMLResponse:
        条件 = RowFilter(
            keyword=keyword or None,
            state_label=state or None,
            rule=rule or None,
            assignee=assignee or None,
        )
        return 見せる("search", lambda h: _検索(h.search(条件), 条件))

    @app.post("/act")
    def _押す(
        what: str = Form(...),
        id: str = Form(...),
        back: str = Form("/today"),
        text: str = Form(""),
    ) -> Any:
        """押されたら文字で app を呼ぶだけ。**断られたら理由を出す。**

        押して何も起きないのが一番わるい（人に見えるもの §3）。
        操作の失敗はエラーではない——仕事の状態は変わらないので、
        一生に傷をつけず、画面にだけ理由を出す。
        """
        手たち = 開く()
        try:
            断り = 手たち.act(what, id, text)
        finally:
            手たち.close()
        つなぎ = "&" if "?" in back else "?"
        戻り = back if 断り is None else f"{back}{つなぎ}refused={断り}"
        return RedirectResponse(戻り, status_code=303)

    return app
