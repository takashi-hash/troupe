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
# run.invoker は**心拍が脈を起こすため**——これが無いと Scheduler は一度も試みない
for role in roles/aiplatform.user roles/cloudsql.client roles/run.invoker \
            roles/secretmanager.secretAccessor roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:${SA}" --role="$role" --condition=None \
    --quiet >/dev/null
  echo "  $role"
done

say "帳簿 — Cloud SQL の中に入れ物を1つ"
gcloud sql databases create "$DB" --instance="$INSTANCE" --project="$PROJECT" \
  2>/dev/null || echo "  既に在る"

say "診療録 — 同じ器に、別の入れ物（事業所の正本。一座は読むだけ）"
gcloud sql databases create emr --instance="$INSTANCE" --project="$PROJECT" \
  2>/dev/null || echo "  既に在る"
echo "  種は cloud/emr-seed.sql — 入れるのは: sh cloud/seed-emr.sh"

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
if ! gcloud secrets describe troupe-emr-dsn --project="$PROJECT" >/dev/null 2>&1; then
  if [ -f /tmp/troupe-dbpw ]; then
    PW=$(cat /tmp/troupe-dbpw)
    printf 'postgresql://postgres:%s@/emr?host=/cloudsql/%s' "$PW" "$CONNECTION" \
      | gcloud secrets create troupe-emr-dsn --project="$PROJECT" --data-file=- >/dev/null
    echo "  診療録の在りかも置いた"
  fi
else
  echo "  診療録の在りかは既に在る"
fi

say "器を焼く"
gcloud artifacts repositories create "$REPO" --repository-format=docker \
  --location="$REGION" --project="$PROJECT" 2>/dev/null || echo "  倉庫は既に在る"
gcloud builds submit --config cloud/cloudbuild.yaml \
  --substitutions=_IMAGE="$IMAGE" --project="$PROJECT" --quiet

say "脈 — 時計のひと回りと AI のひと回り（**常駐する仕組みは買う**）"
for role in tick agent; do
  if [ "$role" = "agent" ]; then ARGS="agent,--name,Nomi"; else ARGS="tick"; fi
  gcloud run jobs deploy "troupe-${role}" \
    --image="$IMAGE" --region="$REGION" --project="$PROJECT" \
    --service-account="$SA" \
    --set-cloudsql-instances="$CONNECTION" \
    --set-secrets="ICHIZA_LEDGER_DSN=troupe-ledger-dsn:latest,ICHIZA_EMR_DSN=troupe-emr-dsn:latest" \
    --set-env-vars="$MODEL_ENV" \
    --args="$ARGS" \
    --max-retries=0 --task-timeout=300s --quiet >/dev/null
  echo "  troupe-${role}"
done

say "窓 — web の器"
gcloud run deploy troupe-window \
  --image="$IMAGE" --region="$REGION" --project="$PROJECT" \
  --service-account="$SA" \
  --set-cloudsql-instances="$CONNECTION" \
  --set-secrets="ICHIZA_LEDGER_DSN=troupe-ledger-dsn:latest,ICHIZA_EMR_DSN=troupe-emr-dsn:latest,ICHIZA_MAPS_KEY=troupe-maps-key:latest" \
  --set-env-vars="$MODEL_ENV" \
  --args="serve,--viewer,Director" \
  --allow-unauthenticated \
  --min-instances=0 --max-instances=3 --quiet >/dev/null
window_url=$(gcloud run services describe troupe-window --region="$REGION" \
  --project="$PROJECT" --format="value(status.url)")
echo "  $window_url"

say "心拍 — 60秒ごとに脈を起こす（**時計の表に「AI を起こす」は増えない**）"
for role in tick agent; do
  URL="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT}/jobs/troupe-${role}:run"
  if gcloud scheduler jobs describe "troupe-${role}-beat" --location="$REGION" \
       --project="$PROJECT" >/dev/null 2>&1; then
    verb=update
  else
    verb=create
  fi
  gcloud scheduler jobs "$verb" http "troupe-${role}-beat" \
    --location="$REGION" --project="$PROJECT" \
    --schedule="* * * * *" --time-zone="Asia/Tokyo" \
    --uri="$URL" --http-method=POST \
    --oauth-service-account-email="$SA" --quiet >/dev/null
  echo "  troupe-${role}-beat（毎分）"
done

say "配線した"
echo "窓: $window_url"
echo "状態は: sh cloud/status.sh"
