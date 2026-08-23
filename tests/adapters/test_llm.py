"""LLM の実装の壊しかた。設計/どう作るか.md §4——生の応答はそのまま帳簿へ入らない。

Ollama は起動しない——urllib を差し替えて、翻訳（印の剥がし）と使った量だけを見る。
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

import pytest

import adapters.acl.llm as llm_module
from adapters.acl.llm import GeminiLlm, OllamaLlm
from app.ports.llm_port import LlmPort
from domain.value_objects.job.reply import Mark


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self._payload = json.dumps(
            {"message": {"role": "assistant", "content": content}}, ensure_ascii=False
        ).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _応答を差す(
    monkeypatch: pytest.MonkeyPatch, content: str
) -> list[urllib.request.Request]:
    seen: list[urllib.request.Request] = []

    def fake_urlopen(request: urllib.request.Request, **kwargs: Any) -> _FakeResponse:
        seen.append(request)
        return _FakeResponse(content)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return seen


def _問う(llm: LlmPort) -> tuple[Any, int, int]:
    return llm.consult(
        instruction="先月分の請求を集計する",
        criteria_terms=("2026-07", "請求"),
        criteria_note="先月分の請求がすべて出ていること",
        source_material="請求は42件、計84万円",
        answered_questions=(("締め日は？", "毎月末です"),),
        previous_result=None,
    )


def test_成果の名乗りを剥がして印にする(monkeypatch: pytest.MonkeyPatch) -> None:
    _応答を差す(monkeypatch, "MARK: RESULT\n2026-07 の請求は42件、計84万円")
    reply, calls, seconds = _問う(OllamaLlm(model="qwen3"))
    assert reply.mark is Mark.RESULT
    assert reply.body == "2026-07 の請求は42件、計84万円"
    assert calls == 1
    assert seconds >= 1


def test_質問の名乗りを剥がして印にする(monkeypatch: pytest.MonkeyPatch) -> None:
    _応答を差す(monkeypatch, "MARK: QUESTION\n締めの区切りは暦月ですか？")
    reply, _, _ = _問う(OllamaLlm(model="qwen3"))
    assert reply.mark is Mark.QUESTION
    assert reply.body == "締めの区切りは暦月ですか？"


def test_どちらでもないの名乗りも印になる(monkeypatch: pytest.MonkeyPatch) -> None:
    _応答を差す(monkeypatch, "MARK: NEITHER\n源の数字が基準と噛み合いません")
    reply, _, _ = _問う(OllamaLlm(model="qwen3"))
    assert reply.mark is Mark.NEITHER
    assert reply.body == "源の数字が基準と噛み合いません"


def test_名乗りが読めなければどちらでもないに倒す(monkeypatch: pytest.MonkeyPatch) -> None:
    """翻訳の失敗は成果でも質問でもない——本文は捨てず、印だけ倒す。"""
    _応答を差す(monkeypatch, "請求は42件でした")
    reply, _, _ = _問う(OllamaLlm(model="qwen3"))
    assert reply.mark is Mark.NEITHER
    assert reply.body == "請求は42件でした"


def test_使った秒は最低1(monkeypatch: pytest.MonkeyPatch) -> None:
    """一瞬で返っても、使ったのに0秒とは書かない。"""
    _応答を差す(monkeypatch, "MARK: RESULT\n請求は42件")
    monkeypatch.setattr(time, "monotonic", lambda: 5.0)
    _, _, seconds = _問う(OllamaLlm(model="qwen3"))
    assert seconds == 1


def test_使った秒は差の切り上げ(monkeypatch: pytest.MonkeyPatch) -> None:
    _応答を差す(monkeypatch, "MARK: RESULT\n請求は42件")
    ticks = [10.0, 12.2]

    def fake_monotonic() -> float:
        return ticks.pop(0) if ticks else 12.2

    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    _, _, seconds = _問う(OllamaLlm(model="qwen3"))
    assert seconds == 3


def test_渡る形はOllamaのchatで印の指示が載る(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _応答を差す(monkeypatch, "MARK: RESULT\n請求は42件")
    _問う(OllamaLlm(model="qwen3", base_url="http://localhost:11434"))
    request = seen[0]
    assert request.full_url == "http://localhost:11434/api/chat"
    assert isinstance(request.data, bytes)
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "qwen3"
    assert payload["stream"] is False
    system = payload["messages"][0]
    assert system["role"] == "system"
    for 名乗り in ("MARK: RESULT", "MARK: QUESTION", "MARK: NEITHER"):
        assert 名乗り in system["content"]


# --- Gemini — 輸送だけが違う。翻訳が Ollama と同じものであることを、ここで確かめる ---


class _FakeGeminiResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class _FakeGeminiModels:
    def __init__(self, text: str | None) -> None:
        self._text = text
        self.seen: list[dict[str, Any]] = []

    def generate_content(
        self, *, model: str, contents: Any, config: Any
    ) -> _FakeGeminiResponse:
        self.seen.append({"model": model, "contents": contents, "config": config})
        return _FakeGeminiResponse(self._text)


class _FakeGeminiClient:
    def __init__(self, text: str | None) -> None:
        self.models = _FakeGeminiModels(text)


def _Geminiを差す(
    monkeypatch: pytest.MonkeyPatch, text: str | None
) -> _FakeGeminiModels:
    """Gemini へは繋がない。渡した形と、翻訳の結果だけを見る。"""
    client = _FakeGeminiClient(text)
    monkeypatch.setattr(llm_module.genai, "Client", lambda *a, **k: client)
    return client.models


def test_Geminiでも成果の名乗りを剥がして印にする(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _Geminiを差す(monkeypatch, "MARK: RESULT\n2026-07 の請求は42件、計84万円")
    reply, calls, seconds = _問う(GeminiLlm())
    assert reply.mark is Mark.RESULT
    assert reply.body == "2026-07 の請求は42件、計84万円"
    assert calls == 1
    assert seconds >= 1


def test_Geminiでも名乗りが読めなければどちらでもないに倒す(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _Geminiを差す(monkeypatch, "請求は42件でした")
    reply, _, _ = _問う(GeminiLlm())
    assert reply.mark is Mark.NEITHER
    assert reply.body == "請求は42件でした"


def test_Geminiの応答が空でも本文の空な応答は作らない(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`response.text` は None になりうる。**本文が空の整えた応答は義務違反。**"""
    _Geminiを差す(monkeypatch, None)
    reply, _, _ = _問う(GeminiLlm())
    assert reply.mark is Mark.NEITHER
    assert reply.body.strip()


