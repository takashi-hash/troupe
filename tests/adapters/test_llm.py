"""LLM の実装の壊しかた。設計/どう作るか.md §4——生の応答はそのまま帳簿へ入らない。

Ollama は起動しない——urllib を差し替えて、翻訳（印の剥がし）と使った量だけを見る。
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

import pytest

from adapters.acl.llm import OllamaLlm
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
    _応答を差す(monkeypatch, "印: 成果\n2026-07 の請求は42件、計84万円")
    reply, calls, seconds = _問う(OllamaLlm(model="qwen3"))
    assert reply.mark is Mark.RESULT
    assert reply.body == "2026-07 の請求は42件、計84万円"
    assert calls == 1
    assert seconds >= 1


def test_質問の名乗りを剥がして印にする(monkeypatch: pytest.MonkeyPatch) -> None:
    _応答を差す(monkeypatch, "印: 質問\n締めの区切りは暦月ですか？")
    reply, _, _ = _問う(OllamaLlm(model="qwen3"))
    assert reply.mark is Mark.QUESTION
    assert reply.body == "締めの区切りは暦月ですか？"


def test_どちらでもないの名乗りも印になる(monkeypatch: pytest.MonkeyPatch) -> None:
    _応答を差す(monkeypatch, "印: どちらでもない\n源の数字が基準と噛み合いません")
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
    _応答を差す(monkeypatch, "印: 成果\n請求は42件")
    monkeypatch.setattr(time, "monotonic", lambda: 5.0)
    _, _, seconds = _問う(OllamaLlm(model="qwen3"))
    assert seconds == 1


def test_使った秒は差の切り上げ(monkeypatch: pytest.MonkeyPatch) -> None:
    _応答を差す(monkeypatch, "印: 成果\n請求は42件")
    ticks = [10.0, 12.2]

    def fake_monotonic() -> float:
        return ticks.pop(0) if ticks else 12.2

    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    _, _, seconds = _問う(OllamaLlm(model="qwen3"))
    assert seconds == 3


def test_渡る形はOllamaのchatで印の指示が載る(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _応答を差す(monkeypatch, "印: 成果\n請求は42件")
    _問う(OllamaLlm(model="qwen3", base_url="http://localhost:11434"))
    request = seen[0]
    assert request.full_url == "http://localhost:11434/api/chat"
    assert isinstance(request.data, bytes)
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "qwen3"
    assert payload["stream"] is False
    system = payload["messages"][0]
    assert system["role"] == "system"
    for 名乗り in ("印: 成果", "印: 質問", "印: どちらでもない"):
        assert 名乗り in system["content"]
