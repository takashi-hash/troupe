"""証拠 — 引用・指紋・完了の根拠。「なぜそうしたか」を後から説明する材料。

置かれたら不変（後から変わるなら証拠ではない）。
**引用は源から読んだ中身そのもの**——読み口を持たないタスクは自己申告に落ちる。
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from pydantic import BaseModel, ConfigDict

_frozen = ConfigDict(frozen=True, extra="forbid")


class Reading(BaseModel):
    """読んだもの — 源から読んだ1件。どの源から・いつ・何を"""

    model_config = _frozen
    source_ref: str
    quote: str
    at: datetime


class Evidence(BaseModel):
    """証拠 — 読んだものの引用と指紋。タスクを閉じる根拠"""

    model_config = _frozen
    evidence_ref: str
    job_id: str
    readings: tuple[Reading, ...]
    fingerprint: str
    at: datetime


def fingerprint(text: str) -> str:
    """指紋を取る — 中身から縮めた印を導く。同じ中身なら必ず同じになる"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def evidence_for(job_id: str, artifact_ref: str, readings: tuple[Reading, ...], at: datetime) -> Evidence:
    """証拠を作る — 読んだものから証拠を組み立てる。参照の形式はドメインが持つ"""
    joined = "\n".join(f"{r.source_ref}\n{r.quote}" for r in readings)
    return Evidence(
        evidence_ref=f"証拠/{artifact_ref}",
        job_id=job_id,
        readings=readings,
        fingerprint=fingerprint(joined),
        at=at,
    )


def needs_evidence(source_refs: tuple[str, ...]) -> bool:
    """証拠が要るか — 読み口を持つタスクは証拠で閉じる。持たないタスクは自己申告"""
    return len(source_refs) > 0
