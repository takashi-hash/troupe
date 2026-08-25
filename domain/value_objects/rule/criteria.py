"""受け入れ基準 — 何をもって成果とするか。

設計: 設計/仕事とは何か.md §2「決まり」・§3・§4「仕事が持つもの」。
| `AcceptanceCriteria` | **2つに分かれる**。①**必ず含む語**の列（空でない。**機械が見る**）
②説明の文（**人と AI が読む**）。①に `{対象期間}` と書ける——**写すときに `Period` で開く**ので、
検査に届く時点では固定の文字列 | ①が空で作れたら赤／開かれていない `{` が検査に届いたら赤 |

**なぜ2つに分かれるか。** 自由文だけでは機械が検査できないから。
「先月分の請求がすべて出ていること」は人にも AI にも読めるが、検査には読めない。
検査は**止める力を持つ**（§2）——止めるには、機械が見られる形が要る。
だから①を機械の目、②を人と AI の目として分ける。
**①だけでは何のための仕事か伝わらず、②だけでは止められない。両方要る。**

**①は tuple で持つ。** 値オブジェクトは同じ辞書の鍵になれること（§3 共通の義務）。
list では鍵になれない。

**穴が書けるのは①だけ。** 機械が見るのはそこだから。
版は「毎月やること」を1つ書けばよく、仕事は自分の `Period` で開いた固定の語を持つ
（§4「写すのであって、指すのではない」）。開かれていない `{` が残っていないかを
言えるのが `opened`——これが偽のまま検査に届けば、機械は幻の語を探すことになる。
"""

from __future__ import annotations

from typing import Final, Self

from pydantic import model_validator

from domain.value_objects.calendar.period import Period
from domain.obligations import Value

#: 版に書ける穴 — 写すときに `Period` で開く。
PERIOD_PLACEHOLDER: Final = "{対象期間}"

#: 患者ごとに展開する版だけが書ける穴 — 写すときに患者記号で開く（筋道 §1 `create`）。
PATIENT_PLACEHOLDER: Final = "{患者}"

#: 訪問ごとに展開する版だけが書ける穴 — 写すときに訪問日で開く（筋道 §1 `create`）。
VISIT_DATE_PLACEHOLDER: Final = "{訪問日}"


class AcceptanceCriteria(Value):
    """受け入れ基準 — **機械が見る語**と、**人と AI が読む文**の2つ。"""

    #: ①必ず含む語。**機械が見る。** 空でない。
    required_terms: tuple[str, ...]

    #: ②説明の文。**人と AI が読む。** 空でもよい。
    description: str = ""

    @property
    def opened(self) -> bool:
        """開かれていない `{` が残っていないか。**検査に届く時点では真。**

        見るのは①だけ——止める力を持つのは機械の目で、機械が見るのはそこだから。
        """
        return not any("{" in term for term in self.required_terms)

    def expand(
        self, period: Period, patient: str | None = None, visit_date: str | None = None
    ) -> AcceptanceCriteria:
        """`{対象期間}`（と、あれば `{患者}`・`{訪問日}`）を開く。**版から写すときに1度だけ通る。**"""

        def 開く(term: str) -> str:
            term = term.replace(PERIOD_PLACEHOLDER, period.text)
            if patient is not None:
                term = term.replace(PATIENT_PLACEHOLDER, patient)
            if visit_date is not None:
                term = term.replace(VISIT_DATE_PLACEHOLDER, visit_date)
            return term

        return AcceptanceCriteria(
            required_terms=tuple(開く(term) for term in self.required_terms),
            description=self.description,
        )

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if not self.required_terms:
            raise ValueError("必ず含む語が空です。機械が見るものが無ければ検査は止められません")
        return self
