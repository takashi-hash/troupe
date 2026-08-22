#!/bin/sh
# クラウドの配線。**launchd/install.sh の対**——買った仕組みの設定であって、コードではない。
#
#   Cloud Scheduler (60秒) ─→ Cloud Run Job  troupe-tick    時計のひと回り
#   Cloud Scheduler (60秒) ─→ Cloud Run Job  troupe-agent   AI のひと回り
#                             Cloud Run Svc  troupe-window  窓（web）
#                                  └─→ Cloud SQL (Postgres)  帳簿
#
# 何度流しても同じ形になる（既に在るものは触らない）。外すのは teardown.sh。
set -e

PROJECT="${PROJECT:-ichiza-agentic}"
REGION="${REGION:-asia-northeast1}"
INSTANCE="${INSTANCE:-troupe-ledger}"
DB="${DB:-troupe}"
SA="troupe-runtime@${PROJECT}.iam.gserviceaccount.com"
REPO="troupe"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/troupe:latest"
CONNECTION="${PROJECT}:${REGION}:${INSTANCE}"
# 見立ても成果も Gemini が書く。**鍵は持たない**——実行の身元で通る。
MODEL_ENV="ICHIZA_LLM=gemini,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=global"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

say "身元 — 一座が名乗る先"
gcloud iam service-accounts create troupe-runtime --project="$PROJECT" \
  --display-name="Troupe runtime" 2>/dev/null || echo "  既に在る"
for role in roles/aiplatform.user roles/cloudsql.client \
            roles/secretmanager.secretAccessor roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:${SA}" --role="$role" --condition=None \
    --quiet >/dev/null
  echo "  $role"
done

say "帳簿 — Cloud SQL の中に入れ物を1つ"
gcloud sql databases create "$DB" --instance="$INSTANCE" --project="$PROJECT" \
  2>/dev/null || echo "  既に在る"

say "在りか — 帳簿への繋ぎを秘密に置く"
if ! gcloud secrets describe troupe-ledger-dsn --project="$PROJECT" >/dev/null 2>&1; then
  if [ ! -f /tmp/troupe-dbpw ]; then
    echo "  帳簿の合言葉が見つかりません（/tmp/troupe-dbpw）。" >&2
    echo "  gcloud sql users set-password postgres --instance=$INSTANCE で決め直してください" >&2
    exit 1
  fi
  PW=$(cat /tmp/troupe-dbpw)
  printf 'postgresql://postgres:%s@/%s?host=/cloudsql/%s' "$PW" "$DB" "$CONNECTION" \
    | gcloud secrets create troupe-ledger-dsn --project="$PROJECT" --data-file=- >/dev/null
  echo "  置いた"
else
  echo "  既に在る"
fi

say "器を焼く"
gcloud artifacts repositories create "$REPO" --repository-format=docker \
  --location="$REGION" --project="$PROJECT" 2>/dev/null || echo "  倉庫は既に在る"
gcloud builds submit --config cloud/cloudbuild.yaml \
  --substitutions=_IMAGE="$IMAGE" --project="$PROJECT" --quiet

say "脈 — 時計のひと回りと AI のひと回り（**常駐する仕組みは買う**）"
for 役 in tick agent; do
  if [ "$役" = "agent" ]; then ARGS="agent,--name,一号"; else ARGS="tick"; fi
  gcloud run jobs deploy "troupe-${役}" \
    --image="$IMAGE" --region="$REGION" --project="$PROJECT" \
    --service-account="$SA" \
    --set-cloudsql-instances="$CONNECTION" \
    --set-secrets="ICHIZA_LEDGER_DSN=troupe-ledger-dsn:latest" \
    --set-env-vars="$MODEL_ENV" \
    --args="$ARGS" \
    --max-retries=0 --task-timeout=300s --quiet >/dev/null
  echo "  troupe-${役}"
done

say "窓 — web の器"
gcloud run deploy troupe-window \
  --image="$IMAGE" --region="$REGION" --project="$PROJECT" \
  --service-account="$SA" \
  --set-cloudsql-instances="$CONNECTION" \
  --set-secrets="ICHIZA_LEDGER_DSN=troupe-ledger-dsn:latest" \
  --set-env-vars="$MODEL_ENV" \
  --args="serve,--viewer,管理者" \
  --allow-unauthenticated \
  --min-instances=0 --max-instances=3 --quiet >/dev/null
窓=$(gcloud run services describe troupe-window --region="$REGION" \
  --project="$PROJECT" --format="value(status.url)")
echo "  $窓"

say "心拍 — 60秒ごとに脈を起こす（**時計の表に「AI を起こす」は増えない**）"
for 役 in tick agent; do
  URL="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT}/jobs/troupe-${役}:run"
  if gcloud scheduler jobs describe "troupe-${役}-beat" --location="$REGION" \
       --project="$PROJECT" >/dev/null 2>&1; then
    動詞=update
  else
    動詞=create
  fi
  gcloud scheduler jobs "$動詞" http "troupe-${役}-beat" \
    --location="$REGION" --project="$PROJECT" \
    --schedule="* * * * *" --time-zone="Asia/Tokyo" \
    --uri="$URL" --http-method=POST \
    --oauth-service-account-email="$SA" --quiet >/dev/null
  echo "  troupe-${役}-beat（毎分）"
done

say "配線した"
echo "窓: $窓"
echo "状態は: sh cloud/status.sh"
