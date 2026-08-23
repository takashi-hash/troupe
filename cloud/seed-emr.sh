#!/bin/sh
# 診療録に種を入れる。**合成データのみ**——実在の患者は1人も居ない。
# cloud-sql-proxy を短く立て、psql で流し、閉じる。
set -e
PROJECT="${PROJECT:-ichiza-agentic}"
REGION="${REGION:-asia-northeast1}"
INSTANCE="${INSTANCE:-troupe-ledger}"
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
SDK_BIN="$(gcloud info --format='value(installation.sdk_root)')/bin"
if [ ! -f /tmp/troupe-dbpw ]; then
  echo "帳簿の合言葉が見つかりません（/tmp/troupe-dbpw）。" >&2
  echo "決め直すなら: gcloud sql users set-password postgres --instance=$INSTANCE --password=<新しい合言葉>" >&2
  exit 1
fi
"$SDK_BIN/cloud-sql-proxy" "$PROJECT:$REGION:$INSTANCE" --port 9470 >/dev/null 2>&1 &
PROXY=$!
trap 'kill $PROXY 2>/dev/null' EXIT
sleep 3
PGPASSWORD=$(cat /tmp/troupe-dbpw) psql -q -h 127.0.0.1 -p 9470 -U postgres -d emr \
  -v ON_ERROR_STOP=1 -f cloud/emr-seed.sql
echo "診療録に種を入れた（10患者・全部架空）"
