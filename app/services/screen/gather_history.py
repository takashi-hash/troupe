"""履歴を集める — 過去に何を頼み、何が済んだ？

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの.md §1・§2。
| 履歴を集める | `gather_history` | 出来事の列を新しい順に、**どの仕事かの見出しを添えて** | 読むだけ。書かない |

**人が画面を開いたときだけ走る。帳簿に書かない。**
出来事の名は**用語集の語**に写してから渡す（画面で言い換えない）。
見出しは業務ルールと対象期間、依頼発はやることの先頭——どの仕事か判らない列は読めない。
"""

from __future__ import annotations

from app.dto.history_row import HistoryRow
from app.ports.history_reader import HistoryReader
from domain.events.event import EVENT_WORDS

_出来事の語 = {ident: word for word, ident in EVENT_WORDS.items()}


def 見出し(rule: str | None, period: str | None, instruction: str) -> str:
    """どの仕事かの見出し。業務ルールと対象期間、無ければやることの先頭。"""
    if rule is not None:
        return f"{rule}　{period}" if period else rule
    return instruction.splitlines()[0] if instruction else ""


def gather_history(history: HistoryReader, limit: int = 200) -> tuple[HistoryRow, ...]:
    """出来事の列を新しい順に、履歴の行にして返す。読むだけ——帳簿に書かない。"""
    return tuple(
        HistoryRow(
            at=e.at,
            by=e.by,
            what=_出来事の語.get(e.name, e.name),
            job_id=e.job_id,
            head=見出し(e.rule, e.period, e.instruction),
        )
        for e in history.read_latest(limit)
    )
