#!/bin/sh
# 合成の座長に席を渡す——**動画を撮り終えてから流すこと**（席が Sim-Director に変わる）。
#
# 患者が合成なら座長も合成（設計/どう作るか §5）。3つやる:
#   1) 全ルールに 受け持ち=Sim-Director の版を積んで有効化
#      （これから生まれる仕事の承認が Sim-Director に渡る——I6 はそのまま）
#   2) 窓を Sim-Director の席で立て直し、開示バナーを点ける
#   3) 2時間ごとに代役を起こす心拍を作る
#
# 戻すのは pilot-off.sh。deploy.sh を流し直したら、これも流し直す（席とバナーが戻るため）。
set -e
PROJECT="${PROJECT:-ichiza-agentic}"
REGION="${REGION:-asia-northeast1}"
INSTANCE="${INSTANCE:-troupe-ledger}"
SA="troupe-runtime@${PROJECT}.iam.gserviceaccount.com"
NOTICE="Live demo: while judging is under way, human decisions here are simulated by a scripted pilot named Sim-Director. Every press is recorded under that name in Activity — see /how. Real judgment stays human: questions wait for a person."

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

if [ ! -f /tmp/troupe-dbpw ]; then
  echo "帳簿の合言葉が見つかりません（/tmp/troupe-dbpw）。" >&2
  echo "決め直すなら: gcloud sql users set-password postgres --instance=$INSTANCE --password=<新しい合言葉>" >&2
  echo "（決め直したら troupe-ledger-dsn / troupe-emr-dsn の秘密にも新しい版を積むこと）" >&2
  exit 1
fi

say "帳簿へ繋ぐ（cloud-sql-proxy を短く立てる）"
SDK_BIN="$(gcloud info --format='value(installation.sdk_root)')/bin"
"$SDK_BIN/cloud-sql-proxy" "$PROJECT:$REGION:$INSTANCE" --port 9471 >/dev/null 2>&1 &
PROXY=$!
trap 'kill $PROXY 2>/dev/null' EXIT
sleep 3
PW=$(cat /tmp/troupe-dbpw)
export ICHIZA_LEDGER_DSN="postgresql://postgres:${PW}@127.0.0.1:9471/troupe"
export ICHIZA_EMR_DSN="postgresql://postgres:${PW}@127.0.0.1:9471/emr"

say "受け持ち＝Sim-Director の版を積んで有効化"
for name in "Care Plan Review" "Physician Order Expiry Check" "Survey Readiness Check" \
            "Visit Note Draft — P-001" "Visit Note Draft — P-003" "Visit Note Draft — P-005" \
            "Weekly Visit Prep"; do
  out=$(uv run python main.py rule-add --name "$name" --by Director --owner Sim-Director)
  ver=$(printf '%s' "$out" | sed -n 's/.*version \([0-9][0-9]*\).*/\1/p')
  if [ -z "$ver" ]; then echo "  $name: $out" >&2; exit 1; fi
  uv run python main.py rule-activate --name "$name" --version "$ver" --by Director >/dev/null
  echo "  $name → v$ver (owner Sim-Director)"
done

say "代役を登記簿へ（座長の役＋医師の名簿——署名は 'signed by Sim-Director' と正直に残る）"
PGPASSWORD=$PW "$SDK_BIN/../bin/psql" -q -h 127.0.0.1 -p 9471 -U postgres -d emr 2>/dev/null || true
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
PGPASSWORD=$PW psql -q -h 127.0.0.1 -p 9471 -U postgres -d emr -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO staff(name, role) VALUES ('Sim-Director', 'director')
  ON CONFLICT (name) DO UPDATE SET role = 'director';
INSERT INTO clinicians(code, name, active)
  VALUES ('Sim-Director', 'Simulated director (demo)', true)
  ON CONFLICT (code) DO UPDATE SET active = true;
SQL
echo "  載せた"

say "開示バナーを点ける"
gcloud run services update troupe-window --region="$REGION" --project="$PROJECT" \
  --update-env-vars="ICHIZA_PILOT_NOTICE=${NOTICE}" --quiet >/dev/null
echo "  点けた"

say "代役の心拍（2時間ごと）"
URL="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT}/jobs/troupe-pilot:run"
if gcloud scheduler jobs describe troupe-pilot-beat --location="$REGION" --project="$PROJECT" >/dev/null 2>&1; then
  gcloud scheduler jobs update http troupe-pilot-beat --location="$REGION" --project="$PROJECT" \
    --schedule="7 */2 * * *" --time-zone="Asia/Tokyo" --uri="$URL" --http-method=POST \
    --oauth-service-account-email="$SA" --quiet >/dev/null
  gcloud scheduler jobs resume troupe-pilot-beat --location="$REGION" --project="$PROJECT" --quiet >/dev/null 2>&1 || true
else
  gcloud scheduler jobs create http troupe-pilot-beat --location="$REGION" --project="$PROJECT" \
    --schedule="7 */2 * * *" --time-zone="Asia/Tokyo" --uri="$URL" --http-method=POST \
    --oauth-service-account-email="$SA" --quiet >/dev/null
fi
echo "  troupe-pilot-beat（毎偶数時の7分）"

say "渡した — 戻すのは pilot-off.sh"
