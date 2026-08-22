#!/bin/sh
# 常駐を配線する。どのマシンでも——パスはこの場で埋める。外すときは uninstall.sh。
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UV="$(command -v uv || true)"
if [ -z "$UV" ]; then
  echo "uv がありません。先に入れてください: https://docs.astral.sh/uv/" >&2
  exit 1
fi
mkdir -p "$ROOT/data/logs" ~/Library/LaunchAgents
for name in tick agent; do
  sed -e "s|__ROOT__|$ROOT|g" -e "s|__UV__|$UV|g" \
    "$ROOT/launchd/org.ichiza.$name.plist" > ~/Library/LaunchAgents/org.ichiza.$name.plist
  launchctl unload ~/Library/LaunchAgents/org.ichiza.$name.plist 2>/dev/null || true
  launchctl load ~/Library/LaunchAgents/org.ichiza.$name.plist
done
echo "配線した: 時計の脈・AI の脈（心拍60秒＋帳簿が変わった瞬間に即応）"

# LLM の道具——起こすだけ。モデルは人に入れてもらう（13GB は黙って引かない）
if command -v ollama >/dev/null 2>&1; then
  brew services start ollama >/dev/null 2>&1 || true
  if ollama list 2>/dev/null | grep -q "gpt-oss:20b"; then
    echo "ollama: 動いている（gpt-oss:20b あり）"
  else
    echo "⚠ モデルがありません。入れてください（13GB）: ollama pull gpt-oss:20b"
    echo "  それまで AI の脈は LLM に届かず、源の失敗以外は進みません"
  fi
else
  echo "⚠ Ollama がありません。入れてください: brew install ollama"
fi
echo "状態は: sh launchd/status.sh"
