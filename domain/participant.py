"""参加者 — 帳簿に名を連ねる者。人間と機体。

申告と実態のずれが最大の事故源。起動時に照合して名乗る——照合を通っていない
参加者は「働ける」にならない（設計/4_集約/集約境界図.md §3）。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

_frozen = ConfigDict(frozen=True, extra="forbid")


class CapabilityDeclaration(BaseModel):
    """能力申告 — 機体が名乗る「何ができるか」。名乗った時点の写しなので不変"""

    model_config = _frozen
    model_name: str  # どの LLM
    sensitivity_ok: bool  # 機微の可否
    accepts: tuple[str, ...]  # 何を受けるか（業務ルールの名）
    reachable_ports: tuple[str, ...]  # どの口と道具に手が届くか


class Participant(BaseModel):
    """参加者 — 登録が同一性。verified が偽のあいだは着手できない"""

    model_config = _frozen
    participant_id: str
    kind: Literal["Human", "Agent"]
    capability: CapabilityDeclaration
    verified: bool = False


class MismatchedDeclaration(Exception):
    """申告のずれ — 実態に無いものを申告した参加者は名乗れない（教訓8）"""


def announce(
    participant: Participant,
    actual_models: frozenset[str],
    actual_ports: frozenset[str],
) -> Participant:
    """名乗る — 起動時に申告と実態を照合して参加する。ずれていたら名乗れない"""
    if participant.capability.model_name not in actual_models:
        raise MismatchedDeclaration(
            f"{participant.participant_id}: 申告した {participant.capability.model_name} が実態に無い"
        )
    missing = set(participant.capability.reachable_ports) - actual_ports
    if missing:
        raise MismatchedDeclaration(
            f"{participant.participant_id}: 申告した口 {sorted(missing)} に手が届かない"
        )
    return participant.model_copy(update={"verified": True})
