"""版の欄 — 人から受け取る値。

設計: 設計/仕事が回る筋道.md §1「人から受け取る値」。
| 版を積む | やること・源・受け入れ基準・周期・日数・使用上限・受け持ちの人・やり直しの上限 |

**画面から app へ渡るのは文字だけ**——受け取る欄が無いと、押しても値が作れない。
DTO は出る向き（今日の行…）だけでなく**入る向き**にも要る。これがその1枚。
振る舞いを持たない。値に組むのは app のサービス（詰め替えるのは app）。

欄が None なら「書かなかった」——版を積むでは題材の初期値が残り、
頼むでは欄が足りないと断られる。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VersionForm(BaseModel):
    """人が書いた版の欄。文字と数だけ。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    instruction: str | None = None
    source: str | None = None
    required_terms: tuple[str, ...] | None = None
    description: str | None = None
    cycle: str | None = None
    days: int | None = None
    budget_calls: int | None = None
    budget_seconds: int | None = None
    owner: str | None = None
    max_retries: int | None = None
