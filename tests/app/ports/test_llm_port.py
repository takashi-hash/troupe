"""LLM の口の壊しかた。設計/仕事が回る筋道.md §4。"""

from __future__ import annotations

from typing import get_type_hints

from app.ports.llm_port import LlmPort
from domain.values.job.reply import Reply


def test_返るのは印つきの応答と使った量() -> None:
    """生の応答は返れない——`Reply` に整えてからしか通れない（I16 の入り口）。"""
    hints = get_type_hints(LlmPort.consult)
    assert hints["return"] == tuple[Reply, int, int]
