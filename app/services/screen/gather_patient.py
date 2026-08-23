"""患者の詳細を集める — 1人のカルテ抽出を写す。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの.md §1・§2。
| 患者の詳細を集める | `gather_patient` | 1人のカルテ抽出（処方・指示書・予定・出来事・記録）を写す | 同上 |

**押せることは無い。** 承認や差し戻しは仕事の画面の話——ここは判断の材料を見るだけ。
"""

from __future__ import annotations

from app.dto.patient_view import PatientView
from app.ports.patient_reader import PatientReader


def gather_patient(patients: PatientReader, code: str) -> PatientView | None:
    """1人のカルテ抽出。居なければ None。読むだけ——帳簿に書かない。"""
    return patients.read_one(code)
