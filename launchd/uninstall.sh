#!/bin/sh
# 常駐を撤去する。**帳簿（data/）は消さない**——起きたことは消さない、が帳簿の定義。
# 消したいなら、それは人が自分の手で打つ:  rm -rf data/
launchctl unload ~/Library/LaunchAgents/org.ichiza.tick.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/org.ichiza.agent.plist 2>/dev/null || true
rm -f ~/Library/LaunchAgents/org.ichiza.tick.plist ~/Library/LaunchAgents/org.ichiza.agent.plist
echo "撤去した（帳簿 data/ は残してある）"
echo "ollama も止めるなら: brew services stop ollama"
