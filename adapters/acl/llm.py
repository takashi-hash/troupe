"""LLM の道具 — 腐敗防止層。LLM の応答を、印つきの整えた応答へ翻訳する。

設計: 設計/どう作るか.md §4。
| **adapters** | **業務の規則** | 帳簿の実装・Port の実装・**腐敗防止層** |
LLM の応答は印つきの `Reply` へ翻訳されてから入る（**振り分けるのは domain の仕様**）。

**生の応答はそのまま帳簿へ入らない。** system プロンプトで印の名乗りを指示し
（1行目に `MARK: RESULT`・`MARK: QUESTION`・`MARK: NEITHER`、2行目以降が本文）、
1行目を剥がして `Mark` に翻訳する。名乗りは**用語集の識別子そのまま**——
`Mark` の値が result・question・neither なので、訳を一段はさまない。
**名乗りが読めなければ「どちらでもない」に倒す**
——翻訳の失敗は成果でも質問でもない。空の応答も同じで、空だった旨が本文になる。

接続できない・タイムアウト等の例外は**そのまま投げる**。LLM が居ないのは
仕事の失敗ではなく環境の故障——呼ぶ側の `consult` は源の失敗だけを `fail` に倒す。
"""

from __future__ import annotations

import json
import math
import time
import urllib.request

from google import genai
from google.genai import types

from domain.value_objects.job.reply import Mark, Reply

#: LLM への指示。**印の名乗りは用語集の識別子そのまま**——`Mark` の値が
#: result・question・neither なので、名乗りもそれに揃う（訳を一段はさまない）。
_SYSTEM_PROMPT = (
    "You are a worker in Troupe. Move the job one step forward, "
    "using only the material you are given.\n"
    "The first line of your reply must be exactly one of "
    "'MARK: RESULT', 'MARK: QUESTION' or 'MARK: NEITHER'. "
    "Everything from the second line on is the body.\n"
    "MARK: RESULT — you can write a result that meets the acceptance criteria. "
    "The body is the result itself.\n"
    "MARK: QUESTION — you cannot go further without asking the owner. "
    "The body is the question.\n"
    "MARK: NEITHER — neither of those. The body is why you read it that way."
)

_MARKS = {
    "RESULT": Mark.RESULT,
    "QUESTION": Mark.QUESTION,
    "NEITHER": Mark.NEITHER,
}


def _read_mark(line: str) -> Mark | None:
    """1行目から名乗りを読む。読めなければ None——信じるかどうかはここでは決めない。"""
    named = line.strip().replace("：", ":").replace(" ", "").replace("　", "").upper()
    if not named.startswith("MARK:"):
        return None
    return _MARKS.get(named.removeprefix("MARK:"))


def _translate(content: str) -> Reply:
    """応答の文字を整えた応答へ。名乗りが読めなければ「どちらでもない」に倒す。"""
    text = content.strip()
    if not text:
        return Reply(mark=Mark.NEITHER, body="The model returned an empty reply.")
    first, _, rest = text.partition("\n")
    mark = _read_mark(first)
    body = rest.strip()
    if mark is None or not body:
        return Reply(mark=Mark.NEITHER, body=text)
    return Reply(mark=mark, body=body)


def _user_message(
    instruction: str,
    criteria_terms: tuple[str, ...],
    criteria_note: str,
    source_material: str,
    answered_questions: tuple[tuple[str, str], ...],
    previous_result: str | None,
) -> str:
    """材料を1つの文にまとめる。LLM へ渡るのは文字だけ。"""
    lines = [
        "## Instruction",
        instruction,
        "",
        "## Acceptance criteria",
        "Required terms: " + ", ".join(criteria_terms),
    ]
    if criteria_note.strip():
        lines.append("Description: " + criteria_note)
    lines += ["", "## Source material", source_material]
    if answered_questions:
        lines += ["", "## Questions already answered"]
        for question, answer in answered_questions:
            lines += [f"Q: {question}", f"A: {answer}"]
    if previous_result is not None:
        lines += ["", "## Previous result (it was sent back)", previous_result]
    return "\n".join(lines)


def _situation_message(
    situation: str,
    fall_reasons: tuple[str, ...],
    previous_result: str | None,
    sibling_states: tuple[str, ...],
) -> str:
    """巡回の材料を1つの文にまとめる。**どの実装から呼んでも同じ文になる。**"""
    lines = [f"Situation: {situation}"]
    if fall_reasons:
        lines.append("Why it stopped (oldest first):")
        lines.extend(f"- {reason}" for reason in fall_reasons)
    if previous_result is not None:
        lines.append(f"Previous result: {previous_result}")
    if sibling_states:
        lines.append(
            "States of jobs from other versions of the same rule and period: "
            + ", ".join(sibling_states)
        )
    return "\n".join(lines)


