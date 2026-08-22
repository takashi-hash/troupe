"""操作の語（`ACTION_WORDS`）と書く欄（`TEXT_FIELDS`）— 識別子と用語集の語の橋。**正本は1つ**。

設計: 設計/人に見えるもの.md §3・どう作るか §5。
画面に出るのは用語集の語そのまま——画面ごとに言い換えを持つと、
同じ操作が画面で違う名になる。だから橋はこの1枚だけ。
"""

from __future__ import annotations

#: 操作の識別子 → 用語集の語。画面で言い換えない。
ACTION_WORDS = {
    "answer": "答える",
    "approve": "承認する",
    "send_back": "差し戻す",
    "abandon": "打ち切る",
    "request": "頼む",
    "add_version": "版を積む",
    "activate": "有効にする",
    "deactivate": "止める",
}

#: 書く欄が要る操作と、その欄の名。
TEXT_FIELDS = {"answer": "答え", "send_back": "差し戻す理由", "abandon": "打ち切る理由"}

#: 状態の語 → 用語集の識別子。**正本は domain の `STATE_WORDS`**——ここは写し。
#: 画面は domain を知らないので写しが要る。**ずれたら突合が赤くする。**
STATE_GLOSS = {
    "作られた": "Created",
    "着手できる": "Ready",
    "実行中": "InProgress",
    "答え待ち": "AwaitingAnswer",
    "提出済み": "Submitted",
    "承認待ち": "AwaitingApproval",
    "承認済み": "Cleared",
    "失敗した": "Failed",
    "終わった（確かめ待ち）": "FinishedPendingRecheck",
    "終わった": "Finished",
    "打ち切られた": "Abandoned",
}


def 併記(語: str, 識別子: str | None) -> str:
    """用語集の語に、用語集の識別子を添える。

    設計/人に見えるもの §5——日本語を読まない人に見せるときは識別子を併記してよい。
    **訳を作らない。** 出すのは用語集に載っている識別子そのままで、
    橋が無ければ語だけを出す（無い訳をここで発明しない）。
    """
    return f"{語}（{識別子}）" if 識別子 else 語
