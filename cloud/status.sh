#!/bin/sh
# 脈と帳簿と窓の状態・直近のログ。**launchd/status.sh の対。**
set -e
PROJECT="${PROJECT:-ichiza-agentic}"
REGION="${REGION:-asia-northeast1}"

printf '\n\033[1m== 帳簿 ==\033[0m\n'
gcloud sql instances describe troupe-ledger --project="$PROJECT" \
  --format="value(state,databaseVersion,settings.tier)"

printf '\n\033[1m== 窓 ==\033[0m\n'
gcloud run services describe troupe-window --region="$REGION" --project="$PROJECT" \
  --format="value(status.url,status.conditions[0].status)"

printf '\n\033[1m== 脈（直近のひと回り）==\033[0m\n'
for role in tick agent; do
  printf '%-14s ' "troupe-$role"
  gcloud run jobs executions list --job="troupe-$role" --region="$REGION" \
    --project="$PROJECT" --limit=1 \
    --format="value(status.completionTime,status.succeededCount,status.failedCount)" 2>/dev/null \
    || echo "まだ回っていない"
done

printf '\n\033[1m== 直近のログ ==\033[0m\n'
gcloud logging read \
  'resource.type=("cloud_run_job" OR "cloud_run_revision") AND resource.labels.job_name:troupe OR resource.labels.service_name:troupe-window' \
  --project="$PROJECT" --limit=15 --freshness=30m \
  --format="value(timestamp,resource.labels.job_name,resource.labels.service_name,textPayload)"
