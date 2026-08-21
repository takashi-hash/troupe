"""業務ルール — タスクを生む規則。名が版の列を束ね、enact するのは Human だけ。

版は積むだけ（上書き無し）。業務の指示（プロンプトの中身）もここに住む——
コード側の FramePrompt と分かれる（設計/9_働き手/働き手とLLM.md §2）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from domain.job import Budget

_frozen = ConfigDict(frozen=True, extra="forbid")

Cadence = Literal["weekly", "monthly"]
"""周期 — 業務ルールがタスクを生む刻み"""


class Version(BaseModel):
    """版 — 業務ルールの1つの世代。積むだけで消えない。使用上限も業務の指示もここが決める"""

    model_config = _frozen
    number: int
    instruction: str  # 業務の指示（プロンプトの中身）
    acceptance: str  # 受け入れ基準（例が仕様の置き場）
    cadence: Cadence
    deadline_days: int  # 作成から期限までの日数
    budget: Budget
    source_refs: tuple[str, ...] = ()  # 読むべき源（ReadPort の ID）——業務ルールが決める
    max_retries: int = 3  # 最大再試行——再試行の規則はポリシー（業務ルールが決める）
    must_contain: tuple[str, ...] = ()  # 必ず含む語——受け入れ基準の決定的な部分（チェックが見る）
    checkpoint_position: str | None = None  # 承認待ちの位置。無ければ承認済みへ直行
    needs_apply: bool = False  # 適用が要るか。要らなければ承認済みから直に完了へ


class Definition(BaseModel):
    """業務ルール — 名（同一性）が版の列（値）を束ねる。enacted が None なら、まだ有効でない"""

    model_config = _frozen
    name: str
    board_id: str
    versions: tuple[Version, ...]
    enacted: int | None = None  # 有効な版の number。effect するのは Human だけ


class AppendOnlyViolation(Exception):
    """積むだけの破り — 版・方針の列を減らす・書き換える書き込みは存在できない"""


class CannotEnact(Exception):
    """有効化できない — 存在しない版は enact できない"""


def enact(definition: Definition, number: int) -> Definition:
    """有効化する — Human だけの行為。誰が有効化したかは DefinitionEnacted の Event が持つ"""
    if not any(v.number == number for v in definition.versions):
        raise CannotEnact(f"版 {number} は {definition.name} に無い")
    return definition.model_copy(update={"enacted": number})


def append(definition: Definition, version: Version) -> Definition:
    """積む — 版は末尾にだけ足せる。上書きは無い"""
    if version.number != len(definition.versions) + 1:
        raise AppendOnlyViolation(f"次の版は {len(definition.versions) + 1}。{version.number} は積めない")
    return definition.model_copy(update={"versions": definition.versions + (version,)})


def definition_required_events(old: Definition | None, new: Definition) -> frozenset[str]:
    """業務ルールの必須出来事 — 書き込みの変化から必須 Event を導く（業務ルールの門）。

    版が減った・書き換わったら AppendOnlyViolation。enacted が無い版なら CannotEnact。
    """
    old_versions: tuple[Version, ...] = old.versions if old else ()
    if new.versions[: len(old_versions)] != old_versions:
        raise AppendOnlyViolation(f"{new.name}: 版は積むだけ——減らせない・書き換えられない")
    if new.enacted is not None and not any(v.number == new.enacted for v in new.versions):
        raise CannotEnact(f"{new.name}: 版 {new.enacted} は無い")
    required: set[str] = set()
    if len(new.versions) > len(old_versions):
        required.add("VersionAppended")
    if (old.enacted if old else None) != new.enacted:
        required.add("DefinitionEnacted")
    return frozenset(required)


def current_period(cadence: Cadence, now: datetime) -> str:
    """いまの対象期間 — 周期から対象期間の文字列を導く（作成元の鍵の材料）"""
    if cadence == "weekly":
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"
    return f"{now.year}-{now.month:02d}"


def definition_ref(name: str, number: int) -> str:
    """業務ルールの参照 — 参照の形式は業務ルールが持つ（外で組み立てない）"""
    return f"業務ルール/{name}/{number}"


def parse_definition_ref(ref: str) -> tuple[str, int]:
    """参照を読む — 業務ルールの参照から名と版を取り出す"""
    _, name, number = ref.split("/")
    return name, int(number)


def artifact_slot(name: str, period: str) -> str:
    """成果物の枠 — 業務ルールの名と対象期間から決まる。参照の形式はドメインが持つ"""
    return f"成果物/{name}/{period}"


def acceptance_ref(name: str, number: int) -> str:
    """受け入れ基準の参照 — 業務ルールの版の受け入れ基準を指す"""
    return f"{definition_ref(name, number)}#受け入れ基準"
