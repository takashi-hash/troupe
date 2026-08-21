"""口の型 — 実装は adapters に置く（依存の向きはここで折り返す）。

**置き場は集約ルートごとに1つ**（リポジトリは集約ルート単位で作る）。
帳簿はそれらをまとめて差し出す場——1つの口に全集約を詰め込まない。
"""

from __future__ import annotations

from typing import Protocol, Sequence

from domain.artifact import Artifact
from domain.board import Board
from domain.definition import Definition
from domain.event import Event
from domain.job import Job
from domain.participant import Participant


class JobRepository(Protocol):
    """タスクの置き場 — 集約ルートはタスク1つ。遷移の門と楽観ロックはここが守る"""

    def get(self, job_id: str) -> tuple[Job, int] | None:
        """読み出す — タスクと rev（次の書き込みの期待値）"""
        ...

    def put(self, job: Job, expected_rev: int, events: Sequence[Event]) -> bool:
        """書き込む — タスクと出来事を1回の書き込みで。負けたら偽（楽観ロック）"""
        ...

    def find_by_origin(self, key: str) -> str | None:
        """作成元で探す — 同じ作成元のタスクの id を返す。冪等の要"""
        ...

    def find_by_state(self, kind: str) -> tuple[str, ...]:
        """状態で探す — その状態に居るタスクの id たち（配る・見回るの走査）"""
        ...


class DefinitionRepository(Protocol):
    """業務ルールの置き場 — 版は積むだけ。有効化するのは人だけ"""

    def get(self, name: str) -> Definition | None:
        """読み出す — 名で1件"""
        ...

    def put(self, definition: Definition, events: Sequence[Event]) -> None:
        """書き込む — 業務ルールの門つき（積むだけの破りと必須の出来事の欠けを拒否）"""
        ...

    def enacted(self) -> tuple[Definition, ...]:
        """有効なものたち — 有効な業務ルールの一覧（名指しでなく宣言から導く）"""
        ...


class BoardRepository(Protocol):
    """ボードの置き場 — 方針は積むだけ。凍結するのは人だけ"""

    def get(self, board_id: str) -> Board | None:
        """読み出す — id で1件"""
        ...

    def put(self, board: Board, events: Sequence[Event]) -> None:
        """書き込む — ボードの門つき"""
        ...


class ParticipantRepository(Protocol):
    """参加者の置き場 — 登録と照合の結果を持つ"""

    def get(self, participant_id: str) -> Participant | None:
        """読み出す — 参加者を1件読む"""
        ...

    def put(self, participant: Participant, events: Sequence[Event]) -> None:
        """書き込む — 参加者の登録と照合の結果を帳簿へ"""
        ...


class ArtifactStore(Protocol):
    """成果物の置き場 — 積むだけ。置かれたら不変"""

    def append(self, artifact: Artifact) -> None:
        """積む — 成果物を帳簿に置く"""
        ...

    def get(self, artifact_ref: str) -> Artifact | None:
        """読み出す — 置いた成果物を参照で読む"""
        ...


class EventLog(Protocol):
    """出来事の置き場 — 積むだけの列。書き換えも削除も無い"""

    def append(self, events: Sequence[Event]) -> None:
        """積む — 出来事を追記する"""
        ...

    def count(self, job_id: str, kind: str) -> int:
        """数える — 帳簿にその出来事が何度積まれたかを数える（再試行の回数はここが持つ）"""
        ...


class LedgerPort(Protocol):
    """帳簿の口 — 集約ごとの置き場をまとめて差し出す場。

    集約をまたぐ書き込みはしない（1回の書き込みは1つの集約）。
    """

    @property
    def jobs(self) -> JobRepository:
        """タスクたち — タスクの置き場"""
        ...

    @property
    def definitions(self) -> DefinitionRepository:
        """業務ルールたち — 業務ルールの置き場"""
        ...

    @property
    def boards(self) -> BoardRepository:
        """ボードたち — ボードの置き場"""
        ...

    @property
    def participants(self) -> ParticipantRepository:
        """参加者たち — 参加者の置き場"""
        ...

    @property
    def artifacts(self) -> ArtifactStore:
        """成果物たち — 成果物の置き場"""
        ...

    @property
    def events(self) -> EventLog:
        """出来事たち — 出来事の置き場"""
        ...


class LlmPort(Protocol):
    """LLMの口 — 実装は adapters（Ollama）。domain は LLM の中身を知らない"""

    def chat(self, prompt: str) -> str:
        """話しかける — LLM に問いを渡して応答を受け取る"""
        ...
