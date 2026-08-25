"""診療録の予定の訪問の読み。

設計: 設計/仕事が回る筋道.md §4。
| `ScheduledVisitReader` | Reader | 診療録の予定の**定期**訪問（患者記号・訪問日）を
**文字のまま**写す——穴あきの源を持つ版の展開の材料。リード内かは `reconcile` が判じる。
往診（urgent）は出ない——約束の外 | **app** | adapters | `create`・`audit`・`gather_schedule` |

**よそのコンテキストの写し。中の語に翻訳しない**——患者記号も日付も文字のまま。
読めなければ空——予定が見えない朝に、展開だけが走ることはない。
"""

from __future__ import annotations

from typing import Protocol


class ScheduledVisitReader(Protocol):
    def read_scheduled(self) -> tuple[tuple[str, str], ...]:
        """予定のままの**定期**訪問の（患者記号・訪問日）の列。読めなければ空。"""
        ...
