"""詳細の材料の読み。

設計: 設計/仕事が回る筋道.md §4・人に見えるもの.md §2。
| `DetailReader` | Reader | 詳細の材料（出来事の列・質問と回答の本文・見立ての本文・
**成果の中身**・**根拠の引用**） | **app** | adapters | 詳細の画面 |

**Reader の返す型は渡す先で決まる**——渡る先は画面なので、**文字と ID だけ**。
本文はそのまま運ぶ——**縮めない**。縮めると人が判断する材料が減る（人に見えるもの §2）。
状態の名・期日・担当・確かめ期日・押せることは集約と仕様から来る——ここでは運ばない。
"""

from __future__ import annotations

from typing import Protocol

from domain.obligations import Value
from domain.value_objects.job.job_id import JobId


class DetailMaterial(Value):
    """詳細の材料 — 文字と ID だけ。振る舞いを持たない。"""

    #: 出来事の列 — （時刻, 誰が, 何が起きたか）。出来事の行の欄そのまま。
    events: tuple[tuple[str, str, str], ...]

    #: 質問と回答の本文 — （質問の本文, 回答の本文）。まだ答えが無ければ None。
    questions: tuple[tuple[str, str | None], ...]

    #: 見立ての本文 — （読んだ結果, そう読んだ理由）。理由の空な見立ては存在しない。
    assessments: tuple[tuple[str, str], ...]

    #: 成果の中身。まだ無ければ None。
    result: str | None

    #: 根拠の引用。
    evidence_quotes: tuple[str, ...]


class DetailReader(Protocol):
    def read(self, id: JobId) -> DetailMaterial:
        """鍵で1件ぶんの詳細。集約を再構成しない——画面に要る形で引く。"""
        ...