class OllamaLlm:
    """LLM の実装 — ローカルの Ollama に渡し、整えた応答と使った量を受け取る。"""

    def __init__(self, model: str, base_url: str = "http://localhost:11434") -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    def consult(
        self,
        instruction: str,
        criteria_terms: tuple[str, ...],
        criteria_note: str,
        source_material: str,
        answered_questions: tuple[tuple[str, str], ...],
        previous_result: str | None,
    ) -> tuple[Reply, int, int]:
        """材料を渡し、（整えた応答, 使った回数, 使った秒）を受け取る。

        回数は1。秒は測った差の切り上げで、最低1——使ったのに0は嘘になる。
        """
        payload = json.dumps(
            {
                "model": self._model,
                "messages": (
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": _user_message(
                            instruction,
                            criteria_terms,
                            criteria_note,
                            source_material,
                            answered_questions,
                            previous_result,
                        ),
                    },
                ),
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self._base_url + "/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        before = time.monotonic()
        with urllib.request.urlopen(request) as response:
            raw = json.loads(response.read().decode("utf-8"))
        seconds = max(1, math.ceil(time.monotonic() - before))
        content = raw["message"]["content"]
        return _translate(str(content)), 1, seconds

    def read_situation(
        self,
        situation: str,
        fall_reasons: tuple[str, ...],
        previous_result: str | None,
        sibling_states: tuple[str, ...],
    ) -> tuple[str, str, int, int]:
        """状況を読み、（見立て, 理由, 回数, 秒）を返す。巡回の口。"""
        payload = json.dumps(
            {
                "model": self._model,
                "messages": (
                    {"role": "system", "content": _SITUATION_PROMPT},
                    {
                        "role": "user",
                        "content": _situation_message(
                            situation, fall_reasons, previous_result, sibling_states
                        ),
                    },
                ),
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self._base_url + "/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        before = time.monotonic()
        with urllib.request.urlopen(request) as response:
            raw = json.loads(response.read().decode("utf-8"))
        seconds = max(1, math.ceil(time.monotonic() - before))
        finding, reason = _translate_situation(str(raw["message"]["content"]))
        return finding, reason, 1, seconds


_SITUATION_PROMPT = (
    "You read the situation in the workplace and write an assessment. "
    "You do NOT decide anything — you report facts and suggest. A human decides.\n"
    "Write your reply as exactly these two lines.\n"
    "FINDING: what you make of the situation, in one or two sentences. "
    "Not a list of numbers — say what seems to be going on.\n"
    "REASON: what you based that on, in one or two sentences."
)


def _translate_situation(content: str) -> tuple[str, str]:
    """見立てと理由の行を剥がす。名乗りが読めなければ全文を見立てに倒す。"""
    finding, reason = "", ""
    for line in content.splitlines():
        stripped = line.strip().replace("：", ":")
        if stripped.upper().startswith("FINDING:"):
            finding = stripped.split(":", 1)[-1].strip()
        elif stripped.upper().startswith("REASON:"):
            reason = stripped.split(":", 1)[-1].strip()
    if not finding:
        finding = content.strip() or "(the model returned an empty reply)"
    if not reason:
        reason = "(no reason was named, so the whole body was taken as the finding)"
    return finding, reason


class GeminiLlm:
    """LLM の実装 — Google の Gemini に渡し、整えた応答と使った量を受け取る。

    設計: 設計/どう作るか.md §5「llm の中身は Ollama と Gemini」。

    **翻訳は Ollama と同じものを使う。** 違うのは輸送だけ——
    印の剥がしも、材料のまとめかたも、見立ての読みかたも、この1枚の中で共有する。
    翻訳が実装ごとに分かれたら、腐敗防止層が2つになる（同じ外の言葉が2通りに中へ入る）。

    どこへ繋ぐかは環境が決める（`GOOGLE_GENAI_USE_VERTEXAI`・`GOOGLE_CLOUD_PROJECT`・
    `GOOGLE_CLOUD_LOCATION`、または `GOOGLE_API_KEY`）——**注ぐのは main.py だけ**で、
    ここは繋ぎ先を選ばない。クラウドの上では鍵を持たない（実行の身元で通る）。

    例外はそのまま投げる。Gemini に届かないのは仕事の失敗ではなく環境の故障。
    """

    def __init__(self, model: str = "gemini-3.5-flash") -> None:
        self._model = model
        self._client = genai.Client()

    def _問う(self, system: str, message: str) -> tuple[str, int]:
        """渡して、（応答の文字, 使った秒）を受け取る。**ここだけが外に触る。**

        秒は測った差の切り上げで、最低1——使ったのに0は嘘になる。
        """
        before = time.monotonic()
        response = self._client.models.generate_content(
            model=self._model,
            contents=message,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        seconds = max(1, math.ceil(time.monotonic() - before))
        return response.text or "", seconds

    def consult(
        self,
        instruction: str,
        criteria_terms: tuple[str, ...],
        criteria_note: str,
        source_material: str,
        answered_questions: tuple[tuple[str, str], ...],
        previous_result: str | None,
    ) -> tuple[Reply, int, int]:
        """材料を渡し、（整えた応答, 使った回数, 使った秒）を受け取る。回数は1。"""
        content, seconds = self._問う(
            _SYSTEM_PROMPT,
            _user_message(
                instruction,
                criteria_terms,
                criteria_note,
                source_material,
                answered_questions,
                previous_result,
            ),
        )
        return _translate(content), 1, seconds

    def read_situation(
        self,
        situation: str,
        fall_reasons: tuple[str, ...],
        previous_result: str | None,
        sibling_states: tuple[str, ...],
    ) -> tuple[str, str, int, int]:
        """状況を読み、（見立て, 理由, 回数, 秒）を返す。巡回の口。"""
        content, seconds = self._問う(
            _SITUATION_PROMPT,
            _situation_message(situation, fall_reasons, previous_result, sibling_states),
        )
        finding, reason = _translate_situation(content)
        return finding, reason, 1, seconds
