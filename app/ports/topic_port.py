"""題材のデータへの口。

設計: 設計/仕事が回る筋道.md §4・§1「人が始めるもの」。
| `TopicPort` | Port | 題材のデータ（版の中身）を読む | **app** | adapters | `add_version` |
| 版を積む | `add_version` | **題材のデータを初期値として読み、人が上書きした値**で版を積む |

これは初期値の側——読んだ束を画面に出し、人が上書きしてから版になる。
題材にデータが無ければ None——初期値なしで人がぜんぶ書く。
"""

from __future__ import annotations

from typing import Protocol

from domain.values.rule.copied import Copied
from domain.values.rule.rule_name import RuleName


class TopicPort(Protocol):
    def read(self, rule: RuleName) -> Copied | None:
        """題材のデータを初期値として読む。無ければ None。"""
        ...