def test_Geminiへ渡る形はモデルと印の指示(monkeypatch: pytest.MonkeyPatch) -> None:
    models = _Geminiを差す(monkeypatch, "MARK: RESULT\n請求は42件")
    _問う(GeminiLlm(model="gemini-3.5-flash"))
    渡した = models.seen[0]
    assert 渡した["model"] == "gemini-3.5-flash"
    for 名乗り in ("MARK: RESULT", "MARK: QUESTION", "MARK: NEITHER"):
        assert 名乗り in 渡した["config"].system_instruction
    assert "先月分の請求を集計する" in 渡した["contents"]


def test_巡回の材料はOllamaとGeminiで同じ文になる(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**翻訳は共有**——実装ごとに材料のまとめかたが分かれたら、腐敗防止層が2つになる。"""
    材料 = ("in progress, no movement for 12 hours", ("the source could not be read",), "previous result", ("Failed",))
    models = _Geminiを差す(monkeypatch, "FINDING: the source is down\nREASON: the same reason three times")
    見立て, 理由, calls, seconds = GeminiLlm().read_situation(*材料)
    assert 見立て == "the source is down"
    assert 理由 == "the same reason three times"
    assert (calls, seconds >= 1) == (1, True)

    ollama_seen = _応答を差す(monkeypatch, "FINDING: x\nREASON: y")
    OllamaLlm(model="qwen3").read_situation(*材料)
    ollama_data = ollama_seen[0].data
    assert isinstance(ollama_data, bytes)
    渡した = json.loads(ollama_data.decode("utf-8"))["messages"][1]["content"]
    assert 渡した == models.seen[0]["contents"]


def test_GeminiもLLMの口を名乗れる(monkeypatch: pytest.MonkeyPatch) -> None:
    """**口が1つであることの証拠**——差し替えても呼ぶ側は何も知らない。"""
    _Geminiを差す(monkeypatch, "MARK: RESULT\n請求は42件")
    口: LlmPort = GeminiLlm()
    assert _問う(口)[0].mark is Mark.RESULT


# --- 案内 — 問いと写しを渡し、答えの文字だけを受け取る。書く道具は持たない ---


def test_案内は問いと写しと往復を渡して答えを受け取る(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from adapters.acl.llm import GeminiGuide, _GUIDE_PROMPT

    models = _Geminiを差す(monkeypatch, "Open /day and sign the visit.")
    答え = GeminiGuide().answer(
        "What needs me today?",
        "1 visit awaiting signature (P-003).",
        (("Anything urgent?", "One approval in /inbox."),),
    )
    assert 答え == "Open /day and sign the visit."
    渡した = models.seen[0]["contents"]
    assert "What needs me today?" in 渡した
    assert "1 visit awaiting signature (P-003)." in 渡した
    assert "Q: Anything urgent?" in 渡した
    assert models.seen[0]["config"].system_instruction == _GUIDE_PROMPT


def test_案内は空の応答を空のまま返す(monkeypatch: pytest.MonkeyPatch) -> None:
    """断りの文言に変えるのは ask_guide——ここは倒すだけ。"""
    from adapters.acl.llm import GeminiGuide

    _Geminiを差す(monkeypatch, None)
    assert GeminiGuide().answer("q", "digest", ()) == ""


def test_案内は例外を空文字に倒す(monkeypatch: pytest.MonkeyPatch) -> None:
    """窓は公開されている——案内の故障で画面を落とさない。"""
    from adapters.acl.llm import GeminiGuide

    class _Raising:
        class models:  # noqa: N801 — 偽物の形合わせ
            @staticmethod
            def generate_content(**kwargs: Any) -> None:
                raise RuntimeError("vertex is down")

    monkeypatch.setattr(llm_module.genai, "Client", lambda *a, **k: _Raising())
    assert GeminiGuide().answer("q", "digest", ()) == ""
