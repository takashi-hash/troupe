# 一座をクラウドへ載せる器。**1枚で3つの役をこなす**——
# 時計のひと回り・AI のひと回り・窓。どれを回すかは引数が決める（launchd の plist と同じ）。
#
# 机の道具（PySide6）は入れない。載せるのは web の器とクラウドの帳簿だけ。
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

# 依存を先に置く——題材やコードを触ってもここは焼き直さない
COPY pyproject.toml ./
RUN uv sync --no-dev --extra web --extra cloud

COPY . .
ENV PATH="/app/.venv/bin:$PATH"

# 引数で役が決まる:
#   tick                     時計のひと回り
#   agent --name 一号        AI のひと回り
#   serve --viewer 管理者    窓（web）
ENTRYPOINT ["python", "main.py"]
CMD ["serve", "--viewer", "管理者"]
