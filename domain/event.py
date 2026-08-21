"""出来事 — 観察された事実。判断を含まない。積むだけの列に積まれる不変の値。

**名前は型**（用語集 §12 の一覧がそのまま EventKind）。打ち間違いは型チェックで落ちる——
状態を型で守ったのと同じ守りを、出来事にもかける。一覧が用語集と一致していることは
tests/event_kinds_lint.py が見張る。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EventKind = Literal[
    # タスク
    "JobCreated",
    "JobDispatched",
    "LeaseTaken",
    "LeaseReleased",
    "LeaseExpired",
    "ProgressLogged",
    "JobSubmitted",
    "InquiryAsked",
    "InquiryAnswered",
    "CheckPassed",
    "CheckBlocked",
    "ReviewPassed",
    "ReviewReturned",
    "CheckpointReached",
    "CheckpointApproved",
    "CheckpointBypassed",
    "JobConfirmed",
    "ApplyAttempted",
    "JobApplied",
    "JobClosed",
    "FailureOccurred",
    "Retried",
    "BudgetExceeded",
    # 業務ルール・提案・方針
    "VersionAppended",
    "DefinitionEnacted",
    "ProposalCreated",
    "ProposalEnacted",
    "ProposalRejected",
    "ConstitutionAppended",
    "ConstitutionFrozen",
    "ConstitutionUnfrozen",
    # 参加者・源
    "Announced",
    "AgentDown",
    "AgentRecovered",
    "ReadPortDown",
    "ReadPortRecovered",
    "DiscrepancyFound",
    # 会話
    "UtteranceLogged",
    "InstructionTranscribed",
]
"""出来事の名前 — 用語集 §12 が正本。ここに無い名前は書けない"""


class Event(BaseModel):
    """出来事 — 名前は EventKind（型）。積むだけ・上書き無し"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: EventKind
    at: datetime
    job_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
