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


class FakeSource:
    """偽の源の口 — 決まった中身を返す。源を読む働き手を、本物の源なしで回す"""

    def __init__(self, body: str = "検査は緑でした（72件）") -> None:
        self._body = body
        self.reads = 0

    def read(self) -> str:
        self.reads += 1
        return self._body


class BrokenSource:
    """読めない源 — 落ちる体（源が落ちている・権限が無い）"""

    def read(self) -> str:
        raise OSError("源が読めない")
