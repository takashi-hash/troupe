"""予定（Automations）— 業務ルールと、いま流れている仕事（人に見えるもの §1）

routes.py の page-sub がこの上に載る——ここでは言い直さない。
やること（instruction）は長文——読み幅で折る。版の数字は右に揃えて等幅。
右の脇（rail）に人の手——版を積む・頼む。表の行には 有効にする・止める。
どのフォームも /automations/act に post する（受け手は routes.py）。
"""

from __future__ import annotations

from html import escape

from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from ui.web.frame import _状態
from ui.words import 語

#: 表の小さな整えはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
_様式 = """<style>
/* 予定の表 — 4pxの目で詰める。やることは読み幅で折り、版の数字は右に揃える。
   日付は .cell-when(等幅)が持ち、折らない */
.automations-rules td, .automations-jobs td { padding: 8px 12px; }
.automations-instr { max-width: 64ch; }
.automations-ver { text-align: right; }
.automations-name { white-space: nowrap; }
.automations-acts { white-space: nowrap; }
.automations-acts form.act + form.act { margin-left: 8px; }
/* 右の脇 — 人の手（版を積む・頼む）。狭い幅では本文の下に落ちる。
   何も display:none にしない——消えるのではなく積み替わるだけ */
.page-cols { display: grid; grid-template-columns: minmax(0, 1fr) 340px;
  gap: 28px; align-items: start; }
.page-rail { position: sticky; top: 20px; }
.page-rail .form-card { margin-top: 0; max-width: none; }
.page-rail .form-card + .form-card { margin-top: 24px; }
@media (max-width: 1100px) {
  .page-cols { display: block; }
  .page-rail { position: static; margin-top: 24px; }
}
</style>"""

_操作先 = "<form class='act' method='post' action='/automations/act'>"


def _押せる(r: ScheduleRow) -> str:
    """行の右端 — 有効にする／止める。押せないときは静かな文字。"""
    最新が有効 = r.active_version is not None and r.active_version == r.version
    有効にする = (
        "<span class='sub'>active</span>"
        if 最新が有効
        else (
            _操作先
            + "<input type='hidden' name='what' value='activate'>"
            + f"<input type='hidden' name='name' value='{escape(r.rule)}'>"
            + f"<input type='hidden' name='version' value='{r.version}'>"
            + "<button class='btn btn--small'>Activate</button></form>"
        )
    )
    止める = (
        (
            _操作先
            + "<input type='hidden' name='what' value='deactivate'>"
            + f"<input type='hidden' name='name' value='{escape(r.rule)}'>"
            + "<button class='btn btn--small btn--destructive'"
            " onclick=\"return confirm('Stop this rule?"
            " No new jobs will be created.')\">Stop</button></form>"
        )
        if r.active_version is not None
        else ""
    )
    return 有効にする + 止める


def _版を積む札(rules: tuple[ScheduleRow, ...]) -> str:
    """版を積む — 空欄は題材のデータが埋める。人は上書きしたい欄だけ書く。"""
    候補 = "".join(
        f"<option value='{escape(r.rule)}'>{escape(r.rule)}</option>" for r in rules
    )
    空欄 = "default from the topic data"
    return (
        "<aside class='form-card'>"
        "<h3 class='form-card__title'>Add a version</h3>"
        "<p class='sub'>Topic data fills every blank field — you override"
        " only what you type.</p>"
        "<form method='post' action='/automations/act'>"
        "<input type='hidden' name='what' value='add_version'>"
        "<div class='form-grid'>"
        "<div class='field'><label for='au-name'>Rule</label>"
        "<input type='text' id='au-name' name='name' list='auto-rules' required"
        " placeholder='existing rule, or a new topic name'>"
        f"<datalist id='auto-rules'>{候補}</datalist></div>"
        "<div class='field'><label for='au-instruction'>Instruction</label>"
        f"<textarea id='au-instruction' name='instruction' rows='3'"
        f" placeholder='{空欄}'></textarea></div>"
        "<div class='field'><label for='au-source'>Source</label>"
        f"<input type='text' id='au-source' name='source' placeholder='{空欄}'></div>"
        "<div class='field'><label for='au-terms'>Required terms</label>"
        f"<input type='text' id='au-terms' name='required_terms' placeholder='{空欄}'>"
        "<span class='sub'>terms separated by 、 or ,</span></div>"
        "<div class='field'><label for='au-description'>Description</label>"
        f"<textarea id='au-description' name='description' rows='2'"
        f" placeholder='{空欄}'></textarea></div>"
        "<div class='field'><label for='au-cycle'>Cycle</label>"
        "<select id='au-cycle' name='cycle'><option value=''>default</option>"
        "<option value='weekly'>weekly</option>"
        "<option value='monthly'>monthly</option></select></div>"
        "<div class='field'><label for='au-days'>Days</label>"
        f"<input type='number' id='au-days' name='days' placeholder='{空欄}'></div>"
        "<div class='field'><label for='au-budget-calls'>Budget calls</label>"
        f"<input type='number' id='au-budget-calls' name='budget_calls'"
        f" placeholder='{空欄}'></div>"
        "<div class='field'><label for='au-budget-seconds'>Budget seconds</label>"
        f"<input type='number' id='au-budget-seconds' name='budget_seconds'"
        f" placeholder='{空欄}'></div>"
        "<div class='field'><label for='au-owner'>Owner</label>"
        f"<input type='text' id='au-owner' name='owner' placeholder='{空欄}'></div>"
        "<div class='field'><label for='au-max-retries'>Max retries</label>"
        f"<input type='number' id='au-max-retries' name='max_retries'"
        f" placeholder='{空欄}'></div>"
        "</div>"
        "<div class='form-actions'><button class='btn'>Add version</button></div>"
        "</form></aside>"
    )


