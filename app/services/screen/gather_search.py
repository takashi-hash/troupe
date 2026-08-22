"""検索する — あの仕事はどこ？

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの.md §1・§2。
| 検索する | `gather_search` | 絞り込みの条件で仕事の行を引く——**終わったものも含めて** | 同上。**状態の語→識別子の橋はここ** |

**人が画面を開いたときだけ走る。帳簿に書かない。**
絞り込みの条件は文字だけ（画面から渡るのは文字だけ）——**状態の表示（用語集の語）を
状態の識別子に写すのはここ**。返す行の状態の名は用語集の語に写し戻す。
"""

from __future__ import annotations

from app.dto.row_filter import RowFilter
from app.dto.search_row import SearchRow
from app.ports.search_reader import SearchReader
from app.services.screen.gather_history import heading
from domain.aggregates.job.life import STATE_WORDS

_状態の語 = {ident: word for word, ident in STATE_WORDS.items()}


def gather_search(search: SearchReader, filter: RowFilter) -> tuple[SearchRow, ...]:
    """条件に合う仕事を検索の行にして返す——終わったものも含めて。読むだけ。"""
    state = STATE_WORDS.get(filter.state_label, filter.state_label) if filter.state_label else None
    return tuple(
        SearchRow(
            id=hit.id,
            head=heading(hit.rule, hit.period, hit.instruction),
            period=hit.period,
            instruction=hit.instruction,
            state_name=_状態の語.get(hit.state_name, hit.state_name),
            due=hit.due[:16].replace("T", " "),
            assignee_name=hit.assignee_name,
        )
        for hit in search.read(filter.keyword, state, filter.rule, filter.assignee)
    )
