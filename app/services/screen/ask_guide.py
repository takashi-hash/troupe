"""案内に答える — 人の問いと画面の写しを LLM へ渡し、答えの文字を受け取る。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの §1「案内」。
| 案内に答える | `ask_guide` | 人の問いと、**画面が既に集めた写し**を LLM へ渡し、
答えの文字を受け取る。帳簿に書かない | **答えを組むのは LLM。案内するだけ——押すのは人** |

律速はここで切る——問いの長さ・往復の上限。器や口に散らさない（正本は1つ）。
"""

from __future__ import annotations

from app.ports.guide_port import GuidePort

#: 問いの長さの上限。窓は公開されている——長文の流し込みで金を溶かさない。
QUESTION_LIMIT = 500

#: 持ち回る往復の上限。記憶は画面が持つ（帳簿に置かない）——器ではなくここで切る。
HISTORY_LIMIT = 3

#: 口が答えを組めなかったときの断り。案内が黙ると人は壊れたと思う。
FALLBACK = "I could not put an answer together just now. Please try again."


def ask_guide(
    guide: GuidePort,
    question: str,
    digest: str,
    history: tuple[tuple[str, str], ...],
) -> str:
    """問いに答えの文字を返す。空の問いには何も返さない——押していないのと同じ。"""
    asked = question.strip()[:QUESTION_LIMIT]
    if not asked:
        return ""
    answer = guide.answer(asked, digest, history[-HISTORY_LIMIT:]).strip()
    return answer or FALLBACK
