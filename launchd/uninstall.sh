#!/bin/sh
launchctl unload ~/Library/LaunchAgents/org.ichiza.tick.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/org.ichiza.agent.plist 2>/dev/null || true
rm -f ~/Library/LaunchAgents/org.ichiza.tick.plist ~/Library/LaunchAgents/org.ichiza.agent.plist
echo "外した（ollama は brew services stop ollama で別途）"
