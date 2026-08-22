#!/bin/sh
# 止めた脈を再開する。
#   sh launchd/start.sh          両方
#   sh launchd/start.sh agent    AI の脈だけ
#   sh launchd/start.sh tick     時計の脈だけ
set -e
which=${1:-all}
if [ "$which" = "all" ] || [ "$which" = "tick" ]; then
  launchctl load ~/Library/LaunchAgents/org.ichiza.tick.plist 2>/dev/null && echo "再開した: 時計の脈" || echo "もう動いている: 時計の脈"
fi
if [ "$which" = "all" ] || [ "$which" = "agent" ]; then
  launchctl load ~/Library/LaunchAgents/org.ichiza.agent.plist 2>/dev/null && echo "再開した: AI の脈" || echo "もう動いている: AI の脈"
fi
