"""語の橋 — 識別子と用語集の語。**正本は設計、橋はこの1枚**。

設計: 設計/人に見えるもの.md §3・§5・どう作るか §5。
画面に出るのは用語集の語そのまま——画面ごとに言い換えを持つと、
同じ操作が画面で違う名になる。だから橋はこの1枚だけ。

**器が2つ、欄が2つ。** 机の窓は語の欄を出し、web の窓は識別子の欄を出す
（人に見えるもの §5——日本語を読まない人には識別子を出してよい）。
**どちらも用語集に載っているもので、訳はここで作らない。**

写しは2つとも突合が守る——`GLOSS` は[用語集](../設計/仕事とは何か.md) §2 と、
`STATE_GLOSS` は domain の `STATE_WORDS` と、1行ずつ照合される。
"""

from __future__ import annotations

import re

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

#: 用語集の語 → 識別子。**正本は 設計/仕事とは何か §2**——突合が1行ずつ照合する。
GLOSS = {
    "人": "Human",
    "AI": "Agent",
    "帳簿": "Ledger",
    "仕事": "Job",
    "仕事の識別子": "JobId",
    "作成元": "Origin",
    "依頼": "Request",
    "期日": "DueDate",
    "確かめ期日": "RecheckDate",
    "担当": "Assignee",
    "起こす者": "Actor",
    "受け持ちの人": "Owner",
    "成果": "Result",
    "根拠": "Evidence",
    "承認": "Approval",
    "差し戻し": "SendBack",
    "質問": "Question",
    "回答": "Answer",
    "見立て": "Assessment",
    "使用上限": "Budget",
    "使った量": "Spent",
    "整えた応答": "Reply",
    "業務ルール": "Rule",
    "業務ルールの識別子": "RuleName",
    "版": "Version",
    "やること": "Instruction",
    "受け入れ基準": "AcceptanceCriteria",
    "周期": "Cycle",
    "対象期間": "Period",
    "源": "Source",
    "有効": "Active",
    "検査": "Check",
    "LLM に問う": "consult",
    "やり直しの上限": "MaxRetries",
}

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


def 読める(識別子: str) -> str:
    """識別子を、読める形に。**訳を作らない**——切れ目に空白を入れて頭を大きくするだけ。

    `send_back` → Send back、`AwaitingApproval` → Awaiting approval。
    出しているのは用語集の識別子そのままで、ここで別の語に置き換えてはいない。
    """
    割った = re.sub(r"(?<!^)(?=[A-Z])", " ", 識別子).replace("_", " ")
    return 割った[:1].upper() + 割った[1:].lower()


def 語(用語: str) -> str:
    """用語集の語を、識別子の側から読める形で。**橋に無い語は出せない。**

    無い語を渡したら落ちる——**訳をその場で発明させないため**。
    足したければ、まず[用語集](../設計/仕事とは何か.md)に行を足す。
    """
    return 読める(GLOSS[用語])


def 状態(語: str) -> str:
    """状態の語を、識別子の側から読める形で。橋に無ければ語をそのまま。"""
    識別子 = STATE_GLOSS.get(語)
    return 読める(識別子) if 識別子 else 語


def 操作(識別子: str) -> str:
    """操作の語を、識別子の側から読める形で。押せることは識別子で届く。"""
    return 読める(識別子)
