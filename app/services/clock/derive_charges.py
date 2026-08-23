"""算定を導出する — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 算定を導出する | `derive_charges` | 署名済みの訪問と行為の記録から、その日の算定行と
月次請求の下書きを**まだ無ければ**診療録に作る。点数の計算・回数の数えは判断ではない
——**上限に触れた行は0点の旗**で置き、裁くのは人。**確定済みの月には触れない** |

plan_visits の同型——展開は帳簿づけ。何度回しても同じ（作成元が一意）。
"""

from __future__ import annotations

from app.ports.emr_charge_port import EmrChargePort


def derive_charges(charges: EmrChargePort) -> tuple[str, ...]:
    """まだ無い算定行を作り、作った行の名を返す。判断はどこにも無い。"""
    return charges.derive()
