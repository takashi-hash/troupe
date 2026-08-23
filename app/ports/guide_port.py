"""案内の口。

設計: 設計/仕事が回る筋道.md §4。
| `GuidePort` | Port | 人の問いと写し（文字）を渡し、**答えの文字**を受け取る。
**仕事の外の一呼び**——使った量はどの仕事にも積まない（積む仕事が無い）。
暴走は律速（問いの長さ・往復の上限——`ask_guide` が切る）で止める。
**書く道具を受け取らない——案内から実行に届く道は型に無い** | **app** | adapters | `ask_guide` |

答えが組めなければ空文字を返す——断りの文言に変えるのは `ask_guide`。
"""

from __future__ import annotations

from typing import Protocol


class GuidePort(Protocol):
    def answer(
        self,
        question: str,
        digest: str,
        history: tuple[tuple[str, str], ...],
    ) -> str:
        """問い・写し・直近の往復を渡し、答えの文字を受け取る。組めなければ空。"""
        ...
