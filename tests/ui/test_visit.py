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


def test_全語だけの太字見出しでも割れる() -> None:
    """Gemini の実物その2: `**Subjective**` — 頭文字なしの全語。"""
    body = (
        "Patient Code: P-011\n\n"
        "**Subjective**\nCalm week, log kept.\n\n"
        "**Objective**\n- SpO2 at rest: [ ] %\n"
        "- **Oxygen Saturation (SpO2):** decoy line that must not split\n\n"
        "**Assessment**\nBack to baseline 93%.\n\n"
        "**Plan**\n- Verify the log.\n"
    )
    out = _soap分解(body)
    assert out is not None
    assert "Calm week" in out["s"]
    assert "decoy line" in out["o"]      # 本文中の太字は切れ目にならない
    assert "93%" in out["a"]
    assert "Verify the log" in out["p"]


def test_全語と括弧の頭文字でも割れる() -> None:
    """Gemini の実物その3: `**Subjective (S):**` — 全語が先・頭文字が括弧。"""
    out = _soap分解(
        "**Subjective (S):**\nfeels well\n**Objective (O):**\nSpO2 93%\n"
        "**Assessment (A):**\nstable\n**Plan (P):**\ncontinue"
    )
    assert out is not None and out["o"] == "SpO2 93%"
