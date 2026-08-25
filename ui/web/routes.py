from __future__ import annotations
from app.dto.row_filter import RowFilter
from collections.abc import Callable
from typing import Any
from ui.web.activity import _履歴
from ui.web.automations import _予定
from ui.web.billing import _会計, _会計面, _提出ファイル, _請求書
from ui.web.day import _道順
from ui.web.fees import _点数表
from ui.web.detail import _詳細
from ui.web.frame import _頁
from ui.web.guide import _リンク, _写し, _案内, 往復を読む
from ui.web.hands import 手
from ui.web.hands import 手を開く

import json as _json
import time as _time
from html import escape as _esc
from fastapi.responses import StreamingResponse
from ui.web.now import _いま
from ui.web.activity import _誰 as _who
from ui.words import 出来事 as _event_word
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
    from fastapi import Cookie, FastAPI, Form, Header
    from fastapi.responses import HTMLResponse, RedirectResponse

    app = FastAPI(title="Troupe", docs_url=None, redoc_url=None)

    def _席名(cookie: str | None) -> str:
        # 席は名乗り(cookie)——空なら起動の席。力の源は登記簿の門なので、ここでは検めない
        return (cookie or "").strip() or viewer

    def 見せる(
        見出し: str,
        描く: Callable[[手], str],
        断り: str | None = None,
        席: str | None = None,
    ) -> HTMLResponse:
        座 = _席名(席)
        手たち = 開く(座)
        try:
            return HTMLResponse(
                _頁(見出し, 描く(手たち), 座, 断り, notice,
                    手たち.staff(), 手たち.billing_flags())
            )
        finally:
            手たち.close()

    @app.post("/seat")
    def _席を替える(
        seat: str = Form(...), referer: str | None = Header(default=None)
    ) -> Any:
        """座り替え。**席は名乗りであって認証ではない**——力の源は登記簿の門。"""
        戻り = referer if referer and referer.startswith(("http", "/")) else "/day"
        応え = RedirectResponse(戻り, status_code=303)
        応え.set_cookie("troupe_seat", seat.strip()[:64], max_age=60 * 60 * 12)
        return 応え

    @app.get("/", response_class=HTMLResponse)
    def _根() -> Any:
        return RedirectResponse("/now", status_code=303)

    @app.get("/now", response_class=HTMLResponse)
    def _いまの頁(troupe_seat: str | None = Cookie(default=None)) -> HTMLResponse:
        return 見せる("now", lambda h: _いま(h.now(), h.history_fetch(0)[:12]),
                    席=troupe_seat)

    @app.get("/events")
    def _生の帯(troupe_seat: str | None = Cookie(default=None)) -> Any:
        """生の帯(SSE)——器が同じ読みを繰り返すだけの、開きっぱなしの導出。

        予告は流さない——起きた事実だけ。語は app が写した英語のまま運ぶ。
        10分で閉じる——EventSource が黙って繋ぎ直す。
        """
        座 = _席名(troupe_seat)

        def 流れ() -> Any:
            前: set[tuple[str, str, str]] = set()
            初回 = True
            for _ in range(150):
                手たち = 開く(座)
                try:
                    v = 手たち.now()
                    行 = 手たち.history_fetch(0)[:12]
                    旗 = 手たち.billing_flags()
                finally:
                    手たち.close()
                鍵 = {(r.at, r.job_id, r.what) for r in 行}
                新 = [] if 初回 else [r for r in 行 if (r.at, r.job_id, r.what) not in 前]
                前, 初回 = 鍵, False
                # innerHTML に入る欄はここで無害化する(語も見出しもサーバー発)
                payload = _json.dumps({
                    "queued": v.queued,
                    "working": [[_esc(i), _esc(h)] for i, h in v.working],
                    "checking": v.checking, "waiting": v.waiting,
                    "beat_at": v.beat_at, "flags": 旗,
                    "events": [
                        {"at": _esc(r.at), "by_kind": _esc(r.by_kind),
                         "who_html": _who(r.by, r.by_kind),
                         "what": _esc(_event_word(r.what)), "job_id": _esc(r.job_id),
                         "head": _esc(r.head)}
                        for r in 新
                    ],
                })
                yield f"data: {payload}\n\n"
                _time.sleep(4)

        return StreamingResponse(流れ(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

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
        return RedirectResponse("/patients", status_code=303)

    @app.get("/alive")
    def _生きているか() -> dict[str, str]:
        """器が生きているかだけ。**帳簿は開かない**——脈ではない。

        （`/healthz` は載せる先の入口に取られるので使わない。）
        """
        return {"status": "ok"}

    @app.get("/inbox", response_class=HTMLResponse)
    def _今日の頁(refused: str | None = None, acted: str | None = None,
               troupe_seat: str | None = Cookie(default=None)) -> HTMLResponse:
        def 描く(h: 手) -> str:
            rows = h.fetch()
            return _帯(rows, len(h.upcoming())) + _今日(rows, acted)

        return 見せる("inbox", 描く, refused, troupe_seat)

    @app.get("/detail", response_class=HTMLResponse)
    def _詳細の頁(id: str, refused: str | None = None, troupe_seat: str | None = Cookie(default=None)) -> HTMLResponse:
        return 見せる("inbox", lambda h: _詳細(h.detail(id)), refused, troupe_seat)

    @app.get("/automations", response_class=HTMLResponse)
    def _予定の頁(
        refused: str | None = None, done: str | None = None,
        troupe_seat: str | None = Cookie(default=None),
    ) -> HTMLResponse:
        副題 = ("<p class='page-sub'>Troupe's own work schedule — AI routines and their runs."
                " Patient visits live in <a href='/day'>My Day</a>.</p>")
        return 見せる(
            "automations",
            lambda h: 副題 + _予定(h.schedule_fetch(), h.upcoming(), done),
            refused, troupe_seat,
        )

    @app.post("/automations/act")
    def _決まりを押す(
        what: str = Form(...),
        name: str = Form(""),
        version: str = Form("0"),
        body: str = Form(""),
        instruction: str = Form(""),
        source: str = Form(""),
        required_terms: str = Form(""),
        description: str = Form(""),
        cycle: str = Form(""),
        days: str = Form(""),
        budget_calls: str = Form(""),
        budget_seconds: str = Form(""),
        owner: str = Form(""),
        max_retries: str = Form(""),
        troupe_seat: str | None = Cookie(default=None),
    ) -> Any:
        # 空欄は渡さない——版の欄は題材のデータが初期値、人が上書き(筋道 §1)
        欄 = {k: v for k, v in {
            "instruction": instruction, "source": source,
            "required_terms": required_terms, "description": description,
            "cycle": cycle, "days": days, "budget_calls": budget_calls,
            "budget_seconds": budget_seconds, "owner": owner,
            "max_retries": max_retries,
        }.items() if v.strip()}
        手たち = 開く(_席名(troupe_seat))
        try:
            if what == "request":
                断り = 手たち.request(body, 欄)
                伝え = "Requested — the job appears in the ledger now"
            else:
                try:
                    版 = int(version or "0")
                except ValueError:
                    版 = 0
                断り = 手たち.schedule_act(what, name, 版, 欄)
                伝え = {"add_version": "Version added — activate it to start creating jobs",
                        "activate": "Activated — jobs will derive from this version",
                        "deactivate": "Stopped — no new jobs from this rule"}.get(what, "Done")
        finally:
            手たち.close()
        if 断り is None:
            戻り = f"/automations?done={quote(伝え)}"
        else:
            戻り = f"/automations?refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/activity", response_class=HTMLResponse)
    def _履歴の頁(page: int = 0, troupe_seat: str | None = Cookie(default=None)) -> HTMLResponse:
        頁 = max(page, 0)
        return 見せる(
            "activity",
            lambda h: _履歴(h.history_fetch(頁), 頁, total=h.history_count()),
            席=troupe_seat,
        )

    @app.get("/day", response_class=HTMLResponse)
    def _道順の頁(
        day: str | None = None, who: str | None = None, signed: str | None = None,
        troupe_seat: str | None = Cookie(default=None),
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

        return 見せる("day", 描く, 席=troupe_seat)

    @app.get("/agreements")
    def _旧agreements() -> Any:
        return RedirectResponse("/patients", status_code=303)

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
        back: str = Form("/patients"),
        troupe_seat: str | None = Cookie(default=None),
    ) -> Any:
        手たち = 開く(_席名(troupe_seat))
        try:
            断り = 手たち.pattern_act(
                what,
                {"id": id, "patient": patient, "weekday": weekday,
                 "every_weeks": every_weeks,
                 "clinician": clinician, "purpose": purpose, "start": start},
            )
        finally:
            手たち.close()
        先 = back if back.startswith("/patient") else "/patients?view=agreements"
        つなぎ = "&" if "?" in 先 else "?"
        if 断り is None:
            戻り = (f"{先}{つなぎ}added=" + quote("Agreement added — visits will appear shortly")
                    if what == "add_pattern" else 先)
        else:
            戻り = f"{先}{つなぎ}refused={quote(断り)}"
        return RedirectResponse(戻り, status_code=303)

    @app.get("/visit", response_class=HTMLResponse)
    def _訪問の頁(id: str, refused: str | None = None, troupe_seat: str | None = Cookie(default=None)) -> HTMLResponse:
        return 見せる("day", lambda h: _訪問(h.visit(id), refused, h.fees(), _席名(troupe_seat)), refused, troupe_seat)

    @app.post("/visit/act")
    def _訪問を押す(
        what: str = Form(...),
        id: str = Form(...),
        signer: str = Form(""),
        s: str = Form(""),
        o: str = Form(""),
        a: str = Form(""),
        p: str = Form(""),
        reason: str = Form(""),
        code: str = Form(""),
        qty: str = Form("1"),
        troupe_seat: str | None = Cookie(default=None),
    ) -> Any:
        手たち = 開く(_席名(troupe_seat))
        try:
            断り = 手たち.visit_act(
                what,
                {"id": id, "signer": signer, "s": s, "o": o, "a": a, "p": p,
                 "reason": reason, "code": code, "qty": qty},
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

    @app.get("/fees")
    def _旧fees() -> Any:
        return RedirectResponse("/billing?view=fees", status_code=303)

    @app.get("/billing", response_class=HTMLResponse)
    def _会計の頁(
        month: str | None = None,
        view: str | None = None,
        invoice: str | None = None,
        refused: str | None = None,
        done: str | None = None,
        troupe_seat: str | None = Cookie(default=None),
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
            if view == "fees":
                fees = h.fees()
                return (
                    "<div class='page-head'><h1 class='page-title'>Billing</h1>"
                    f"<span class='count-pill'><strong>{len(fees)}</strong> items</span>"
                    "<span class='page-head__aside'>Nagisa Schedule — every value"
                    " invented</span></div>"
                    + _会計面(対象, "fees")
                    + _点数表(fees, 頭あり=False)
                )
            if view == "file":
                return _提出ファイル(views, 対象)
            if invoice:
                v = next((x for x in views if x.patient == invoice), None)
                if v is not None:
                    return _請求書(v, 対象)
            座 = _席名(troupe_seat)
            座長 = any(s.name == 座 and s.role == "director" for s in h.staff())
            return _会計(views, 対象, today_month, refused, done, is_director=座長)

        return 見せる("billing", 描く, 席=troupe_seat)

    @app.post("/billing/act")
    def _会計を押す(
        what: str = Form(...),
        id: str = Form(""),
        action: str = Form(""),
        reason: str = Form(""),
        patient: str = Form(""),
        month: str = Form(""),
        troupe_seat: str | None = Cookie(default=None),
    ) -> Any:
        手たち = 開く(_席名(troupe_seat))
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
    def _案内の頁(troupe_seat: str | None = Cookie(default=None)) -> HTMLResponse:
        return 見せる("guide", lambda h: _案内("", "", ()), 席=troupe_seat)

    @app.post("/guide", response_class=HTMLResponse)
    def _案内に問う(
        question: str = Form(""), history: str = Form("[]"),
        troupe_seat: str | None = Cookie(default=None),
    ) -> HTMLResponse:
        往復 = 往復を読む(history)

        def 描く(h: 手) -> str:
            answer = h.guide(question, _写し(h), 往復) if question.strip() else ""
            return _案内(question.strip(), answer, 往復)

        return 見せる("guide", 描く, 席=troupe_seat)

    # 案内の律速 — 公開の窓で Gemini を溶かさない(器1つあたり: 最短2秒間隔・日400問)
    案内の息 = {"last": 0.0, "day": "", "n": 0}

    @app.post("/guide/turn")
    def _案内の一手(
        question: str = Form(""), history: str = Form(""), path: str = Form(""),
        troupe_seat: str | None = Cookie(default=None),
    ) -> Any:
        from time import monotonic

        from fastapi.responses import JSONResponse

        往復 = 往復を読む(history)
        手たち = 開く(_席名(troupe_seat))
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

    @app.get("/how")
    def _旧how() -> Any:
        # 説明は「いま」に溶けた——貼られたリンクを死なせない
        return RedirectResponse("/now", status_code=303)

    @app.get("/patients", response_class=HTMLResponse)
    def _患者たちの頁(
        refused: str | None = None, added: str | None = None,
        view: str | None = None,
        troupe_seat: str | None = Cookie(default=None),
    ) -> HTMLResponse:
        面 = "agreements" if view == "agreements" else "patients"
        return 見せる(
            "patients",
            lambda h: _患者たち(h.patients(), h.today(), h.patterns(), added, 面),
            refused, troupe_seat,
        )

    @app.get("/patient", response_class=HTMLResponse)
    def _患者の頁(
        code: str, refused: str | None = None, added: str | None = None,
        troupe_seat: str | None = Cookie(default=None),
    ) -> HTMLResponse:
        return 見せる(
            "patients",
            lambda h: _患者(
                h.patient(code),
                tuple(r for r in h.patterns() if r.patient == code),
                added,
            ),
            refused, troupe_seat,
        )

    @app.get("/search", response_class=HTMLResponse)
    def _検索の頁(
        keyword: str = "", state: str = "", rule: str = "", assignee: str = "",
        troupe_seat: str | None = Cookie(default=None),
    ) -> HTMLResponse:
        条件 = RowFilter(
            keyword=keyword or None,
            state_label=state or None,
            rule=rule or None,
            assignee=assignee or None,
        )
        return 見せる("search", lambda h: _検索(h.search(条件), 条件), 席=troupe_seat)

    @app.post("/act")
    def _押す(
        what: str = Form(...),
        id: str = Form(...),
        back: str = Form("/today"),
        text: str = Form(""),
        troupe_seat: str | None = Cookie(default=None),
    ) -> Any:
        """押されたら文字で app を呼ぶだけ。**断られたら理由を出す。**

        押して何も起きないのが一番わるい（人に見えるもの §3）。
        操作の失敗はエラーではない——仕事の状態は変わらないので、
        一生に傷をつけず、画面にだけ理由を出す。
        """
        手たち = 開く(_席名(troupe_seat))
        try:
            断り = 手たち.act(what, id, text)
        finally:
            手たち.close()
        つなぎ = "&" if "?" in back else "?"
        # 成功にも一言返す——押して何も起きないのが一番わるい(受信箱が緑の一行にする)
        戻り = (f"{back}{つなぎ}acted={what}" if 断り is None
              else f"{back}{つなぎ}refused={断り}")
        return RedirectResponse(戻り, status_code=303)

    return app
