"""いまの眺め — 「いま」の画面が見る、文字と数の入れ物。

設計: 設計/人に見えるもの.md §2。
| いまの眺め | 段ごとの数（待ち・作業中・検査中・人待ち）・作業中の（仕事の識別子・見出し）の列・
最後の脈の時刻（まだ無ければ空）。生の帯の行は履歴の行を使う |

**画面に届くのは文字と ID だけ。振る舞いを持たない。** ただの入れ物。
予告の欄は無い——最後の脈の**事実**だけを持つ（予告はしない）。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NowView(BaseModel):
    """いまの眺め — 環の段ごとの数と、作業中の仕事。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    #: 待ち — 作られた・着手できる。
    queued: int
    #: 作業中 — 実行中の（仕事の識別子・見出し）の列。数は列の長さ。
    working: tuple[tuple[str, str], ...]
    #: 検査中 — 提出済み・終わった（確かめ待ち）。
    checking: int
    #: 人待ち — 承認待ち・答え待ち。
    waiting: int
    #: 時計が最後に書いた時刻 — 静かな時間は書くことが無い(脈は周期で打っている)。まだ無ければ空。
    beat_at: str | None
