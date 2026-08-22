#!/bin/sh
# 常駐を配線する。外すときは uninstall.sh。
set -e
cp "$(dirname "$0")"/org.ichiza.*.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/org.ichiza.tick.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/org.ichiza.agent.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/org.ichiza.tick.plist
launchctl load ~/Library/LaunchAgents/org.ichiza.agent.plist
brew services start ollama
echo "配線した。launchctl list | grep ichiza で確認"
