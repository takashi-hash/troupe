"""患者を集める — 診療録（よそのコンテキスト）の患者の一覧を写す。

設計: 設計/仕事が回る筋道.md §1「画面が始めるもの」・人に見えるもの.md §1・§2。
| 患者を集める | `gather_patients` | 診療録（**よそのコンテキスト**）の患者の一覧を写す |
読むだけ。**中の語に翻訳しない** |

**翻訳が無いのは手抜きではなく境界。** 他の gather は帳簿の識別子を用語集の語へ写すが、
診療録の語は一座の用語集に無い——無い橋を渡らない。写しをそのまま運ぶ。
"""

from __future__ import annotations

from app.dto.patient_row import PatientRow
from app.ports.patient_reader import PatientReader


def gather_patients(patients: PatientReader) -> tuple[PatientRow, ...]:
    """患者の行の一覧。読むだけ——帳簿に書かない。"""
    return patients.read_all()
