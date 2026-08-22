"""LLM の道具 — 腐敗防止層。ローカル LLM の応答を、印つきの整えた応答へ翻訳する。

設計: 設計/どう作るか.md §4。
| **adapters** | **業務の規則** | 帳簿の実装・Port の実装・**腐敗防止層** |
LLM の応答は印つきの `Reply` へ翻訳されてから入る（**振り分けるのは domain の仕様**）。

**生の応答はそのまま帳簿へ入らない。** system プロンプトで印の名乗りを指示し
（1行目に「印: 成果」「印: 質問」「印: どちらでもない」、2行目以降が本文）、
1行目を剥がして `Mark` に翻訳する。**名乗りが読めなければ「どちらでもない」に倒す**
——翻訳の失敗は成果でも質問でもない。空の応答も同じで、空だった旨が本文になる。

接続できない・タイムアウト等の例外は**そのまま投げる**。LLM が居ないのは
仕事の失敗ではなく環境の故障——呼ぶ側の `consult` は源の失敗だけを `fail` に倒す。
"""

from __future__ import annotations

import json
import math
import time
import urllib.request

from domain.value_objects.job.reply import Mark, Reply

_SYSTEM_PROMPT = (
    "あなたは一座の働き手です。渡された材料だけで仕事を1歩進めてください。\n"
    "応答の1行目には、必ず「印: 成果」「印: 質問」「印: どちらでもない」の"
    "どれか1つだけを書いてください。2行目以降が本文です。\n"
    "印: 成果 — 受け入れ基準を満たす成果が書けたとき。本文は成果そのもの。\n"
    "印: 質問 — 受け持ちの人に確かめないと進めないとき。本文は質問。\n"
    "印: どちらでもない — どちらとも言えないとき。本文はそう見立てた理由。"
)

_MARKS = {
    "成果": Mark.RESULT,
    "質問": Mark.QUESTION,
    "どちらでもない": Mark.NEITHER,
}


def _read_mark(line: str) -> Mark | None:
    """1行目から名乗りを読む。読めなければ None——信じるかどうかはここでは決めない。"""
    named = line.strip().replace("：", ":").replace(" ", "").replace("　", "")
    if not named.startswith("印:"):
        return None
    return _MARKS.get(named.removeprefix("印:"))


def _translate(content: str) -> Reply:
    """応答の文字を整えた応答へ。名乗りが読めなければ「どちらでもない」に倒す。"""
    text = content.strip()
    if not text:
        return Reply(mark=Mark.NEITHER, body="LLM の応答が空でした")
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
        "## やること",
        instruction,
        "",
        "## 受け入れ基準",
        "必ず含む語: " + "、".join(criteria_terms),
    ]
    if criteria_note.strip():
        lines.append("説明: " + criteria_note)
    lines += ["", "## 源の材料", source_material]
    if answered_questions:
        lines += ["", "## 答えのある質問"]
        for question, answer in answered_questions:
            lines += [f"問: {question}", f"答: {answer}"]
    if previous_result is not None:
        lines += ["", "## 前に出した成果（差し戻されている）", previous_result]
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
        lines = [f"いまの状況: {situation}"]
        if fall_reasons:
            lines.append("止まった理由（古い順）:")
            lines.extend(f"- {reason}" for reason in fall_reasons)
        if previous_result is not None:
            lines.append(f"前に出した成果: {previous_result}")
        if sibling_states:
            lines.append(f"同じ決まり・同じ期間の別の版の仕事の状態: {'、'.join(sibling_states)}")
        payload = json.dumps(
            {
                "model": self._model,
                "messages": (
                    {"role": "system", "content": _SITUATION_PROMPT},
                    {"role": "user", "content": "\n".join(lines)},
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
    "あなたは仕事場の状況を読んで、見立てを書く係です。**判断はしません**——"
    "事実の報告と案だけを書きます。決めるのは人です。\n"
    "応答は次の2つの行で書いてください。\n"
    "見立て: 状況を読んだ結果を1〜2文で。数字の羅列ではなく、何が起きていそうかを言う。\n"
    "理由: そう読んだ根拠を1〜2文で。"
)


def _translate_situation(content: str) -> tuple[str, str]:
    """見立てと理由の行を剥がす。名乗りが読めなければ全文を見立てに倒す。"""
    finding, reason = "", ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("見立て:") or stripped.startswith("見立て："):
            finding = stripped.split(":", 1)[-1].split("：", 1)[-1].strip()
        elif stripped.startswith("理由:") or stripped.startswith("理由："):
            reason = stripped.split(":", 1)[-1].split("：", 1)[-1].strip()
    if not finding:
        finding = content.strip() or "（LLM の応答が空でした）"
    if not reason:
        reason = "（理由の名乗りが無かったので、本文全体を見立てとして扱った）"
    return finding, reason
