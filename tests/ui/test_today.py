"""今日の画面の煙テスト。offscreen——読む手・押す手は偽物。"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from app.dto.today_row import TodayRow
from ui.today import TodayScreen


def _黙って通す(what: str, id: str, text: str) -> str | None:
    return None


def _row(**over: object) -> TodayRow:
    base: dict[str, object] = dict(
        id="J-0001",
        rule="会話の稽古",
        born_version=1,
        period="2026-W34",
        request_head=None,
        instruction="依存の一覧を突き合わせる",
        source="file:pyproject.toml",
        state_name="答え待ち",
        due="2026-08-25 08:06",
        assignee_name="一号",
        recheck_at=None,
        result_body=None,
        evidence_quote=None,
        question_body="本番と手元、どちらの依存を棚卸ししますか",
        answer_body=None,
        assessments=(),
        retries_exhausted=False,
        spent_calls=1,
        spent_seconds=15,
        budget_calls=20,
        budget_seconds=600,
        owner_name="座長",
        actions=("answer",),
    )
    return TodayRow(**(base | over))  # type: ignore[arg-type]


def _texts(screen: TodayScreen) -> str:
    return "\n".join(label.text() for label in screen.findChildren(QLabel))


def test_質問が縮めずに出て_ボタンは用語集の語() -> None:
    _ = QApplication.instance() or QApplication([])
    screen = TodayScreen(fetch=lambda: (_row(),), act=_黙って通す, refresh_seconds=3600)
    assert "本番と手元、どちらの依存を棚卸ししますか" in _texts(screen)
    assert "答え待ち" in _texts(screen)
    labels = [b.text() for b in screen.findChildren(QPushButton)]
    assert "答える" in labels and "更新" in labels


def test_押すと文字で手に渡り_断りは画面に出る() -> None:
    _ = QApplication.instance() or QApplication([])
    押された: list[tuple[str, str, str]] = []

    def act(what: str, id: str, text: str) -> str | None:
        押された.append((what, id, text))
        return "いまは答えを待っていません（もう誰かが動かしました）"

    screen = TodayScreen(fetch=lambda: (_row(),), act=act, refresh_seconds=3600)
    screen._press("answer", "J-0001", "手元です")  # pyright: ignore[reportPrivateUsage]
    assert 押された == [("answer", "J-0001", "手元です")]
    assert "断り" in _texts(screen)


def test_空なら今日は空ですと言う() -> None:
    _ = QApplication.instance() or QApplication([])
    screen = TodayScreen(fetch=lambda: (), act=_黙って通す, refresh_seconds=3600)
    assert "今日は空です" in _texts(screen)
