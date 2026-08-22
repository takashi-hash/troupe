#!/bin/sh
# 撤去。**帳簿の中身は消さない**——インスタンスを消すのは人の手（launchd/uninstall.sh と同じ構え）。
set -e
PROJECT="${PROJECT:-ichiza-agentic}"
REGION="${REGION:-asia-northeast1}"
for role in tick agent; do
  gcloud scheduler jobs delete "troupe-${role}-beat" --location="$REGION" \
    --project="$PROJECT" --quiet 2>/dev/null || true
  gcloud run jobs delete "troupe-${role}" --region="$REGION" --project="$PROJECT" \
    --quiet 2>/dev/null || true
done
gcloud run services delete troupe-window --region="$REGION" --project="$PROJECT" \
  --quiet 2>/dev/null || true
echo "脈と窓を外した。**帳簿（Cloud SQL troupe-ledger）は残っている**"
echo "課金を止めるには: gcloud sql instances delete troupe-ledger --project=$PROJECT"
