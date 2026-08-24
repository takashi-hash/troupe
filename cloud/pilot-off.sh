#!/bin/sh
# 合成の座長から席を返してもらう——撮影の前・審査の後に流す。
#   1) 代役の心拍を止める
#   2) 全ルールに 受け持ち=Director の版を積んで有効化
#   3) 窓を Director の席へ戻し、開示バナーを消す
set -e
PROJECT="${PROJECT:-ichiza-agentic}"
REGION="${REGION:-asia-northeast1}"
INSTANCE="${INSTANCE:-troupe-ledger}"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

say "代役の心拍を止める"
gcloud scheduler jobs pause troupe-pilot-beat --location="$REGION" --project="$PROJECT" --quiet >/dev/null 2>&1 \
  && echo "  止めた" || echo "  もともと無い"

if [ ! -f /tmp/troupe-dbpw ]; then
  echo "帳簿の合言葉が見つかりません（/tmp/troupe-dbpw）——席の返しだけ続けます" >&2
else
  say "受け持ち＝Director の版を積んで有効化"
  SDK_BIN="$(gcloud info --format='value(installation.sdk_root)')/bin"
  "$SDK_BIN/cloud-sql-proxy" "$PROJECT:$REGION:$INSTANCE" --port 9471 >/dev/null 2>&1 &
  PROXY=$!
  trap 'kill $PROXY 2>/dev/null' EXIT
  sleep 3
  PW=$(cat /tmp/troupe-dbpw)
  export ICHIZA_LEDGER_DSN="postgresql://postgres:${PW}@127.0.0.1:9471/troupe"
  export ICHIZA_EMR_DSN="postgresql://postgres:${PW}@127.0.0.1:9471/emr"
  for name in "Care Plan Review" "Physician Order Expiry Check" "Survey Readiness Check" \
              "Visit Note Draft" "Weekly Visit Prep"; do
    out=$(uv run python main.py rule-add --name "$name" --by Director --owner Director)
    ver=$(printf '%s' "$out" | sed -n 's/.*version \([0-9][0-9]*\).*/\1/p')
    if [ -z "$ver" ]; then echo "  $name: $out" >&2; exit 1; fi
    uv run python main.py rule-activate --name "$name" --version "$ver" --by Director >/dev/null
    echo "  $name → v$ver (owner Director)"
  done
fi

say "代役を登記簿から外す（署名済みの記録は残る——歴史は消さない）"
if [ -f /tmp/troupe-dbpw ]; then
  export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
  PGPASSWORD=$(cat /tmp/troupe-dbpw) psql -q -h 127.0.0.1 -p 9471 -U postgres -d emr <<'SQL'
UPDATE clinicians SET active = false WHERE code = 'Sim-Director';
DELETE FROM staff WHERE name = 'Sim-Director';
SQL
  echo "  外した"
fi

say "バナーを消す"
gcloud run services update troupe-window --region="$REGION" --project="$PROJECT" \
  --remove-env-vars="ICHIZA_PILOT_NOTICE" --quiet >/dev/null
echo "  消した"
