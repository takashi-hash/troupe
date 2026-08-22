"""押せること — いまこの業務ルールに、人が押せる操作はどれか。

設計: 設計/仕事が回る筋道.md §2「仕様」・人に見えるもの.md §3。
| いまこの業務ルールに**人が押せる操作**はどれか | 有効な版の有無 | 版を積む・有効にする はいつでも。**止めるは有効な版があるときだけ** |

人なら誰でも押せる（公理6つの操作ではない）——人を材料に取らない。
"""

from __future__ import annotations


def rule_allowed(active_version: int | None) -> tuple[str, ...]:
    """押せる操作の識別子の列（add_version・activate・deactivate）。"""
    always = ("add_version", "activate")
    return always + (("deactivate",) if active_version is not None else ())
