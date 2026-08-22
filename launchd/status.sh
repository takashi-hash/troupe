#!/bin/sh
# いまの脈の状態と、直近のログ。
for label in org.ichiza.tick org.ichiza.agent; do
  if launchctl list "$label" >/dev/null 2>&1; then
    code=$(launchctl list "$label" | awk -F'= |;' '/LastExitStatus/ {print $2}')
    echo "$label: 動いている（直近の終了コード ${code:-まだ}）"
  else
    echo "$label: 止まっている"
  fi
done
if curl -s --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "ollama: 動いている"
else
  echo "ollama: 止まっている（brew services start ollama）"
fi
root="$(cd "$(dirname "$0")/.." && pwd)"
for log in tick agent; do
  last=$(tail -1 "$root/data/logs/$log.log" 2>/dev/null)
  [ -n "$last" ] && echo "$log の直近: $last"
done
