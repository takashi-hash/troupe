#!/bin/sh
# すべてのチェックを1本で回す。1つでも赤なら止まる。
set -e
uv run lint-imports
uv run pyright
uv run pytest -q
uv run python tests/glossary_lint.py
uv run python tests/ui_words_lint.py
uv run python tests/event_kinds_lint.py
uv run python tests/paths_lint.py
echo "チェック: すべて緑"
