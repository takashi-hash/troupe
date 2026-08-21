"""成果物 — タスクが生んだもの。帳簿に置かれ、次の係が拾う。証拠が指す先。

置かれたら不変。直しは新しい成果物（設計/3_部品/部品一覧.md §2）。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Artifact(BaseModel):
    """成果物 — 置き場（artifact_ref）で指す。中身は不変"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    artifact_ref: str
    job_id: str
    body: str
    at: datetime
