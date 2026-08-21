"""口の型 — 実装は adapters に置く（依存の向きはここで折り返す）。

**読み口もここに置く**（2026-08-21。SheetSource を ui/reads.py から移した——
口の型が ui に在ったせいで、app の輪から画面の材料に触れられず、
判定が画面の中に落ちた。層の間違いが掟破りを呼んだ形）。

**置き場は集約ルートごとに1つ**（リポジトリは集約ルート単位で作る）。
帳簿はそれらをまとめて差し出す場——1つの口に全集約を詰め込まない。
"""

from __future__ import annotations

from typing import Protocol, Sequence

from domain.artifact import Artifact
from domain.board import Board
from domain.definition import Definition
from domain.event import Event
from domain.evidence import Evidence
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

    @property
    def evidences(self) -> EvidenceStore:
        """証拠たち — 証拠の置き場"""
        ...


class LlmPort(Protocol):
    """LLMの口 — 実装は adapters（Ollama）。domain は LLM の中身を知らない"""

    @property
    def name(self) -> str:
        """LLMの名 — 能力申告が名乗る model_name の実態。申告と突き合わせる相手"""
        ...

    def chat(self, prompt: str) -> str:
        """話しかける — LLM に問いを渡して応答を受け取る"""
        ...


class CustomPort(Protocol):
    """カスタムの口 — 現場のデータ（方針と業務ルール）を読む。

    土台はカスタムの**中身**を1行も知らない——読むのは方針と業務ルールという**型**だけ。
    次の現場は、注入するデータの差し替えで済む。
    """

    def load(self) -> tuple[Board, tuple[Definition, ...]]:
        """読み込む — 注入するデータをまとめて読む。凍結も有効化もされていない形で返す"""
        ...


class SourcePort(Protocol):
    """源の口 — 読むだけ。1つ落ちても他は回る（書き口とは別物として隔離）"""

    def read(self) -> str:
        """源を読む — 読んだ中身を返す。読めなければ例外（働き手が環境エラーに落とす）"""
        ...


class EvidenceStore(Protocol):
    """証拠の置き場 — 積むだけ。置かれたら不変"""

    def append(self, evidence: Evidence) -> None:
        """積む — 証拠を帳簿に置く"""
        ...

    def get(self, evidence_ref: str) -> Evidence | None:
        """読み出す — 参照で読む"""
        ...


class SheetSource(Protocol):
    """枚の材料の口 — 画面と surface が読むものだけ。書く口は無い（画面は常に導出）"""

    def standing_jobs(self) -> tuple[Job, ...]:
        """立っているタスク"""
        ...

    def all_jobs(self) -> tuple[Job, ...]:
        """すべてのタスク"""
        ...

    def enacted_definitions(self) -> tuple[Definition, ...]:
        """有効な業務ルールたち"""
        ...

    def all_definitions(self) -> tuple[Definition, ...]:
        """すべての業務ルール"""
        ...

    def events_for(self, job_id: str) -> tuple[Event, ...]:
        """そのタスクの出来事"""
        ...

    def recent_events(self, limit: int = 200) -> tuple[Event, ...]:
        """近ごろの出来事"""
        ...

    def origin_keys(self) -> frozenset[str]:
        """作成元の鍵たち"""
        ...
