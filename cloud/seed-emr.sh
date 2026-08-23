#!/bin/sh
# 診療録に種を入れる。**合成データのみ**——実在の患者は1人も居ない。
# gcloud sql connect が一時的にこの端末のIPを許し、psql で流す。
set -e
PROJECT="${PROJECT:-ichiza-agentic}"
INSTANCE="${INSTANCE:-troupe-ledger}"
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
if [ ! -f /tmp/troupe-dbpw ]; then
  echo "帳簿の合言葉が見つかりません（/tmp/troupe-dbpw）" >&2; exit 1
fi
PGPASSWORD=$(cat /tmp/troupe-dbpw) gcloud sql connect "$INSTANCE" \
  --user=postgres --database=emr --project="$PROJECT" --quiet < cloud/emr-seed.sql
echo "診療録に種を入れた（10患者・全部架空）"
