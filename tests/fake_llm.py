"""偽の LLM の口 — 決まった応答を返す。働き手のループを LLM 無しで決定的に回す。"""

from __future__ import annotations


class FakeLlm:
    """渡された応答を順に返すだけの口。プロンプトは記録して、あとで確かめる"""

    def __init__(self, *replies: str) -> None:
        self._replies = list(replies)
        self.prompts: list[str] = []

    def chat(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._replies.pop(0) if self._replies else ""
