#!/bin/sh
# 脈を止める（配線は残る——再開は start.sh）。帳簿・ollama はそのまま。
#   sh launchd/stop.sh          両方止める
#   sh launchd/stop.sh agent    AI の脈だけ止める（緊急停止——tick は回り続ける）
#   sh launchd/stop.sh tick     時計の脈だけ止める
set -e
which=${1:-all}
if [ "$which" = "all" ] || [ "$which" = "tick" ]; then
  launchctl unload ~/Library/LaunchAgents/org.ichiza.tick.plist 2>/dev/null && echo "止めた: 時計の脈" || echo "もう止まっている: 時計の脈"
fi
if [ "$which" = "all" ] || [ "$which" = "agent" ]; then
  launchctl unload ~/Library/LaunchAgents/org.ichiza.agent.plist 2>/dev/null && echo "止めた: AI の脈" || echo "もう止まっている: AI の脈"
fi
