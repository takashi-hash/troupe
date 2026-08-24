"""訪問の頁 — 下書きの SOAP 切り出しが実物の形式で割れるか。

代役は前埋めの無い訪問を跳ばす——切り出しが死ぬと審査の輪ごと止まる。
"""
from ui.web.visit import _soap分解


def test_geminiの太字見出しで割れる() -> None:
    """Gemini の実物: `**S (Subjective):**` — コロンが太字の内側にある。"""
    body = (
        "### Visit Note Draft (Unsigned)\n\n"
        "**Patient:** P-011\n\n"
        "**S (Subjective):**  \nStable week, daughter logs SpO2 daily.\n\n"
        "**O (Objective):**  \n*   Resting SpO2: \\_\\_\\_%\n\n"
        "**A (Assessment):**  \nSpO2 trend stable at 92-94%.\n\n"
        "**P (Plan):**  \n*   [ ] Verify the SpO2 log.\n"
    )
    out = _soap分解(body)
    assert out is not None
    assert "daughter logs SpO2" in out["s"]
    assert "Resting SpO2" in out["o"]
    assert "92-94%" in out["a"]
    assert "Verify the SpO2 log" in out["p"]


def test_素朴な見出しでも割れる() -> None:
    out = _soap分解("S:\nfeels well\nO:\nBP 120/80\nA:\nstable\nP:\ncontinue")
    assert out == {"s": "feels well", "o": "BP 120/80", "a": "stable", "p": "continue"}


def test_切れなければ発明しない() -> None:
    assert _soap分解("just a paragraph with no headings") is None
