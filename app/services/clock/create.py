"""作る — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」・§2・§3。
| 作る | `create` | 有効な版といまから、まだ無い仕事を作る | 作成元が一意（I3） |

**誰も呼ばなくても回る。何度回しても同じ結果**——作成元が一意（I3）だから、
既にある鍵のものは `reconcile` が二度出さない。
**`reconcile` が対象期間も決める**——業務の判断なので domain に置いてある。
版は `RuleRepository` から引き、`copy_for(period)` の束を写す——版そのものは渡さない。
識別子は `IdPort` が振る——**立てた者が振る**（採番はファクトリの外）。
"""

from __future__ import annotations

from app.ports.active_rule_reader import ActiveRuleReader
from app.ports.clock_port import ClockPort
from app.ports.id_port import IdPort
from app.ports.origin_reader import OriginReader
from domain.aggregates.job import create as 生成
from domain.repositories.job_repository import JobRepository
from domain.repositories.rule_repository import RuleRepository
from domain.services.reconcile import reconcile
from domain.value_objects.job.job_id import JobId


def create(
    jobs: JobRepository,
    rules: RuleRepository,
    active_rules: ActiveRuleReader,
    origins: OriginReader,
    ids: IdPort,
    clock: ClockPort,
) -> tuple[JobId, ...]:
    """作るべきをぜんぶ作り、作った識別子を返す。二度目は空になる——何度回しても同じ。"""
    now = clock.now()
    created: list[JobId] = []
    for rule_name, version_number, period in reconcile(
        active_rules.read_all(), origins.keys(), now
    ):
        rule = rules.load(rule_name)
        if rule is None:
            continue  # 一覧と帳簿の食い違い——触らない
        version = next((v for v in rule.versions if v.number == version_number), None)
        if version is None:
            continue  # 同上
        id = JobId(text=ids.new_id())
        job, event = 生成.create(
            id, rule_name, version_number, period, version.copy_for(period), now
        )
        jobs.save(job, (event,))
        created.append(id)
    return tuple(created)
