"""仮の LLM の口 — まだ本物に繋いでいない間の実装。段5で Ollama に差し替える。

口の実装は adapters の仕事（組み立ての根には置かない）。
**作り話をしない**——渡された指示を写し、本物でないことを成果物自身が名乗る。
中身を作れないので、受け入れ基準を満たすかはチェックが決める（満たさなければ止まる）。
"""

from __future__ import annotations


class StubLlm:
    """渡されたプロンプトの「やること」を写して返すだけの口"""

    def chat(self, prompt: str) -> str:
        """話しかける — 指示を写し、まだ本物でないことを名乗る"""
        instruction = _section(prompt, "# やること")
        acceptance = _section(prompt, "# 受け入れ基準")
        return "\n".join(
            [
                f"（仮の成果物）{instruction}",
                "まだ本物の LLM に繋いでいないため、源を読んでいません。",
                f"満たすべき条件: {acceptance}",
            ]
        )


def _section(prompt: str, heading: str) -> str:
    """プロンプトの見出しの下の1行を取り出す"""
    for block in prompt.split("\n" + heading + "\n")[1:]:
        return block.split("\n")[0].strip()
    return ""