def _頼む札() -> str:
    """一回きりの仕事を頼む — 決まりを作らず、この場で1件。"""
    return (
        "<aside class='form-card'>"
        "<h3 class='form-card__title'>Request a one-off job</h3>"
        "<p class='sub'>Cycle, budget and retries take the designed defaults.</p>"
        "<form method='post' action='/automations/act'>"
        "<input type='hidden' name='what' value='request'>"
        "<div class='form-grid'>"
        "<div class='field'><label for='au-body'>Instruction</label>"
        "<textarea id='au-body' name='body' rows='3' required"
        " placeholder='What should be done — this becomes the instruction'>"
        "</textarea></div>"
        "<div class='field'><label for='au-req-source'>Source</label>"
        "<input type='text' id='au-req-source' name='source' required"
        " placeholder='file:… or db:…'></div>"
        "<div class='field'><label for='au-req-terms'>Required terms</label>"
        "<input type='text' id='au-req-terms' name='required_terms' required"
        " placeholder='words the result must contain, separated by 、 or ,'></div>"
        "<div class='field'><label for='au-req-owner'>Owner</label>"
        "<input type='text' id='au-req-owner' name='owner'"
        " placeholder='optional'></div>"
        "</div>"
        "<div class='form-actions'><button class='btn'>Request</button></div>"
        "</form></aside>"
    )


def _予定(
    rules: tuple[ScheduleRow, ...],
    jobs: tuple[SearchRow, ...],
    done: str | None = None,
) -> str:
    バナー = (
        f"<div class='banner banner--success'>✓ {escape(done)}</div>" if done else ""
    )
    決まり = "".join(
        f"<tr><td class='mono automations-name'>{escape(r.rule)}</td>"
        f"<td class='automations-instr'>{escape(r.instruction)}</td>"
        f"<td class='automations-ver'>{r.version}</td>"
        f"<td class='automations-ver'>{r.active_version if r.active_version else '—'}</td>"
        # 次の対象期間だけを出す。**その期間の仕事が在るかは、すぐ下の表が示す**
        # ——同じことを2箇所で言わない（言い換えを画面で作らない）
        f"<td class='cell-when'>{escape((r.next_period or '—').split('（')[0])}</td>"
        f"<td class='automations-acts'>{_押せる(r)}</td></tr>"
        for r in rules
    )
    仕事 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(j.id)}'>{escape(j.id)}</a></td>"
        f"<td class='automations-instr'>{escape(j.head)}</td>"
        f"<td class='cell-when'>{escape(j.period or '')}</td>"
        f"<td>{_状態(j.state_name)}</td><td class='cell-when'>{escape(j.due)}</td></tr>"
        for j in jobs
    )
    # 頭は頁の決まり（style.py §2）——数を先に言う。routes.py の page-sub の下に載る
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Automations</h1>"
        f"<span class='count-pill'><strong>{len(rules)}</strong> rules</span>"
        f"<span class='page-head__aside num'>{len(jobs)} jobs in flight</span></div>"
    )
    # 空の言葉は本当のことを——表の頭だけ残さず、言葉に置き換える
    決まりの表 = (
        (
            "<div class='wrap automations-rules'><table>"
            "<tr><th>Rule</th><th>Instruction</th>"
            "<th class='automations-ver'>Version</th>"
            "<th class='automations-ver'>Active version</th>"
            "<th>Next period</th><th>Actions</th></tr>" + 決まり + "</table></div>"
        )
        if rules
        else "<p class='empty'>No rules registered — nothing runs until a rule "
             "is written and activated.</p>"
    )
    仕事の表 = (
        (
            "<div class='wrap automations-jobs'><table>"
            "<tr><th>Id</th><th>Title</th><th>Period</th><th>State</th>"
            "<th>Due date</th></tr>" + 仕事 + "</table></div>"
        )
        if jobs
        else "<p class='empty'>No jobs in flight — a job opens when an active rule "
             "reaches its next period, and leaves this list when it is finished "
             "or abandoned.</p>"
    )
    本文 = (
        f"<h3 class='section-title'>{語('業務ルール')}</h3>"
        + 決まりの表
        + "<h3 class='section-title'>Jobs in flight</h3>"
        + 仕事の表
    )
    脇 = _版を積む札(rules) + _頼む札()
    return (
        頭
        + バナー
        + _様式
        + "<div class='page-cols'>"
        + f"<div class='page-main'>{本文}</div>"
        + f"<aside class='page-rail'>{脇}</aside>"
        + "</div>"
    )
