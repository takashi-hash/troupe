"""頼む — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・§3。
| 頼む | `request` | 依頼を読んで仕事を作る |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
ここは読む仕事がまだ無い——代わりに `IdPort` で識別子を振る（`JobId` は**立てた者が振る**。
採番はファクトリの外）。依頼と写すものの束は人が書いた値のまま domain へ運ぶ。
業務の判断はしない。義務が拒んだら**断りに変えるだけ**。
"""

from __future__ import annotations

from app.dto.version_form import VersionForm
from app.ports.clock_port import ClockPort
from app.ports.id_port import IdPort
from app.services.refusal import Refusal, reason_of
from domain.aggregates.job import request as 依頼発
from domain.repositories.job_repository import JobRepository
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.request import Request
from app.services.human.add_version import copied_from, form_from_fields
from domain.value_objects.people.human import Human


def request_from_fields(
    jobs: JobRepository,
    ids: IdPort,
    clock: ClockPort,
    by: str,
    body: str,
    fields: dict[str, str],
) -> Refusal | None:
    """欄の文字から組んで頼む。数に読めない欄は断りに変える——エラーは投げない。

    人が必ず書くのは 頼む中身・源・必ず含む語だけ（設計 筋道 §1）。残りは既定——
    **やること=頼む中身・受け持ち=頼んだ人**・周期=週・日数=3・使用上限=20回600秒・
    やり直し=2。既定は設計が決めた値で、黙った発明ではない。
    組み立ては版を積むと同じ（`form_from_fields`——正本は1つ）。
    """
    既定 = {"cycle": "週", "days": "3", "budget_calls": "20", "budget_seconds": "600", "max_retries": "2"}
    欄 = {**既定, **fields}
    if "instruction" not in 欄 and body.strip():
        欄["instruction"] = body
    if "owner" not in 欄:
        欄["owner"] = by
    try:
        form = form_from_fields(欄)
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    return request(jobs, ids, clock, by, body, form)


def request(
    jobs: JobRepository, ids: IdPort, clock: ClockPort, by: str, body: str, form: VersionForm
) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——一生に傷をつけない。

    **画面から渡るのは文字だけ**（設計 §1）——ui は domain を知らないので、
    値に組むのはここ。依頼発は題材の初期値が無い——欄はぜんぶ人が書く。
    成功しても識別子は**返さない**——行方は履歴・検索から導出する（**判断が要るときだけ今日に出る**）。
    """
    try:
        req = Request(by=Human(name=by), at=clock.now(), body=body)
        copied = copied_from(form, base=None)
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    id = JobId(text=ids.new_id())
    request_id = ids.new_id()
    try:
        job, requested, created = 依頼発.request(id, request_id, req, copied, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    jobs.save(job, (requested, created))
    return None
