"""源 — 腐敗防止層。外のファイルの言葉を、業務の語へ翻訳する。

設計: 設計/どう作るか.md §4。
| **adapters** | **業務の規則** | 帳簿の実装・Port の実装・**腐敗防止層** |
源の中身は**材料・引用・読めなかった理由**へ翻訳されてから中へ入る。

在りかの形は `file:相対パス` だけ。**`cmd:` や `http:` は後で足す**——
いまは読めなかった理由に倒す。読める形が増えたら、ここに実装を足す。

**読めたら常に引用（`Quote`）で返す。** 口には「何のために読むか」を渡す欄が無く、
呼ぶ側は材料でも引用でも本文を材料に使え（`consult` の1回目）、
根拠に積めるのは引用だけ（`consult` の取り直しと `confirm`）。
材料で返すと根拠が永久に積まれない——だからこの実装に `Material` の出口は無い。

例外は漏らさない。読めない理由は外の言葉（例外）ではなく、
中の語（読めなかった理由）になってから返る——**読めなければ `fail` へ**の材料。
"""

from __future__ import annotations

from pathlib import Path

from app.ports.source_port import Quote, SourceOutcome, Unreadable
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.rule.source import Source

#: 読める在りかの形。この接頭辞に続く相対パスを根から読む。
FILE_PREFIX = "file:"


class FileSource:
    """源の実装 — 根からの相対パスでファイルを読む。出口は引用か、読めなかった理由。"""

    def __init__(self, root: Path = Path(".")) -> None:
        self._root = root

    def read(self, source: Source) -> SourceOutcome:
        """源から読む。読めたら引用、読めなければ理由。"""
        location = source.location
        if not location.startswith(FILE_PREFIX):
            return Unreadable(reason=f"読める在りかの形は file:相対パス だけです: {location}")
        path = self._root / location.removeprefix(FILE_PREFIX)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return Unreadable(reason=f"源のファイルが読めませんでした: {location}")
        except UnicodeDecodeError:
            return Unreadable(reason=f"源のファイルが文字として読めませんでした: {location}")
        if not text.strip():
            return Unreadable(reason=f"源のファイルが空でした: {location}")
        return Quote(evidence=Evidence(quote=text, source=source))
