"""検査 — 成果が受け入れ基準を満たすか。

設計: 設計/仕事が回る筋道.md §2「仕様」・仕事とは何か.md §2「検査 `Check`」。
| 成果が受け入れ基準を満たすか | 成果の中身 ＋ 受け入れ基準の**必ず含む語** | 通る／止まる＋理由。**文字の照合だけ**——だから何度でも同じ結果になる |

**止める力を持つ**ので、同じ成果なら何度でも同じ結果でなければならない。
だから文字の照合だけ——時間依存は写すとき（`{対象期間}` を開く）に済んでいる。
"""

from __future__ import annotations

from domain.values.rule.criteria import AcceptanceCriteria


def stop_reason(body: str, criteria: AcceptanceCriteria) -> str | None:
    """通るなら None、止まるなら理由。"""
    if not criteria.opened:
        raise ValueError("開かれていない差し込みが検査に届きました（写すときに開く）")
    missing = [term for term in criteria.required_terms if term not in body]
    if missing:
        return "必ず含む語がありません: " + "、".join(missing)
    return None
